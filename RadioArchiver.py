#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RadioArchiver - 放送局向け録音・アーカイブ統合システム

Copyright (c) 2026 Masaya Miyazaki / Office Stray Cat
All rights reserved.

Licensed under the MIT License
See LICENSE file for more details.

NOTICE: This copyright notice must be retained in all copies or 
substantial portions of the software, including derivative works.

Author: Masaya Miyazaki
Organization: Office Stray Cat
Website: https://stcat.com/
Email: info@stcat.com
GitHub: https://github.com/stcatcom/RadioArchiver
Version: 0.1.0
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import configparser
from pathlib import Path
import logging
from datetime import datetime, timedelta
import wave
import webbrowser
import socket

# 録音関連
try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None
    np = None

# Flask関連
from flask import Flask, request, send_file, jsonify, render_template_string

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flaskアプリ
app = Flask(__name__)

# HTMLテンプレート
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RadioArchiver - 録音ファイル結合</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 20px auto;
            padding: 0 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }
        input[type="datetime-local"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 12px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #0056b3;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        #result {
            margin-top: 25px;
            padding: 15px;
            border-radius: 5px;
            display: none;
        }
        .success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .error {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .processing {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        .download-link {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 3px;
            transition: background-color 0.3s;
        }
        .download-link:hover {
            background-color: #0056b3;
            color: white;
        }
        .config-info {
            margin-top: 30px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            font-size: 14px;
            color: #666;
        }
        .footer {
            margin-top: 50px;
            padding: 20px 0;
            text-align: center;
            border-top: 1px solid #dee2e6;
            font-size: 12px;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 RadioArchiver - Web UI</h1>
        <p style="text-align: center; color: #666; margin-bottom: 30px;">
            録音ファイルを指定した時間範囲で結合します
        </p>
        
        <form id="mergeForm">
            <div class="form-group">
                <label for="startTime">📅 開始時刻:</label>
                <input type="datetime-local" id="startTime" required>
            </div>
            <div class="form-group">
                <label for="endTime">📅 終了時刻:</label>
                <input type="datetime-local" id="endTime" required>
            </div>
            <button type="submit" id="submitBtn">🔄 結合開始</button>
        </form>
        
        <div id="result"></div>
        
        <div class="config-info">
            <strong>設定情報:</strong><br>
            録音ディレクトリ: {{ recording_dir }}<br>
            保存先ディレクトリ: {{ output_dir }}
        </div>
        
        <div class="footer">
            1999-2025 (c) Office Stray Cat all rights reserved.
        </div>
    </div>

    <script>
        document.getElementById('mergeForm').onsubmit = async (e) => {
            e.preventDefault();
            
            const startTime = new Date(document.getElementById('startTime').value);
            const endTime = new Date(document.getElementById('endTime').value);
            const submitBtn = document.getElementById('submitBtn');
            
            if (startTime >= endTime) {
                showResult('error', 'エラー: 開始時刻は終了時刻より前にしてください。');
                return;
            }
            
            const formatDate = (date) => {
                return date.getFullYear() +
                    String(date.getMonth() + 1).padStart(2, '0') +
                    String(date.getDate()).padStart(2, '0') + '-' +
                    String(date.getHours()).padStart(2, '0') +
                    String(date.getMinutes()).padStart(2, '0') +
                    String(date.getSeconds()).padStart(2, '0');
            };

            showResult('processing', '⏳ 処理中... しばらくお待ちください');
            submitBtn.disabled = true;
            submitBtn.textContent = '処理中...';

            try {
                const response = await fetch(`/merge?start_time=${formatDate(startTime)}&end_time=${formatDate(endTime)}`);
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const filename = `merged_${formatDate(startTime)}_${formatDate(endTime)}.wav`;
                    
                    showResult('success', `
                        <p>✅ ファイルの結合が完了しました！</p>
                        <a href="${url}" download="${filename}" class="download-link">
                            💾 結合したファイルをダウンロード (${filename})
                        </a>
                    `);
                } else {
                    const error = await response.json();
                    showResult('error', `❌ エラー: ${error.error}`);
                }
            } catch (error) {
                showResult('error', `❌ エラー: ${error.message}`);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '🔄 結合開始';
            }
        };
        
        function showResult(type, message) {
            const resultDiv = document.getElementById('result');
            resultDiv.className = type;
            resultDiv.innerHTML = message;
            resultDiv.style.display = 'block';
        }
    </script>
</body>
</html>
'''

# グローバル変数（Flaskから参照）
gui_instance = None

# Flaskルート
@app.route('/')
def index():
    """メインページ"""
    if gui_instance:
        recording_dir = gui_instance.config.get('DEFAULT', 'recording_dir')
        output_dir = gui_instance.config.get('DEFAULT', 'output_dir')
    else:
        recording_dir = "設定を読み込み中..."
        output_dir = "設定を読み込み中..."
    
    return render_template_string(HTML_TEMPLATE, 
                                recording_dir=recording_dir, 
                                output_dir=output_dir)

@app.route('/merge')
def merge_files():
    """WAVファイル結合API"""
    if not gui_instance:
        return jsonify({'error': 'アプリケーションが初期化されていません'}), 500
    
    try:
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        
        if not start_time_str or not end_time_str:
            return jsonify({'error': 'start_time と end_time パラメータが必要です'}), 400
        
        # 時刻のパース
        try:
            start_time = datetime.strptime(start_time_str, '%Y%m%d-%H%M%S')
            end_time = datetime.strptime(end_time_str, '%Y%m%d-%H%M%S')
        except ValueError as e:
            return jsonify({'error': f'時刻フォーマットエラー: {str(e)}'}), 400
        
        if start_time >= end_time:
            return jsonify({'error': '開始時刻は終了時刻より前にしてください'}), 400
        
        recording_dir = gui_instance.config.get('DEFAULT', 'recording_dir')
        output_dir = gui_instance.config.get('DEFAULT', 'output_dir')
        
        # 保存先ディレクトリの確認・作成
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return jsonify({'error': f'保存先ディレクトリの作成に失敗しました: {str(e)}'}), 400
        
        # 対象ファイルの取得
        wav_files = gui_instance.get_wav_files_in_timerange(start_time, end_time, recording_dir)
        if not wav_files:
            return jsonify({'error': '指定された時間範囲内にWAVファイルが見つかりませんでした'}), 404
        
        logger.info(f"結合対象ファイル数: {len(wav_files)}")
        
        # 出力ファイル名の生成
        output_filename = f"merged_{start_time_str}_{end_time_str}.wav"
        output_path = os.path.join(output_dir, output_filename)
        
        # ファイルの結合
        gui_instance.merge_wav_files(wav_files, output_path)
        
        # ファイルの送信
        return send_file(output_path, 
                        as_attachment=True, 
                        download_name=output_filename,
                        mimetype='audio/wav')
        
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': f'予期しないエラーが発生しました: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    if gui_instance:
        recording_dir = gui_instance.config.get('DEFAULT', 'recording_dir')
        output_dir = gui_instance.config.get('DEFAULT', 'output_dir')
        return jsonify({
            'status': 'ok',
            'recording_dir': recording_dir,
            'recording_dir_exists': os.path.exists(recording_dir),
            'output_dir': output_dir,
            'output_dir_exists': os.path.exists(output_dir)
        })
    else:
        return jsonify({'status': 'initializing'}), 503

class RadioArchiverGUI:
    def __init__(self, root):
        global gui_instance
        gui_instance = self
        
        self.root = root
        self.root.title("RadioArchiver - 録音・アーカイブ統合システム")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # 録音状態
        self.recording = False
        self.recording_thread = None
        self.recording_stream = None
        self.rec_start_time = None
        
        # モニタリング状態
        self.monitoring = False
        self.monitor_stream = None
        
        # Webサーバー状態
        self.server_running = False
        self.server_thread = None
        
        # 設定の読み込み
        self.load_config()
        
        # UI構築
        self.create_widgets()
        
        # Webサーバーを自動起動
        self.root.after(500, self.auto_start_webserver)
        
        # 定期的に古いファイルを削除（10分ごと）
        self.root.after(60000, self.cleanup_old_files)  # 1分後に初回実行
        
        # ウィンドウクローズ時の処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_config(self):
        """設定ファイルの読み込み"""
        self.config = configparser.ConfigParser()
        
        # 実行ファイルのディレクトリを取得
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(__file__)
        
        self.config_path = os.path.join(app_dir, 'config.ini')
        
        # デフォルト設定
        self.default_config = {
            'recording_dir': 'C:/RadioArchiver/rec' if sys.platform == 'win32' else os.path.expanduser('~') + "/rec",
            'output_dir': 'C:/RadioArchiver/merged' if sys.platform == 'win32' else '/tmp/wav_merged',
            'audio_device': '',
            'sample_rate': '44100',
            'channels': '2',
            'bit_depth': '16',
            'recording_retention_days': '90',  # 同録ファイルの保持期間（日）
            'merged_retention_hours': '2'  # mergedファイルの保持時間（時間）
        }
        
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')
        
        # デフォルト値の設定
        for key, value in self.default_config.items():
            if not self.config.has_option('DEFAULT', key):
                self.config['DEFAULT'][key] = value
    
    def save_config(self):
        """設定ファイルの保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            messagebox.showinfo("成功", "設定を保存しました")
            logger.info(f"設定を保存しました: {self.config_path}")
        except Exception as e:
            messagebox.showerror("エラー", f"設定の保存に失敗しました:\n{e}")
            logger.error(f"設定保存エラー: {e}")
    
    def create_widgets(self):
        """UIの構築"""
        # ノートブック（タブ）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # タブ1: 録音
        self.recording_tab = ttk.Frame(notebook)
        notebook.add(self.recording_tab, text="📻 録音")
        self.create_recording_tab()
        
        # タブ2: アーカイブ（結合）
        self.archive_tab = ttk.Frame(notebook)
        notebook.add(self.archive_tab, text="📼 アーカイブ結合")
        self.create_archive_tab()
        
        # タブ3: Webサーバー
        self.webserver_tab = ttk.Frame(notebook)
        notebook.add(self.webserver_tab, text="🌐 Web UI")
        self.create_webserver_tab()
        
        # タブ4: 設定
        self.settings_tab = ttk.Frame(notebook)
        notebook.add(self.settings_tab, text="⚙️ 設定")
        self.create_settings_tab()
        
        # ステータスバー
        self.create_status_bar()
    
    def get_local_ip_addresses(self):
        """ローカルIPアドレスの一覧を取得"""
        ip_addresses = []
        
        try:
            # ホスト名を取得
            hostname = socket.gethostname()
            
            # すべてのIPアドレスを取得
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                # IPv4のみ、ループバック以外
                if ':' not in ip and not ip.startswith('127.'):
                    if ip not in ip_addresses:
                        ip_addresses.append(ip)
        except Exception as e:
            logger.warning(f"IPアドレス取得エラー: {e}")
        
        # 追加の方法でIPアドレスを取得（WindowsやLinuxで確実に取得）
        try:
            # ダミー接続でIPアドレスを取得
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            if local_ip not in ip_addresses and not local_ip.startswith('127.'):
                ip_addresses.append(local_ip)
        except Exception:
            pass
        
        return ip_addresses
    
    def get_audio_devices(self):
        """録音可能なオーディオデバイスの一覧を取得"""
        devices = []
        
        if not SOUNDDEVICE_AVAILABLE:
            return [("sounddeviceがインストールされていません", -1)]
        
        try:
            device_list = sd.query_devices()
            
            for idx, device in enumerate(device_list):
                # 入力チャンネルがあるデバイスのみ
                if device['max_input_channels'] > 0:
                    name = device['name']
                    channels = device['max_input_channels']
                    sample_rate = int(device['default_samplerate'])
                    
                    # デバイス情報を整形
                    device_info = f"[{idx}] {name} ({channels}ch, {sample_rate}Hz)"
                    devices.append((device_info, idx))
            
            if not devices:
                devices.append(("録音可能なデバイスが見つかりません", -1))
        
        except Exception as e:
            logger.error(f"デバイス一覧取得エラー: {e}")
            devices.append((f"エラー: {e}", -1))
        
        return devices
    
    def create_recording_tab(self):
        """録音タブの作成"""
        frame = ttk.LabelFrame(self.recording_tab, text="録音設定", padding=15)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 録音デバイス選択
        row = 0
        ttk.Label(frame, text="録音デバイス:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        device_frame = ttk.Frame(frame)
        device_frame.grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.device_var, width=60, state='readonly')
        self.device_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(device_frame, text="🔄 更新", command=self.refresh_devices, width=10).pack(side=tk.LEFT)
        
        # 初回デバイス一覧取得
        self.refresh_devices()
        
        # サンプルレート
        row += 1
        ttk.Label(frame, text="サンプルレート:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.sample_rate_var = tk.StringVar(value=self.config.get('DEFAULT', 'sample_rate', fallback='44100'))
        sample_rate_combo = ttk.Combobox(frame, textvariable=self.sample_rate_var, width=20, state='readonly')
        sample_rate_combo['values'] = ['44100', '48000', '96000']
        sample_rate_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text="Hz").grid(row=row, column=2, sticky=tk.W)
        
        # チャンネル数
        row += 1
        ttk.Label(frame, text="チャンネル数:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.channels_var = tk.StringVar(value=self.config.get('DEFAULT', 'channels', fallback='2'))
        channels_combo = ttk.Combobox(frame, textvariable=self.channels_var, width=20, state='readonly')
        channels_combo['values'] = ['1', '2']
        channels_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text="(1=モノラル, 2=ステレオ)").grid(row=row, column=2, sticky=tk.W, padx=5)
        
        # ビット深度
        row += 1
        ttk.Label(frame, text="ビット深度:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.bit_depth_var = tk.StringVar(value=self.config.get('DEFAULT', 'bit_depth', fallback='16'))
        bit_depth_combo = ttk.Combobox(frame, textvariable=self.bit_depth_var, width=20, state='readonly')
        bit_depth_combo['values'] = ['16', '24', '32']
        bit_depth_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text="bit").grid(row=row, column=2, sticky=tk.W)
        
        # レベルメーター
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)
        
        row += 1
        meter_frame = ttk.LabelFrame(frame, text="レベルメーター", padding=10)
        meter_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Lチャンネル
        l_frame = ttk.Frame(meter_frame)
        l_frame.pack(fill=tk.X, pady=5)
        ttk.Label(l_frame, text="L:", width=3).pack(side=tk.LEFT)
        
        self.meter_l_canvas = tk.Canvas(l_frame, height=20, bg='#2b2b2b', highlightthickness=0)
        self.meter_l_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.meter_l_label = ttk.Label(l_frame, text="-∞ dB", width=10, anchor=tk.E)
        self.meter_l_label.pack(side=tk.LEFT)
        
        # Rチャンネル
        r_frame = ttk.Frame(meter_frame)
        r_frame.pack(fill=tk.X, pady=5)
        ttk.Label(r_frame, text="R:", width=3).pack(side=tk.LEFT)
        
        self.meter_r_canvas = tk.Canvas(r_frame, height=20, bg='#2b2b2b', highlightthickness=0)
        self.meter_r_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.meter_r_label = ttk.Label(r_frame, text="-∞ dB", width=10, anchor=tk.E)
        self.meter_r_label.pack(side=tk.LEFT)
        
        # モニターコントロール
        row += 1
        monitor_frame = ttk.Frame(frame)
        monitor_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.monitor_button = ttk.Button(monitor_frame, text="🎧 モニター開始", 
                                        command=self.toggle_monitor, 
                                        width=20)
        self.monitor_button.pack(side=tk.LEFT, padx=5)
        
        # 録音コントロール
        row += 1
        control_frame = ttk.Frame(frame)
        control_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        self.rec_button = ttk.Button(control_frame, text="⏺ 録音開始", 
                                     command=self.start_recording, 
                                     width=20)
        self.rec_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="⏹ 停止", 
                                      command=self.stop_recording, 
                                      width=20, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 録音時間表示
        row += 1
        self.rec_time_label = ttk.Label(frame, text="録音時間: 00:00:00", font=("Arial", 14))
        self.rec_time_label.grid(row=row, column=0, columnspan=3, pady=10)
        
        # 現在のファイル名表示
        row += 1
        self.rec_file_label = ttk.Label(frame, text="", font=("Arial", 9), foreground="gray")
        self.rec_file_label.grid(row=row, column=0, columnspan=3, pady=5)
        
        # カラムの調整
        frame.columnconfigure(1, weight=1)
    
    def create_archive_tab(self):
        """アーカイブ結合タブの作成"""
        main_frame = ttk.Frame(self.archive_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 上部: 結合設定
        settings_frame = ttk.LabelFrame(main_frame, text="結合設定", padding=15)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 開始時刻
        row = 0
        ttk.Label(settings_frame, text="開始時刻:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        time_frame_start = ttk.Frame(settings_frame)
        time_frame_start.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        # 日付
        self.start_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(time_frame_start, textvariable=self.start_date_var, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_start, text="").pack(side=tk.LEFT, padx=2)
        
        # 時刻
        self.start_hour_var = tk.StringVar(value='00')
        self.start_min_var = tk.StringVar(value='00')
        self.start_sec_var = tk.StringVar(value='00')
        
        ttk.Entry(time_frame_start, textvariable=self.start_hour_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_start, text=":").pack(side=tk.LEFT)
        ttk.Entry(time_frame_start, textvariable=self.start_min_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_start, text=":").pack(side=tk.LEFT)
        ttk.Entry(time_frame_start, textvariable=self.start_sec_var, width=4).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(time_frame_start, text="現在時刻", command=self.set_start_now, width=10).pack(side=tk.LEFT, padx=10)
        
        # 終了時刻
        row += 1
        ttk.Label(settings_frame, text="終了時刻:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        time_frame_end = ttk.Frame(settings_frame)
        time_frame_end.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        # 日付
        self.end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(time_frame_end, textvariable=self.end_date_var, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_end, text="").pack(side=tk.LEFT, padx=2)
        
        # 時刻
        self.end_hour_var = tk.StringVar(value='01')
        self.end_min_var = tk.StringVar(value='00')
        self.end_sec_var = tk.StringVar(value='00')
        
        ttk.Entry(time_frame_end, textvariable=self.end_hour_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_end, text=":").pack(side=tk.LEFT)
        ttk.Entry(time_frame_end, textvariable=self.end_min_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_end, text=":").pack(side=tk.LEFT)
        ttk.Entry(time_frame_end, textvariable=self.end_sec_var, width=4).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(time_frame_end, text="現在時刻", command=self.set_end_now, width=10).pack(side=tk.LEFT, padx=10)
        
        # 保存先
        row += 1
        ttk.Label(settings_frame, text="保存先:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        output_frame = ttk.Frame(settings_frame)
        output_frame.grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        self.output_dir_var = tk.StringVar(value=self.config.get('DEFAULT', 'output_dir'))
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="参照...", command=self.browse_output_dir, width=10).pack(side=tk.LEFT)
        
        # 結合ボタン
        row += 1
        ttk.Separator(settings_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=15)
        
        row += 1
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        self.merge_button = ttk.Button(button_frame, text="🔄 結合開始", 
                                      command=self.start_merge, 
                                      width=25)
        self.merge_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📁 保存先を開く", 
                  command=self.open_output_dir, 
                  width=25).pack(side=tk.LEFT, padx=5)
        
        # カラムの調整
        settings_frame.columnconfigure(1, weight=1)
        
        # 下部: ログ表示
        log_frame = ttk.LabelFrame(main_frame, text="処理ログ", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.merge_log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80, state=tk.DISABLED)
        self.merge_log_text.pack(fill=tk.BOTH, expand=True)
        
        # ログクリアボタン
        ttk.Button(log_frame, text="ログをクリア", command=self.clear_merge_log, width=15).pack(anchor=tk.E, pady=5)
    
    def create_webserver_tab(self):
        """Webサーバータブの作成"""
        frame = ttk.LabelFrame(self.webserver_tab, text="Webサーバー設定", padding=15)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ポート設定
        row = 0
        ttk.Label(frame, text="ポート:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value='5000')
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text="(デフォルト: 5000)").grid(row=row, column=2, sticky=tk.W, padx=10)
        
        # サーバー制御
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)
        
        row += 1
        control_frame = ttk.Frame(frame)
        control_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.start_server_button = ttk.Button(control_frame, text="▶ サーバー起動", 
                                             command=self.start_webserver, 
                                             width=20)
        self.start_server_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_server_button = ttk.Button(control_frame, text="⏹ サーバー停止", 
                                            command=self.stop_webserver, 
                                            width=20, state=tk.DISABLED)
        self.stop_server_button.pack(side=tk.LEFT, padx=5)
        
        self.open_browser_button = ttk.Button(control_frame, text="🌐 ブラウザで開く", 
                                             command=self.open_webui, 
                                             width=20, state=tk.DISABLED)
        self.open_browser_button.pack(side=tk.LEFT, padx=5)
        
        # サーバー状態表示
        row += 1
        self.server_status_label = ttk.Label(frame, text="● サーバー停止中", 
                                            foreground="red", font=("Arial", 12, "bold"))
        self.server_status_label.grid(row=row, column=0, columnspan=3, pady=10)
        
        row += 1
        self.server_url_label = ttk.Label(frame, text="", font=("Arial", 10), justify=tk.LEFT)
        self.server_url_label.grid(row=row, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        # 説明
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)
        
        row += 1
        info_text = """Web UIを使用すると、スマホやタブレットからも結合操作ができます。
        
使い方:
1. 「▶ サーバー起動」をクリック
2. 「🌐 ブラウザで開く」をクリック、またはURL を直接開く
3. 開始時刻・終了時刻を入力して結合開始"""
        
        info_label = ttk.Label(frame, text=info_text, justify=tk.LEFT, foreground="gray")
        info_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        # ログ表示
        row += 1
        ttk.Label(frame, text="システムログ（録音・削除・サーバーなど）:").grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        row += 1
        self.server_log_text = scrolledtext.ScrolledText(frame, height=12, width=80, state=tk.DISABLED)
        self.server_log_text.grid(row=row, column=0, columnspan=3, sticky=tk.NSEW, pady=5)
        
        # カラムと行の調整
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(row, weight=1)
    
    def create_settings_tab(self):
        """設定タブの作成"""
        frame = ttk.LabelFrame(self.settings_tab, text="ディレクトリ設定", padding=15)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 録音ディレクトリ
        row = 0
        ttk.Label(frame, text="録音ディレクトリ:").grid(row=row, column=0, sticky=tk.W, pady=10)
        self.recording_dir_var = tk.StringVar(value=self.config.get('DEFAULT', 'recording_dir'))
        ttk.Entry(frame, textvariable=self.recording_dir_var, width=50).grid(row=row, column=1, sticky=tk.EW, pady=10)
        ttk.Button(frame, text="参照...", command=self.browse_recording_dir, width=10).grid(row=row, column=2, padx=5)
        
        row += 1
        rec_note = ttk.Label(frame, text="録音されたWAVファイルが保存されるディレクトリ（rec_YYYYMMDD-HHMMSS.wav形式）", 
                            font=("Arial", 8), foreground="gray")
        rec_note.grid(row=row, column=1, sticky=tk.W)
        
        # 結合ファイル保存先（デフォルト）
        row += 1
        ttk.Label(frame, text="結合ファイル保存先:").grid(row=row, column=0, sticky=tk.W, pady=10)
        default_output_var = tk.StringVar(value=self.config.get('DEFAULT', 'output_dir'))
        ttk.Entry(frame, textvariable=default_output_var, width=50).grid(row=row, column=1, sticky=tk.EW, pady=10)
        ttk.Button(frame, text="参照...", 
                  command=lambda: self.browse_directory(default_output_var, "結合ファイル保存先を選択"), 
                  width=10).grid(row=row, column=2, padx=5)
        
        row += 1
        temp_note = ttk.Label(frame, text="結合されたWAVファイルのデフォルト保存先", 
                             font=("Arial", 8), foreground="gray")
        temp_note.grid(row=row, column=1, sticky=tk.W)
        
        # ファイル保持期間設定
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)
        
        row += 1
        retention_label = ttk.Label(frame, text="ファイル保持期間設定", font=("Arial", 10, "bold"))
        retention_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        # 同録ファイル（録音ファイル）保持期間
        row += 1
        ttk.Label(frame, text="同録ファイル保持期間:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        retention_rec_frame = ttk.Frame(frame)
        retention_rec_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        self.recording_retention_var = tk.StringVar(value=self.config.get('DEFAULT', 'recording_retention_days', fallback='90'))
        ttk.Entry(retention_rec_frame, textvariable=self.recording_retention_var, width=10).pack(side=tk.LEFT)
        ttk.Label(retention_rec_frame, text="日").pack(side=tk.LEFT, padx=5)
        
        row += 1
        rec_retention_note = ttk.Label(frame, text="録音された1分ごとのファイル（rec_*.wav）の保持期間\n"
                                                   "※ 地上波放送局の場合、放送法により3ヶ月（90日）以上の保存が義務付けられています", 
                                      font=("Arial", 8), foreground="gray", justify=tk.LEFT)
        rec_retention_note.grid(row=row, column=1, sticky=tk.W)
        
        # 結合ファイル保持期間
        row += 1
        ttk.Label(frame, text="結合ファイル保持期間:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        retention_merged_frame = ttk.Frame(frame)
        retention_merged_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        self.merged_retention_var = tk.StringVar(value=self.config.get('DEFAULT', 'merged_retention_hours', fallback='2'))
        ttk.Entry(retention_merged_frame, textvariable=self.merged_retention_var, width=10).pack(side=tk.LEFT)
        ttk.Label(retention_merged_frame, text="時間").pack(side=tk.LEFT, padx=5)
        
        row += 1
        merged_retention_note = ttk.Label(frame, text="結合されたファイル（merged_*.wav）の保持期間", 
                                         font=("Arial", 8), foreground="gray")
        merged_retention_note.grid(row=row, column=1, sticky=tk.W)
        
        # ディレクトリ作成ボタン
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)
        
        row += 1
        ttk.Button(frame, text="📁 ディレクトリを作成", 
                  command=self.create_directories, 
                  width=25).grid(row=row, column=1, sticky=tk.W, pady=10)
        
        # 保存ボタン
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)
        
        row += 1
        save_frame = ttk.Frame(frame)
        save_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        ttk.Button(save_frame, text="💾 設定を保存", 
                  command=lambda: self.save_all_config(default_output_var), 
                  width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(save_frame, text="🔄 デフォルトに戻す", 
                  command=lambda: self.reset_to_default(default_output_var), 
                  width=20).pack(side=tk.LEFT, padx=5)
        
        # アプリ情報
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)
        
        row += 1
        info_frame = ttk.Frame(frame)
        info_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        info_text = """RadioArchiver - 録音・アーカイブ統合システム
Version 0.1.0

© 2026 Masaya Miyazaki / Office Stray Cat
Licensed under the MIT License

https://stcat.com/
https://github.com/stcatcom/RadioArchiver"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.CENTER, foreground="gray").pack()
        
        # カラムの調整
        frame.columnconfigure(1, weight=1)
    
    def create_status_bar(self):
        """ステータスバーの作成"""
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="準備完了", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
    
    # イベントハンドラ - 録音関連
    def refresh_devices(self):
        """オーディオデバイス一覧の更新"""
        devices = self.get_audio_devices()
        
        # デバイス名のリストを作成
        device_names = [name for name, idx in devices]
        self.device_combo['values'] = device_names
        
        # デバイスインデックスを保存（内部用）
        self.device_indices = {name: idx for name, idx in devices}
        
        # 設定ファイルから前回選択したデバイスを復元
        saved_device = self.config.get('DEFAULT', 'audio_device', fallback='')
        
        if saved_device and saved_device in device_names:
            self.device_var.set(saved_device)
        elif device_names:
            # 保存されたデバイスがない、または見つからない場合は最初のデバイスを選択
            self.device_var.set(device_names[0])
        
        if SOUNDDEVICE_AVAILABLE:
            self.log_merge(f"オーディオデバイス一覧を更新しました ({len(devices)} 件)")
        else:
            messagebox.showwarning("警告", 
                "sounddeviceがインストールされていません。\n\n"
                "録音機能を使用するには、以下のコマンドでインストールしてください:\n"
                "pip install sounddevice")
    
    def get_selected_device_index(self):
        """現在選択されているデバイスのインデックスを取得"""
        device_name = self.device_var.get()
        return self.device_indices.get(device_name, -1)
    
    
    def toggle_monitor(self):
        """モニタリングの開始/停止"""
        if not SOUNDDEVICE_AVAILABLE:
            messagebox.showerror("エラー", "sounddeviceがインストールされていません")
            return
        
        if self.monitoring:
            self.stop_monitor()
        else:
            self.start_monitor()
    
    def start_monitor(self):
        """モニタリング開始"""
        try:
            device_idx = self.get_selected_device_index()
            if device_idx < 0:
                messagebox.showerror("エラー", "有効な録音デバイスを選択してください")
                return
            
            sample_rate = int(self.sample_rate_var.get())
            channels = int(self.channels_var.get())
            
            # モニタリングコールバック
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"モニタリング状態: {status}")
                
                # 音量レベル計算
                if channels == 1:
                    # モノラル
                    rms = np.sqrt(np.mean(indata**2))
                    db = 20 * np.log10(rms) if rms > 0 else -100
                    self.update_meter(db, db)
                else:
                    # ステレオ
                    rms_l = np.sqrt(np.mean(indata[:, 0]**2))
                    rms_r = np.sqrt(np.mean(indata[:, 1]**2))
                    db_l = 20 * np.log10(rms_l) if rms_l > 0 else -100
                    db_r = 20 * np.log10(rms_r) if rms_r > 0 else -100
                    self.update_meter(db_l, db_r)
            
            # ストリーム開始
            self.monitor_stream = sd.InputStream(
                device=device_idx,
                channels=channels,
                samplerate=sample_rate,
                callback=audio_callback,
                blocksize=1024
            )
            self.monitor_stream.start()
            self.monitoring = True
            
            # UI更新
            self.monitor_button.config(text="⏹ モニター停止")
            self.rec_button.config(state=tk.NORMAL)
            self.status_label.config(text="モニタリング中...")
            
            logger.info(f"モニタリング開始: デバイス={device_idx}, {sample_rate}Hz, {channels}ch")
            
        except Exception as e:
            messagebox.showerror("エラー", f"モニタリング開始エラー:\n{e}")
            logger.error(f"モニタリングエラー: {e}")
    
    def stop_monitor(self):
        """モニタリング停止"""
        if self.monitor_stream:
            self.monitor_stream.stop()
            self.monitor_stream.close()
            self.monitor_stream = None
        
        self.monitoring = False
        
        # メーターをリセット
        self.meter_l_canvas.delete("all")
        self.meter_r_canvas.delete("all")
        self.meter_l_label.config(text="-∞ dB")
        self.meter_r_label.config(text="-∞ dB")
        
        # UI更新
        self.monitor_button.config(text="🎧 モニター開始")
        self.status_label.config(text="準備完了")
        
        logger.info("モニタリング停止")
    
    def update_meter(self, db_l, db_r):
        """レベルメーターの更新（位置ベース色分け版）"""
        def update():
            # dBを0-100のスケールに変換（-60dB ~ 0dB を 0-100 に）
            def db_to_percent(db):
                if db < -60:
                    return 0
                elif db > 0:
                    return 100
                else:
                    return (db + 60) / 60 * 100
            
            # Lチャンネルを描画
            self.draw_meter(self.meter_l_canvas, db_to_percent(db_l))
            self.meter_l_label.config(text=f"{db_l:.1f} dB" if db_l > -60 else "-∞ dB")
            
            # Rチャンネルを描画
            self.draw_meter(self.meter_r_canvas, db_to_percent(db_r))
            self.meter_r_label.config(text=f"{db_r:.1f} dB" if db_r > -60 else "-∞ dB")
        
        # メインスレッドで更新
        self.root.after(0, update)
    
    def draw_meter(self, canvas, percent):
        """Canvasにメーターを描画（位置ベースの色分け背景）"""
        canvas.delete("all")  # 前回の描画をクリア
        
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        if width <= 1:  # 初期化前の場合
            width = 500
        
        # 背景に色分けを描画（-60dB ~ 0dB を横幅にマッピング）
        # -60dB ~ -20dB: 緑 (0% ~ 66.7%)
        # -20dB ~ -6dB:  黄色 (66.7% ~ 90%)
        # -6dB ~ 0dB:    赤 (90% ~ 100%)
        
        green_end = int(width * 66.7 / 100)    # -20dBの位置
        yellow_end = int(width * 90 / 100)      # -6dBの位置
        
        # 緑の部分 (-60dB ~ -20dB)
        canvas.create_rectangle(0, 0, green_end, height, fill='#00ff00', outline="")
        
        # 黄色の部分 (-20dB ~ -6dB)
        canvas.create_rectangle(green_end, 0, yellow_end, height, fill='#ffff00', outline="")
        
        # 赤の部分 (-6dB ~ 0dB)
        canvas.create_rectangle(yellow_end, 0, width, height, fill='#ff0000', outline="")
        
        # 現在のレベルより右側を暗くする（オーバーレイ）
        bar_width = int(width * percent / 100)
        if bar_width < width:
            canvas.create_rectangle(bar_width, 0, width, height, fill='#2b2b2b', outline="")
    
    def start_recording(self):
        """録音開始"""
        if not SOUNDDEVICE_AVAILABLE:
            messagebox.showerror("エラー", 
                "sounddeviceがインストールされていません。\n\n"
                "以下のコマンドでインストールしてください:\n"
                "pip install sounddevice")
            return
        
        # モニタリング中なら停止
        if self.monitoring:
            self.stop_monitor()
        
        device_idx = self.get_selected_device_index()
        if device_idx == -1:
            messagebox.showerror("エラー", "有効な録音デバイスが選択されていません")
            return
        
        # 録音ディレクトリの確認
        recording_dir = self.config.get('DEFAULT', 'recording_dir')
        if not os.path.exists(recording_dir):
            try:
                Path(recording_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("エラー", f"録音ディレクトリの作成に失敗しました:\n{e}")
                return
        
        # 録音開始
        self.recording = True
        self.rec_start_time = datetime.now()
        
        # UI更新
        self.rec_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.monitor_button.config(state=tk.DISABLED)
        self.status_label.config(text="🔴 録音中...")
        
        # 録音スレッド開始
        self.recording_thread = threading.Thread(target=self.recording_worker, daemon=True)
        self.recording_thread.start()
        
        # 録音時間表示の更新
        self.update_recording_time()
        
        logger.info(f"録音開始: デバイス={device_idx}, ディレクトリ={recording_dir}")
    
    def recording_worker(self):
        """録音ワーカースレッド（タイムスタンプベース + ダブルバッファ）"""
        try:
            device_idx = self.get_selected_device_index()
            sample_rate = int(self.sample_rate_var.get())
            channels = int(self.channels_var.get())
            bit_depth = int(self.bit_depth_var.get())
            recording_dir = self.config.get('DEFAULT', 'recording_dir')
            
            # サンプル幅の計算
            if bit_depth == 16:
                dtype = 'int16'
                sampwidth = 2
            elif bit_depth == 24:
                dtype = 'int32'  # 24bitはint32として扱う
                sampwidth = 3
            else:  # 32bit
                dtype = 'int32'
                sampwidth = 4
            
            # ダブルバッファ
            buffer_a = []  # 書き込み中のバッファ
            buffer_b = []  # コールバックが使うバッファ
            current_buffer = buffer_b
            buffer_lock = threading.Lock()
            
            # 現在のファイル情報
            current_file = None
            current_wav = None
            current_file_start_sample = 0  # 現在のファイルの開始サンプル位置
            total_samples = 0  # 録音開始からの総サンプル数
            
            # 録音開始時刻を記録
            recording_start_time = datetime.now()
            
            # 次のファイル境界（毎時00秒）を計算
            next_boundary = recording_start_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
            next_boundary_sample = int((next_boundary - recording_start_time).total_seconds() * sample_rate)
            
            # 音声コールバック
            def audio_callback(indata, frames, time_info, status):
                nonlocal current_buffer, total_samples
                
                if status:
                    logger.warning(f"録音状態: {status}")
                
                with buffer_lock:
                    current_buffer.append((indata.copy(), total_samples))
                    total_samples += frames
            
            # ストリーム開始
            stream = sd.InputStream(
                device=device_idx,
                channels=channels,
                samplerate=sample_rate,
                dtype=dtype,
                callback=audio_callback,
                blocksize=1024
            )
            
            stream.start()
            self.recording_stream = stream
            
            logger.info(f"録音開始: 次の境界={next_boundary.strftime('%H:%M:%S')}, サンプル位置={next_boundary_sample}")
            
            while self.recording:
                # バッファを入れ替え（ダブルバッファリング）
                with buffer_lock:
                    if current_buffer is buffer_b:
                        buffer_a, buffer_b = buffer_b, buffer_a
                        current_buffer = buffer_b
                    else:
                        buffer_b, buffer_a = buffer_a, buffer_b
                        current_buffer = buffer_a
                
                # buffer_a を処理（コールバックは buffer_b に書き込み中）
                if buffer_a:
                    for audio_data, sample_position in buffer_a:
                        # ファイルの切り替えが必要か判定
                        if current_wav is None or sample_position >= next_boundary_sample:
                            # 現在のファイルがある場合は閉じる
                            if current_wav:
                                current_wav.close()
                                logger.info(f"ファイルクローズ: {current_file}")
                            
                            # 新しいファイルを開く
                            filename = f"rec_{next_boundary.strftime('%Y%m%d-%H%M%S')}.wav"
                            current_file = os.path.join(recording_dir, filename)
                            
                            current_wav = wave.open(current_file, 'wb')
                            current_wav.setnchannels(channels)
                            current_wav.setsampwidth(sampwidth)
                            current_wav.setframerate(sample_rate)
                            
                            current_file_start_sample = next_boundary_sample
                            
                            # 次の境界を計算
                            next_boundary += timedelta(minutes=1)
                            next_boundary_sample += sample_rate * 60
                            
                            # UIに現在のファイル名を表示
                            self.root.after(0, lambda f=filename: self.rec_file_label.config(text=f"録音中: {f}"))
                            
                            logger.info(f"新規ファイル作成: {current_file}, 次の境界={next_boundary.strftime('%H:%M:%S')}")
                        
                        # ファイルに書き込み
                        if bit_depth == 24:
                            # int32からint24に変換
                            audio_data_converted = (audio_data >> 8).astype(np.int32)
                            current_wav.writeframes(audio_data_converted.tobytes())
                        else:
                            current_wav.writeframes(audio_data.tobytes())
                        
                        # レベルメーター更新（最新のフレームのみ）
                        # 整数データを -1.0 ~ 1.0 の範囲に正規化
                        if dtype == 'int16':
                            audio_normalized = audio_data.astype(np.float32) / 32768.0
                        else:  # int32
                            audio_normalized = audio_data.astype(np.float32) / 2147483648.0
                        
                        if channels == 1:
                            rms = np.sqrt(np.mean(audio_normalized**2))
                            db = 20 * np.log10(rms) if rms > 0 else -100
                            self.update_meter(db, db)
                        else:
                            rms_l = np.sqrt(np.mean(audio_normalized[:, 0]**2))
                            rms_r = np.sqrt(np.mean(audio_normalized[:, 1]**2))
                            db_l = 20 * np.log10(rms_l) if rms_l > 0 else -100
                            db_r = 20 * np.log10(rms_r) if rms_r > 0 else -100
                            self.update_meter(db_l, db_r)
                    
                    # 処理済みバッファをクリア
                    buffer_a.clear()
                
                # 少し待機
                threading.Event().wait(0.1)
            
            # 録音終了処理
            stream.stop()
            stream.close()
            
            # 残っているバッファを全て書き込む
            with buffer_lock:
                remaining_buffer = buffer_a + buffer_b
            
            for audio_data, sample_position in remaining_buffer:
                if current_wav:
                    if bit_depth == 24:
                        audio_data_converted = (audio_data >> 8).astype(np.int32)
                        current_wav.writeframes(audio_data_converted.tobytes())
                    else:
                        current_wav.writeframes(audio_data.tobytes())
            
            # 最後のファイルを閉じる
            if current_wav:
                current_wav.close()
                logger.info(f"最終ファイルクローズ: {current_file}")
            
        except Exception as e:
            logger.error(f"録音エラー: {e}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror("録音エラー", f"録音中にエラーが発生しました:\n{e}"))
            self.root.after(0, self.stop_recording)
    
    def update_recording_time(self):
        """録音時間表示の更新"""
        if self.recording:
            elapsed = datetime.now() - self.rec_start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            
            self.rec_time_label.config(text=f"録音時間: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # 1秒後に再度更新
            self.root.after(1000, self.update_recording_time)
        # self.stop_button.config(state=tk.NORMAL)
        # self.recording = True
    
    def stop_recording(self):
        """録音停止"""
        if not self.recording:
            return
        
        self.recording = False
        
        # スレッドの終了を待つ
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        # ストリームのクローズ
        if self.recording_stream:
            try:
                self.recording_stream.stop()
                self.recording_stream.close()
            except:
                pass
            self.recording_stream = None
        
        # メーターをリセット
        self.meter_l_canvas.delete("all")
        self.meter_r_canvas.delete("all")
        self.meter_l_label.config(text="-∞ dB")
        self.meter_r_label.config(text="-∞ dB")
        
        # UI更新
        self.rec_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.monitor_button.config(state=tk.NORMAL)
        self.rec_time_label.config(text="録音時間: 00:00:00")
        self.rec_file_label.config(text="")
        self.status_label.config(text="準備完了")
        
        logger.info("録音停止")
    
    # イベントハンドラ - アーカイブ関連
    def set_start_now(self):
        """開始時刻を現在時刻に設定"""
        now = datetime.now()
        self.start_date_var.set(now.strftime('%Y-%m-%d'))
        self.start_hour_var.set(now.strftime('%H'))
        self.start_min_var.set(now.strftime('%M'))
        self.start_sec_var.set(now.strftime('%S'))
    
    def set_end_now(self):
        """終了時刻を現在時刻に設定"""
        now = datetime.now()
        self.end_date_var.set(now.strftime('%Y-%m-%d'))
        self.end_hour_var.set(now.strftime('%H'))
        self.end_min_var.set(now.strftime('%M'))
        self.end_sec_var.set(now.strftime('%S'))
    
    def browse_output_dir(self):
        """保存先ディレクトリの選択"""
        directory = filedialog.askdirectory(
            title="保存先ディレクトリを選択",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
    
    def open_output_dir(self):
        """保存先ディレクトリを開く"""
        output_dir = self.output_dir_var.get()
        if os.path.exists(output_dir):
            if sys.platform == 'win32':
                os.startfile(output_dir)
            elif sys.platform == 'darwin':
                os.system(f'open "{output_dir}"')
            else:
                os.system(f'xdg-open "{output_dir}"')
        else:
            messagebox.showwarning("警告", f"ディレクトリが存在しません:\n{output_dir}")
    
    def start_merge(self):
        """結合処理の開始"""
        try:
            # 時刻のパース
            start_date_str = f"{self.start_date_var.get()} {self.start_hour_var.get()}:{self.start_min_var.get()}:{self.start_sec_var.get()}"
            end_date_str = f"{self.end_date_var.get()} {self.end_hour_var.get()}:{self.end_min_var.get()}:{self.end_sec_var.get()}"
            
            start_time = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
            
            if start_time >= end_time:
                messagebox.showerror("エラー", "開始時刻は終了時刻より前にしてください")
                return
            
            output_dir = self.output_dir_var.get()
            recording_dir = self.config.get('DEFAULT', 'recording_dir')
            
            # ディレクトリの確認
            if not os.path.exists(recording_dir):
                messagebox.showerror("エラー", f"録音ディレクトリが存在しません:\n{recording_dir}")
                return
            
            # 保存先ディレクトリの作成
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 別スレッドで結合処理を実行
            self.merge_button.config(state=tk.DISABLED)
            self.status_label.config(text="結合処理中...")
            
            thread = threading.Thread(target=self.merge_files_thread, 
                                    args=(start_time, end_time, recording_dir, output_dir),
                                    daemon=True)
            thread.start()
            
        except ValueError as e:
            messagebox.showerror("エラー", f"時刻フォーマットエラー:\n{e}")
        except Exception as e:
            messagebox.showerror("エラー", f"予期しないエラー:\n{e}")
            self.merge_button.config(state=tk.NORMAL)
    
    def merge_files_thread(self, start_time, end_time, recording_dir, output_dir):
        """結合処理スレッド"""
        try:
            self.log_merge(f"=== 結合処理開始 ===")
            self.log_merge(f"開始時刻: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_merge(f"終了時刻: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_merge(f"録音ディレクトリ: {recording_dir}")
            self.log_merge(f"保存先: {output_dir}")
            
            # 対象ファイルの検索
            wav_files = self.get_wav_files_in_timerange(start_time, end_time, recording_dir)
            
            if not wav_files:
                self.log_merge("ERROR: 指定された時間範囲内にWAVファイルが見つかりませんでした")
                messagebox.showwarning("警告", "指定された時間範囲内にWAVファイルが見つかりませんでした")
                return
            
            self.log_merge(f"対象ファイル数: {len(wav_files)}")
            for f in wav_files:
                self.log_merge(f"  - {os.path.basename(f)}")
            
            # 出力ファイル名の生成
            start_str = start_time.strftime('%Y%m%d-%H%M%S')
            end_str = end_time.strftime('%Y%m%d-%H%M%S')
            output_filename = f"merged_{start_str}_{end_str}.wav"
            output_path = os.path.join(output_dir, output_filename)
            
            self.log_merge(f"出力ファイル: {output_filename}")
            
            # ファイルの結合
            self.merge_wav_files(wav_files, output_path)
            
            self.log_merge("=== 結合完了 ===")
            self.log_merge("")
            
            messagebox.showinfo("完了", f"ファイルの結合が完了しました！\n\n{output_filename}")
            
        except Exception as e:
            self.log_merge(f"ERROR: {e}")
            messagebox.showerror("エラー", f"結合処理中にエラーが発生しました:\n{e}")
        
        finally:
            self.root.after(0, lambda: self.merge_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_label.config(text="準備完了"))
    
    def get_wav_files_in_timerange(self, start_time, end_time, recording_dir):
        """指定された時間範囲内のWAVファイルを取得"""
        # 検索範囲を前後1分ずつ拡張
        extended_start = start_time - timedelta(minutes=1)
        extended_end = end_time + timedelta(minutes=1)
        
        files_with_timestamps = []
        
        for file in os.listdir(recording_dir):
            if not file.endswith('.wav'):
                continue
            
            filepath = os.path.join(recording_dir, file)
            try:
                file_timestamp = self.get_wav_file_timestamp(filepath)
                if extended_start <= file_timestamp <= extended_end:
                    files_with_timestamps.append((filepath, file_timestamp))
            except Exception as e:
                logger.warning(f"ファイル {file} の処理中にエラー: {e}")
                continue
        
        # タイムスタンプ順でソート
        files_with_timestamps.sort(key=lambda x: x[1])
        return [filepath for filepath, _ in files_with_timestamps]
    
    def get_wav_file_timestamp(self, filepath):
        """WAVファイルのタイムスタンプを取得"""
        try:
            # ファイル名から時刻を取得 (rec_YYYYMMDD-HHMMSS.wav)
            filename = os.path.basename(filepath)
            if filename.startswith('rec_') and filename.endswith('.wav'):
                time_str = filename[4:19]  # rec_YYYYMMDD-HHMMSS
                return datetime.strptime(time_str, '%Y%m%d-%H%M%S')
        except (ValueError, IndexError):
            pass
        
        # ファイル名から取得できない場合は、ファイルの更新時刻を使用
        stat = os.stat(filepath)
        return datetime.fromtimestamp(stat.st_mtime)
    
    def merge_wav_files(self, input_files, output_file):
        """純粋Pythonでwaveモジュールを使用してWAVファイルを結合"""
        if not input_files:
            raise ValueError("結合するファイルが指定されていません")
        
        self.log_merge(f"結合開始: {len(input_files)} ファイル")
        
        # 最初のファイルからパラメータを取得
        with wave.open(input_files[0], 'rb') as first_wav:
            params = first_wav.getparams()
            nchannels = params.nchannels
            sampwidth = params.sampwidth
            framerate = params.framerate
            
            self.log_merge(f"WAVフォーマット: {nchannels}ch, {sampwidth*8}bit, {framerate}Hz")
        
        # 出力ファイルを開く
        with wave.open(output_file, 'wb') as output_wav:
            output_wav.setparams(params)
            
            # 各ファイルを順次読み込んで結合
            for i, file_path in enumerate(input_files, 1):
                try:
                    with wave.open(file_path, 'rb') as input_wav:
                        # フォーマットの整合性チェック
                        if (input_wav.getnchannels() != nchannels or
                            input_wav.getsampwidth() != sampwidth or
                            input_wav.getframerate() != framerate):
                            self.log_merge(f"WARNING: ファイル {os.path.basename(file_path)} のフォーマットが異なります。スキップします。")
                            continue
                        
                        # 音声データを読み込んで書き込む
                        frames = input_wav.readframes(input_wav.getnframes())
                        output_wav.writeframes(frames)
                        
                        self.log_merge(f"ファイル {i}/{len(input_files)} 結合完了: {os.path.basename(file_path)}")
                        
                except Exception as e:
                    self.log_merge(f"WARNING: ファイル {file_path} の結合中にエラー: {e}")
                    continue
        
        self.log_merge(f"結合完了: {output_file}")
    
    def log_merge(self, message):
        """結合ログの追加"""
        def update():
            self.merge_log_text.config(state=tk.NORMAL)
            self.merge_log_text.insert(tk.END, f"{message}\n")
            self.merge_log_text.see(tk.END)
            self.merge_log_text.config(state=tk.DISABLED)
        
        self.root.after(0, update)
    
    def clear_merge_log(self):
        """結合ログのクリア"""
        self.merge_log_text.config(state=tk.NORMAL)
        self.merge_log_text.delete(1.0, tk.END)
        self.merge_log_text.config(state=tk.DISABLED)
    
    # イベントハンドラ - 設定関連
    def browse_recording_dir(self):
        """録音ディレクトリの選択"""
        directory = filedialog.askdirectory(
            title="録音ディレクトリを選択",
            initialdir=self.recording_dir_var.get()
        )
        if directory:
            self.recording_dir_var.set(directory)
    
    def browse_directory(self, var, title):
        """汎用ディレクトリ選択"""
        directory = filedialog.askdirectory(
            title=title,
            initialdir=var.get()
        )
        if directory:
            var.set(directory)
    
    def create_directories(self):
        """ディレクトリの作成"""
        try:
            Path(self.recording_dir_var.get()).mkdir(parents=True, exist_ok=True)
            Path(self.config.get('DEFAULT', 'output_dir')).mkdir(parents=True, exist_ok=True)
            messagebox.showinfo("成功", "ディレクトリを作成しました")
        except Exception as e:
            messagebox.showerror("エラー", f"ディレクトリの作成に失敗しました:\n{e}")
    
    def save_all_config(self, default_output_var):
        """全設定の保存"""
        self.config['DEFAULT']['recording_dir'] = self.recording_dir_var.get()
        self.config['DEFAULT']['output_dir'] = default_output_var.get()
        self.config['DEFAULT']['audio_device'] = self.device_var.get()
        self.config['DEFAULT']['sample_rate'] = self.sample_rate_var.get()
        self.config['DEFAULT']['channels'] = self.channels_var.get()
        self.config['DEFAULT']['bit_depth'] = self.bit_depth_var.get()
        self.config['DEFAULT']['recording_retention_days'] = self.recording_retention_var.get()
        self.config['DEFAULT']['merged_retention_hours'] = self.merged_retention_var.get()
        
        # アーカイブタブの保存先も更新
        self.output_dir_var.set(default_output_var.get())
        
        self.save_config()
    
    def reset_to_default(self, default_output_var):
        """デフォルト設定に戻す"""
        if messagebox.askyesno("確認", "設定をデフォルトに戻しますか？"):
            for key, value in self.default_config.items():
                self.config['DEFAULT'][key] = value
            
            # UIを更新
            self.recording_dir_var.set(self.config.get('DEFAULT', 'recording_dir'))
            default_output_var.set(self.config.get('DEFAULT', 'output_dir'))
            self.output_dir_var.set(self.config.get('DEFAULT', 'output_dir'))
            self.device_var.set(self.config.get('DEFAULT', 'audio_device'))
            self.sample_rate_var.set(self.config.get('DEFAULT', 'sample_rate'))
            self.channels_var.set(self.config.get('DEFAULT', 'channels'))
            self.bit_depth_var.set(self.config.get('DEFAULT', 'bit_depth'))
            self.recording_retention_var.set(self.config.get('DEFAULT', 'recording_retention_days'))
            self.merged_retention_var.set(self.config.get('DEFAULT', 'merged_retention_hours'))
            
            self.save_config()
    
    
    # イベントハンドラ - Webサーバー関連
    def auto_start_webserver(self):
        """アプリ起動時に自動でWebサーバーを起動"""
        try:
            self.start_webserver()
            self.status_label.config(text="起動完了 - Webサーバー自動起動済み")
        except Exception as e:
            logger.error(f"Webサーバー自動起動エラー: {e}")
            messagebox.showwarning("警告", f"Webサーバーの自動起動に失敗しました:\n{e}\n\n手動で起動してください。")
    
    def start_webserver(self):
        """Webサーバー起動"""
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("エラー", "ポート番号は数値で入力してください")
            return
        
        def run_server():
            try:
                logger.info(f"Webサーバーを起動しています... (ポート: {port})")
                app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
            except Exception as e:
                logger.error(f"Webサーバーエラー: {e}")
                self.server_running = False
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.server_running = True
        
        # UI更新
        self.start_server_button.config(state=tk.DISABLED)
        self.stop_server_button.config(state=tk.NORMAL)
        self.open_browser_button.config(state=tk.NORMAL)
        self.server_status_label.config(text="● サーバー起動中", foreground="green")
        
        # IPアドレス一覧を取得して表示
        ip_addresses = self.get_local_ip_addresses()
        
        if ip_addresses:
            url_text = "アクセスURL:\n"
            for ip in ip_addresses:
                url_text += f"  http://{ip}:{port}\n"
            url_text += f"  http://localhost:{port} (ローカルのみ)"
        else:
            url_text = f"アクセスURL:\n  http://localhost:{port}"
        
        self.server_url_label.config(text=url_text)
        
        status_text = f"Webサーバー起動中"
        if ip_addresses:
            status_text += f": {ip_addresses[0]}:{port}"
        self.status_label.config(text=status_text)
        
        logger.info(f"Webサーバーが起動しました (ポート: {port})")
        if ip_addresses:
            logger.info("アクセス可能なURL:")
            for ip in ip_addresses:
                logger.info(f"  http://{ip}:{port}")
        logger.info(f"  http://localhost:{port} (ローカルのみ)")
        logger.info("ブラウザで上記URLを開くか、「🌐 ブラウザで開く」ボタンをクリックしてください")
    
    def stop_webserver(self):
        """Webサーバー停止（注意喚起のみ）"""
        messagebox.showwarning("注意", 
            "Webサーバーを停止するには、アプリケーションを再起動してください。\n\n" +
            "（Flaskサーバーは別スレッドで動作しているため、安全に停止できません）")
    
    def open_webui(self):
        """ブラウザでWeb UIを開く"""
        try:
            port = int(self.port_var.get())
            url = f"http://localhost:{port}"
            webbrowser.open(url)
            logger.info(f"ブラウザで開きました: {url}")
        except Exception as e:
            messagebox.showerror("エラー", f"ブラウザを開けませんでした:\n{e}")
    
    
    def cleanup_old_files(self):
        """古いファイルを削除（定期実行）- 同録ファイルとmergedファイル"""
        try:
            # 同録ファイル（録音ファイル）の削除
            recording_dir = self.config.get('DEFAULT', 'recording_dir')
            recording_retention_days = float(self.config.get('DEFAULT', 'recording_retention_days', fallback='90'))
            
            if os.path.exists(recording_dir):
                now = datetime.now()
                deleted_rec_count = 0
                
                for filename in os.listdir(recording_dir):
                    if not filename.startswith('rec_') or not filename.endswith('.wav'):
                        continue
                    
                    filepath = os.path.join(recording_dir, filename)
                    
                    try:
                        # ファイルの作成時刻を取得
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        age_days = (now - file_mtime).total_seconds() / 86400
                        
                        # 保持期間を超えていたら削除
                        if age_days > recording_retention_days:
                            os.remove(filepath)
                            deleted_rec_count += 1
                            logger.info(f"古い同録ファイルを削除: {filename} (経過日数: {age_days:.1f}日)")
                    
                    except Exception as e:
                        logger.warning(f"ファイル削除エラー: {filename} - {e}")
                
                if deleted_rec_count > 0:
                    logger.info(f"同録ファイルクリーンアップ完了: {deleted_rec_count}件削除")
            
            # mergedファイルの削除
            output_dir = self.config.get('DEFAULT', 'output_dir')
            merged_retention_hours = float(self.config.get('DEFAULT', 'merged_retention_hours', fallback='2'))
            
            if os.path.exists(output_dir):
                now = datetime.now()
                deleted_merged_count = 0
                
                for filename in os.listdir(output_dir):
                    if not filename.startswith('merged_') or not filename.endswith('.wav'):
                        continue
                    
                    filepath = os.path.join(output_dir, filename)
                    
                    try:
                        # ファイルの作成時刻を取得
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        age_hours = (now - file_mtime).total_seconds() / 3600
                        
                        # 保持時間を超えていたら削除
                        if age_hours > merged_retention_hours:
                            os.remove(filepath)
                            deleted_merged_count += 1
                            logger.info(f"古いmergedファイルを削除: {filename} (経過時間: {age_hours:.1f}時間)")
                    
                    except Exception as e:
                        logger.warning(f"ファイル削除エラー: {filename} - {e}")
                
                if deleted_merged_count > 0:
                    logger.info(f"mergedファイルクリーンアップ完了: {deleted_merged_count}件削除")
        
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
        
        finally:
            # 10分後に再度実行
            self.root.after(600000, self.cleanup_old_files)
    
    def on_closing(self):
        """ウィンドウクローズ時の処理"""
        # モニタリング中なら停止
        if self.monitoring:
            self.stop_monitor()
        
        if self.recording:
            if messagebox.askyesno("確認", "録音中です。終了しますか？"):
                self.root.destroy()
        elif self.server_running:
            if messagebox.askyesno("確認", "Webサーバーが起動中です。終了しますか？"):
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = RadioArchiverGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
