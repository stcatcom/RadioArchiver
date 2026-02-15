#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RadioArchiver - Recording & Archive System for Broadcast Stations

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
Version: 0.2.0
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

# Audio recording
try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None
    np = None

# Flask
from flask import Flask, request, send_file, jsonify, render_template_string

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
flask_app = Flask(__name__)

# ============================================================
# Internationalization (i18n)
# ============================================================

TRANSLATIONS = {
    'en': {
        # Window & Tabs
        'window_title': 'RadioArchiver - Recording & Archive System',
        'tab_recording': '📻 Recording',
        'tab_archive': '📼 Archive Merge',
        'tab_webui': '🌐 Web UI',
        'tab_settings': '⚙️ Settings',

        # Recording tab
        'recording_settings': 'Recording Settings',
        'recording_device': 'Recording Device:',
        'btn_refresh': '🔄 Refresh',
        'sample_rate': 'Sample Rate:',
        'channels': 'Channels:',
        'channels_hint': '(1=Mono, 2=Stereo)',
        'bit_depth': 'Bit Depth:',
        'level_meter': 'Level Meter',
        'btn_monitor_start': '🎧 Start Monitor',
        'btn_monitor_stop': '⏹ Stop Monitor',
        'btn_rec_start': '⏺ Start Recording',
        'btn_stop': '⏹ Stop',
        'rec_time': 'Recording Time: {time}',
        'recording_file': 'Recording: {filename}',

        # Archive tab
        'merge_settings': 'Merge Settings',
        'start_time': 'Start Time:',
        'end_time': 'End Time:',
        'btn_now': 'Now',
        'output_dir': 'Output:',
        'btn_browse': 'Browse...',
        'btn_merge': '🔄 Start Merge',
        'btn_open_output': '📁 Open Output Folder',
        'process_log': 'Process Log',
        'btn_clear_log': 'Clear Log',

        # Web UI tab
        'webserver_settings': 'Web Server Settings',
        'port': 'Port:',
        'port_default': '(Default: 5000)',
        'btn_start_server': '▶ Start Server',
        'btn_stop_server': '⏹ Stop Server',
        'btn_open_browser': '🌐 Open in Browser',
        'server_stopped': '● Server Stopped',
        'server_running': '● Server Running',
        'webui_info': '''With Web UI, you can perform merge operations from smartphones and tablets.

Usage:
1. Click "▶ Start Server"
2. Click "🌐 Open in Browser" or open the URL directly
3. Enter start/end time and start merging''',
        'system_log': 'System Log (Recording / Cleanup / Server):',

        # Settings tab
        'directory_settings': 'Directory Settings',
        'recording_dir': 'Recording Directory:',
        'recording_dir_note': 'Directory where recorded WAV files are saved (rec_YYYYMMDD-HHMMSS.wav format)',
        'merged_output_dir': 'Merged File Output:',
        'merged_output_note': 'Default output directory for merged WAV files',
        'retention_settings': 'File Retention Settings',
        'recording_retention': 'Recording File Retention:',
        'unit_days': 'days',
        'recording_retention_note': "Retention period for 1-minute recording files (rec_*.wav)\n"
                                    "* For terrestrial broadcasters, 3 months (90 days) retention is legally required",
        'merged_retention': 'Merged File Retention:',
        'unit_hours': 'hours',
        'merged_retention_note': 'Retention period for merged files (merged_*.wav)',
        'btn_create_dirs': '📁 Create Directories',
        'btn_save_settings': '💾 Save Settings',
        'btn_reset_default': '🔄 Reset to Default',
        'language_label': 'Language:',
        'language_restart_note': 'Restart the application after changing the language',
        'app_info': '''RadioArchiver - Recording & Archive System
Version 0.2.0

© 2026 Masaya Miyazaki / Office Stray Cat
Licensed under the MIT License

https://stcat.com/
https://github.com/stcatcom/RadioArchiver''',

        # Status bar
        'status_ready': 'Ready',
        'status_monitoring': 'Monitoring...',
        'status_recording': '🔴 Recording...',
        'status_merging': 'Merging...',
        'status_startup_complete': 'Startup complete - Web server auto-started',
        'status_webserver_running': 'Web server running',

        # Dialogs
        'dlg_success': 'Success',
        'dlg_error': 'Error',
        'dlg_warning': 'Warning',
        'dlg_confirm': 'Confirm',
        'dlg_complete': 'Complete',
        'dlg_recording_error': 'Recording Error',
        'dlg_notice': 'Notice',

        # Messages
        'msg_settings_saved': 'Settings saved.',
        'msg_settings_save_failed': 'Failed to save settings:\n{error}',
        'msg_sounddevice_not_installed': 'sounddevice is not installed.\n\n'
                                         'To use recording features, install it with:\n'
                                         'pip install sounddevice',
        'msg_sounddevice_missing': 'sounddevice is not installed',
        'msg_select_valid_device': 'Please select a valid recording device',
        'msg_no_valid_device': 'No valid recording device selected',
        'msg_monitor_error': 'Monitor start error:\n{error}',
        'msg_rec_dir_create_failed': 'Failed to create recording directory:\n{error}',
        'msg_recording_error': 'An error occurred during recording:\n{error}',
        'msg_start_before_end': 'Start time must be before end time',
        'msg_rec_dir_not_found': 'Recording directory does not exist:\n{path}',
        'msg_time_format_error': 'Time format error:\n{error}',
        'msg_unexpected_error': 'Unexpected error:\n{error}',
        'msg_merge_error': 'An error occurred during merge:\n{error}',
        'msg_no_wav_in_range': 'No WAV files found in the specified time range',
        'msg_merge_complete': 'File merge complete!\n\n{filename}',
        'msg_dirs_created': 'Directories created.',
        'msg_dirs_create_failed': 'Failed to create directories:\n{error}',
        'msg_confirm_reset': 'Reset settings to default?',
        'msg_confirm_quit_recording': 'Recording is in progress. Quit?',
        'msg_confirm_quit_server': 'Web server is running. Quit?',
        'msg_port_not_number': 'Port number must be numeric',
        'msg_server_stop_notice': 'To stop the web server, restart the application.\n\n'
                                  '(The Flask server runs in a separate thread and cannot be safely stopped)',
        'msg_browser_open_failed': 'Failed to open browser:\n{error}',
        'msg_webserver_autostart_failed': 'Failed to auto-start web server:\n{error}\n\nPlease start it manually.',
        'msg_dir_not_found': 'Directory does not exist:\n{path}',
        'msg_no_files_specified': 'No files specified for merge',
        'msg_device_not_installed': 'sounddevice is not installed',
        'msg_no_recording_device': 'No recording devices found',

        # Access URL
        'access_url': 'Access URL:',
        'local_only': '(local only)',

        # Web UI HTML
        'web_title': 'RadioArchiver - Merge Recording Files',
        'web_heading': '🎵 RadioArchiver - Web UI',
        'web_subtitle': 'Merge recording files within a specified time range',
        'web_start_time': '📅 Start Time:',
        'web_end_time': '📅 End Time:',
        'web_btn_merge': '🔄 Start Merge',
        'web_config_info': 'Configuration:',
        'web_recording_dir': 'Recording Directory: ',
        'web_output_dir': 'Output Directory: ',
        'web_error_start_before_end': 'Error: Start time must be before end time.',
        'web_processing': '⏳ Processing... Please wait',
        'web_processing_btn': 'Processing...',
        'web_merge_complete': '✅ File merge complete!',
        'web_download': '💾 Download merged file',
        'web_error_prefix': '❌ Error: ',

        # API messages
        'api_not_initialized': 'Application not initialized',
        'api_params_required': 'start_time and end_time parameters are required',
        'api_time_format_error': 'Time format error: {error}',
        'api_start_before_end': 'Start time must be before end time',
        'api_output_dir_failed': 'Failed to create output directory: {error}',
        'api_no_wav_in_range': 'No WAV files found in the specified time range',
        'api_unexpected_error': 'Unexpected error: {error}',
        'api_loading': 'Loading settings...',

        # Merge log messages
        'log_merge_start': '=== Merge started ===',
        'log_start_time': 'Start time: {time}',
        'log_end_time': 'End time: {time}',
        'log_recording_dir': 'Recording directory: {dir}',
        'log_output_dir': 'Output: {dir}',
        'log_no_wav': 'ERROR: No WAV files found in the specified time range',
        'log_file_count': 'Target files: {count}',
        'log_output_file': 'Output file: {filename}',
        'log_merge_complete': '=== Merge complete ===',
        'log_merging_files': 'Merging: {count} files',
        'log_wav_format': 'WAV format: {ch}ch, {bits}bit, {rate}Hz',
        'log_format_mismatch': 'WARNING: File {filename} has different format. Skipping.',
        'log_file_merged': 'File {i}/{total} merged: {filename}',
        'log_file_merge_error': 'WARNING: Error merging file {filepath}: {error}',
        'log_merged_output': 'Merge complete: {filepath}',
        'log_devices_updated': 'Audio device list updated ({count} devices)',
    },
    'ja': {
        # Window & Tabs
        'window_title': 'RadioArchiver - 録音・アーカイブ統合システム',
        'tab_recording': '📻 録音',
        'tab_archive': '📼 アーカイブ結合',
        'tab_webui': '🌐 Web UI',
        'tab_settings': '⚙️ 設定',

        # Recording tab
        'recording_settings': '録音設定',
        'recording_device': '録音デバイス:',
        'btn_refresh': '🔄 更新',
        'sample_rate': 'サンプルレート:',
        'channels': 'チャンネル数:',
        'channels_hint': '(1=モノラル, 2=ステレオ)',
        'bit_depth': 'ビット深度:',
        'level_meter': 'レベルメーター',
        'btn_monitor_start': '🎧 モニター開始',
        'btn_monitor_stop': '⏹ モニター停止',
        'btn_rec_start': '⏺ 録音開始',
        'btn_stop': '⏹ 停止',
        'rec_time': '録音時間: {time}',
        'recording_file': '録音中: {filename}',

        # Archive tab
        'merge_settings': '結合設定',
        'start_time': '開始時刻:',
        'end_time': '終了時刻:',
        'btn_now': '現在時刻',
        'output_dir': '保存先:',
        'btn_browse': '参照...',
        'btn_merge': '🔄 結合開始',
        'btn_open_output': '📁 保存先を開く',
        'process_log': '処理ログ',
        'btn_clear_log': 'ログをクリア',

        # Web UI tab
        'webserver_settings': 'Webサーバー設定',
        'port': 'ポート:',
        'port_default': '(デフォルト: 5000)',
        'btn_start_server': '▶ サーバー起動',
        'btn_stop_server': '⏹ サーバー停止',
        'btn_open_browser': '🌐 ブラウザで開く',
        'server_stopped': '● サーバー停止中',
        'server_running': '● サーバー起動中',
        'webui_info': '''Web UIを使用すると、スマホやタブレットからも結合操作ができます。

使い方:
1. 「▶ サーバー起動」をクリック
2. 「🌐 ブラウザで開く」をクリック、またはURL を直接開く
3. 開始時刻・終了時刻を入力して結合開始''',
        'system_log': 'システムログ（録音・削除・サーバーなど）:',

        # Settings tab
        'directory_settings': 'ディレクトリ設定',
        'recording_dir': '録音ディレクトリ:',
        'recording_dir_note': '録音されたWAVファイルが保存されるディレクトリ（rec_YYYYMMDD-HHMMSS.wav形式）',
        'merged_output_dir': '結合ファイル保存先:',
        'merged_output_note': '結合されたWAVファイルのデフォルト保存先',
        'retention_settings': 'ファイル保持期間設定',
        'recording_retention': '同録ファイル保持期間:',
        'unit_days': '日',
        'recording_retention_note': '録音された1分ごとのファイル（rec_*.wav）の保持期間\n'
                                    '※ 地上波放送局の場合、放送法により3ヶ月（90日）以上の保存が義務付けられています',
        'merged_retention': '結合ファイル保持期間:',
        'unit_hours': '時間',
        'merged_retention_note': '結合されたファイル（merged_*.wav）の保持期間',
        'btn_create_dirs': '📁 ディレクトリを作成',
        'btn_save_settings': '💾 設定を保存',
        'btn_reset_default': '🔄 デフォルトに戻す',
        'language_label': '言語 / Language:',
        'language_restart_note': '言語変更後はアプリケーションを再起動してください',
        'app_info': '''RadioArchiver - 録音・アーカイブ統合システム
Version 0.2.0

© 2026 Masaya Miyazaki / Office Stray Cat
Licensed under the MIT License

https://stcat.com/
https://github.com/stcatcom/RadioArchiver''',

        # Status bar
        'status_ready': '準備完了',
        'status_monitoring': 'モニタリング中...',
        'status_recording': '🔴 録音中...',
        'status_merging': '結合処理中...',
        'status_startup_complete': '起動完了 - Webサーバー自動起動済み',
        'status_webserver_running': 'Webサーバー起動中',

        # Dialogs
        'dlg_success': '成功',
        'dlg_error': 'エラー',
        'dlg_warning': '警告',
        'dlg_confirm': '確認',
        'dlg_complete': '完了',
        'dlg_recording_error': '録音エラー',
        'dlg_notice': '注意',

        # Messages
        'msg_settings_saved': '設定を保存しました',
        'msg_settings_save_failed': '設定の保存に失敗しました:\n{error}',
        'msg_sounddevice_not_installed': 'sounddeviceがインストールされていません。\n\n'
                                         '録音機能を使用するには、以下のコマンドでインストールしてください:\n'
                                         'pip install sounddevice',
        'msg_sounddevice_missing': 'sounddeviceがインストールされていません',
        'msg_select_valid_device': '有効な録音デバイスを選択してください',
        'msg_no_valid_device': '有効な録音デバイスが選択されていません',
        'msg_monitor_error': 'モニタリング開始エラー:\n{error}',
        'msg_rec_dir_create_failed': '録音ディレクトリの作成に失敗しました:\n{error}',
        'msg_recording_error': '録音中にエラーが発生しました:\n{error}',
        'msg_start_before_end': '開始時刻は終了時刻より前にしてください',
        'msg_rec_dir_not_found': '録音ディレクトリが存在しません:\n{path}',
        'msg_time_format_error': '時刻フォーマットエラー:\n{error}',
        'msg_unexpected_error': '予期しないエラー:\n{error}',
        'msg_merge_error': '結合処理中にエラーが発生しました:\n{error}',
        'msg_no_wav_in_range': '指定された時間範囲内にWAVファイルが見つかりませんでした',
        'msg_merge_complete': 'ファイルの結合が完了しました！\n\n{filename}',
        'msg_dirs_created': 'ディレクトリを作成しました',
        'msg_dirs_create_failed': 'ディレクトリの作成に失敗しました:\n{error}',
        'msg_confirm_reset': '設定をデフォルトに戻しますか？',
        'msg_confirm_quit_recording': '録音中です。終了しますか？',
        'msg_confirm_quit_server': 'Webサーバーが起動中です。終了しますか？',
        'msg_port_not_number': 'ポート番号は数値で入力してください',
        'msg_server_stop_notice': 'Webサーバーを停止するには、アプリケーションを再起動してください。\n\n'
                                  '（Flaskサーバーは別スレッドで動作しているため、安全に停止できません）',
        'msg_browser_open_failed': 'ブラウザを開けませんでした:\n{error}',
        'msg_webserver_autostart_failed': 'Webサーバーの自動起動に失敗しました:\n{error}\n\n手動で起動してください。',
        'msg_dir_not_found': 'ディレクトリが存在しません:\n{path}',
        'msg_no_files_specified': '結合するファイルが指定されていません',
        'msg_device_not_installed': 'sounddeviceがインストールされていません',
        'msg_no_recording_device': '録音可能なデバイスが見つかりません',

        # Access URL
        'access_url': 'アクセスURL:',
        'local_only': '(ローカルのみ)',

        # Web UI HTML
        'web_title': 'RadioArchiver - 録音ファイル結合',
        'web_heading': '🎵 RadioArchiver - Web UI',
        'web_subtitle': '録音ファイルを指定した時間範囲で結合します',
        'web_start_time': '📅 開始時刻:',
        'web_end_time': '📅 終了時刻:',
        'web_btn_merge': '🔄 結合開始',
        'web_config_info': '設定情報:',
        'web_recording_dir': '録音ディレクトリ: ',
        'web_output_dir': '保存先ディレクトリ: ',
        'web_error_start_before_end': 'エラー: 開始時刻は終了時刻より前にしてください。',
        'web_processing': '⏳ 処理中... しばらくお待ちください',
        'web_processing_btn': '処理中...',
        'web_merge_complete': '✅ ファイルの結合が完了しました！',
        'web_download': '💾 結合したファイルをダウンロード',
        'web_error_prefix': '❌ エラー: ',

        # API messages
        'api_not_initialized': 'アプリケーションが初期化されていません',
        'api_params_required': 'start_time と end_time パラメータが必要です',
        'api_time_format_error': '時刻フォーマットエラー: {error}',
        'api_start_before_end': '開始時刻は終了時刻より前にしてください',
        'api_output_dir_failed': '保存先ディレクトリの作成に失敗しました: {error}',
        'api_no_wav_in_range': '指定された時間範囲内にWAVファイルが見つかりませんでした',
        'api_unexpected_error': '予期しないエラーが発生しました: {error}',
        'api_loading': '設定を読み込み中...',

        # Merge log messages
        'log_merge_start': '=== 結合処理開始 ===',
        'log_start_time': '開始時刻: {time}',
        'log_end_time': '終了時刻: {time}',
        'log_recording_dir': '録音ディレクトリ: {dir}',
        'log_output_dir': '保存先: {dir}',
        'log_no_wav': 'ERROR: 指定された時間範囲内にWAVファイルが見つかりませんでした',
        'log_file_count': '対象ファイル数: {count}',
        'log_output_file': '出力ファイル: {filename}',
        'log_merge_complete': '=== 結合完了 ===',
        'log_merging_files': '結合開始: {count} ファイル',
        'log_wav_format': 'WAVフォーマット: {ch}ch, {bits}bit, {rate}Hz',
        'log_format_mismatch': 'WARNING: ファイル {filename} のフォーマットが異なります。スキップします。',
        'log_file_merged': 'ファイル {i}/{total} 結合完了: {filename}',
        'log_file_merge_error': 'WARNING: ファイル {filepath} の結合中にエラー: {error}',
        'log_merged_output': '結合完了: {filepath}',
        'log_devices_updated': 'オーディオデバイス一覧を更新しました ({count} 件)',
    }
}

# Current language (will be set from config)
current_lang = 'en'

def t(key, **kwargs):
    """Get translated string for the current language."""
    text = TRANSLATIONS.get(current_lang, TRANSLATIONS['en']).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text

# Language display names
LANGUAGE_OPTIONS = {
    'English': 'en',
    '日本語': 'ja',
}
LANGUAGE_NAMES = {v: k for k, v in LANGUAGE_OPTIONS.items()}

# ============================================================
# HTML Template (generated per-language)
# ============================================================

def get_html_template():
    """Generate HTML template for the current language."""
    return '''
<!DOCTYPE html>
<html lang="''' + ('ja' if current_lang == 'ja' else 'en') + '''">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>''' + t('web_title') + '''</title>
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
        <h1>''' + t('web_heading') + '''</h1>
        <p style="text-align: center; color: #666; margin-bottom: 30px;">
            ''' + t('web_subtitle') + '''
        </p>

        <form id="mergeForm">
            <div class="form-group">
                <label for="startTime">''' + t('web_start_time') + '''</label>
                <input type="datetime-local" id="startTime" required>
            </div>
            <div class="form-group">
                <label for="endTime">''' + t('web_end_time') + '''</label>
                <input type="datetime-local" id="endTime" required>
            </div>
            <button type="submit" id="submitBtn">''' + t('web_btn_merge') + '''</button>
        </form>

        <div id="result"></div>

        <div class="config-info">
            <strong>''' + t('web_config_info') + '''</strong><br>
            ''' + t('web_recording_dir') + '''{{ recording_dir }}<br>
            ''' + t('web_output_dir') + '''{{ output_dir }}
        </div>

        <div class="footer">
            1999-2026 (c) Office Stray Cat all rights reserved.
        </div>
    </div>

    <script>
        const STRINGS = {
            errorStartBeforeEnd: "''' + t('web_error_start_before_end').replace('"', '\\"') + '''",
            processing: "''' + t('web_processing').replace('"', '\\"') + '''",
            processingBtn: "''' + t('web_processing_btn').replace('"', '\\"') + '''",
            mergeComplete: "''' + t('web_merge_complete').replace('"', '\\"') + '''",
            download: "''' + t('web_download').replace('"', '\\"') + '''",
            errorPrefix: "''' + t('web_error_prefix').replace('"', '\\"') + '''",
            btnMerge: "''' + t('web_btn_merge').replace('"', '\\"') + '''"
        };

        document.getElementById('mergeForm').onsubmit = async (e) => {
            e.preventDefault();

            const startTime = new Date(document.getElementById('startTime').value);
            const endTime = new Date(document.getElementById('endTime').value);
            const submitBtn = document.getElementById('submitBtn');

            if (startTime >= endTime) {
                showResult('error', STRINGS.errorStartBeforeEnd);
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

            showResult('processing', STRINGS.processing);
            submitBtn.disabled = true;
            submitBtn.textContent = STRINGS.processingBtn;

            try {
                const response = await fetch(`/merge?start_time=${formatDate(startTime)}&end_time=${formatDate(endTime)}`);

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const filename = `merged_${formatDate(startTime)}_${formatDate(endTime)}.wav`;

                    showResult('success', `
                        <p>${STRINGS.mergeComplete}</p>
                        <a href="${url}" download="${filename}" class="download-link">
                            ${STRINGS.download} (${filename})
                        </a>
                    `);
                } else {
                    const error = await response.json();
                    showResult('error', `${STRINGS.errorPrefix}${error.error}`);
                }
            } catch (error) {
                showResult('error', `${STRINGS.errorPrefix}${error.message}`);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = STRINGS.btnMerge;
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

# Global variable (referenced by Flask)
gui_instance = None

# Flask routes
@flask_app.route('/')
def index():
    """Main page"""
    if gui_instance:
        recording_dir = gui_instance.config.get('DEFAULT', 'recording_dir')
        output_dir = gui_instance.config.get('DEFAULT', 'output_dir')
    else:
        recording_dir = t('api_loading')
        output_dir = t('api_loading')

    return render_template_string(get_html_template(),
                                recording_dir=recording_dir,
                                output_dir=output_dir)

@flask_app.route('/merge')
def merge_files():
    """WAV file merge API"""
    if not gui_instance:
        return jsonify({'error': t('api_not_initialized')}), 500

    try:
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')

        if not start_time_str or not end_time_str:
            return jsonify({'error': t('api_params_required')}), 400

        try:
            start_time = datetime.strptime(start_time_str, '%Y%m%d-%H%M%S')
            end_time = datetime.strptime(end_time_str, '%Y%m%d-%H%M%S')
        except ValueError as e:
            return jsonify({'error': t('api_time_format_error', error=str(e))}), 400

        if start_time >= end_time:
            return jsonify({'error': t('api_start_before_end')}), 400

        recording_dir = gui_instance.config.get('DEFAULT', 'recording_dir')
        output_dir = gui_instance.config.get('DEFAULT', 'output_dir')

        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return jsonify({'error': t('api_output_dir_failed', error=str(e))}), 400

        wav_files = gui_instance.get_wav_files_in_timerange(start_time, end_time, recording_dir)
        if not wav_files:
            return jsonify({'error': t('api_no_wav_in_range')}), 404

        logger.info(f"Merge target files: {len(wav_files)}")

        output_filename = f"merged_{start_time_str}_{end_time_str}.wav"
        output_path = os.path.join(output_dir, output_filename)

        gui_instance.merge_wav_files(wav_files, output_path)

        return send_file(output_path,
                        as_attachment=True,
                        download_name=output_filename,
                        mimetype='audio/wav')

    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': t('api_unexpected_error', error=str(e))}), 500

@flask_app.route('/health')
def health_check():
    """Health check"""
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
        self.root.title(t('window_title'))
        self.root.geometry("900x750")
        self.root.resizable(True, True)

        # Recording state
        self.recording = False
        self.recording_thread = None
        self.recording_stream = None
        self.rec_start_time = None

        # Monitoring state
        self.monitoring = False
        self.monitor_stream = None

        # Web server state
        self.server_running = False
        self.server_thread = None

        # Load config
        self.load_config()

        # Build UI
        self.create_widgets()

        # Auto-start web server
        self.root.after(500, self.auto_start_webserver)

        # Periodic cleanup (every 10 minutes)
        self.root.after(60000, self.cleanup_old_files)

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        """Load configuration file"""
        global current_lang
        self.config = configparser.ConfigParser()

        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(__file__)

        self.config_path = os.path.join(app_dir, 'config.ini')

        # Default settings
        self.default_config = {
            'recording_dir': 'C:/RadioArchiver/rec' if sys.platform == 'win32' else os.path.expanduser('~') + "/rec",
            'output_dir': 'C:/RadioArchiver/merged' if sys.platform == 'win32' else '/tmp/wav_merged',
            'audio_device': '',
            'sample_rate': '44100',
            'channels': '2',
            'bit_depth': '16',
            'recording_retention_days': '90',
            'merged_retention_hours': '2',
            'language': 'en'
        }

        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')

        for key, value in self.default_config.items():
            if not self.config.has_option('DEFAULT', key):
                self.config['DEFAULT'][key] = value

        # Apply language setting
        lang = self.config.get('DEFAULT', 'language', fallback='en')
        if lang in TRANSLATIONS:
            current_lang = lang

    def save_config(self):
        """Save configuration file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            messagebox.showinfo(t('dlg_success'), t('msg_settings_saved'))
            logger.info(f"Settings saved: {self.config_path}")
        except Exception as e:
            messagebox.showerror(t('dlg_error'), t('msg_settings_save_failed', error=e))
            logger.error(f"Settings save error: {e}")

    def create_widgets(self):
        """Build UI"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.recording_tab = ttk.Frame(notebook)
        notebook.add(self.recording_tab, text=t('tab_recording'))
        self.create_recording_tab()

        self.archive_tab = ttk.Frame(notebook)
        notebook.add(self.archive_tab, text=t('tab_archive'))
        self.create_archive_tab()

        self.webserver_tab = ttk.Frame(notebook)
        notebook.add(self.webserver_tab, text=t('tab_webui'))
        self.create_webserver_tab()

        self.settings_tab = ttk.Frame(notebook)
        notebook.add(self.settings_tab, text=t('tab_settings'))
        self.create_settings_tab()

        self.create_status_bar()

    def get_local_ip_addresses(self):
        """Get list of local IP addresses"""
        ip_addresses = []

        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if ':' not in ip and not ip.startswith('127.'):
                    if ip not in ip_addresses:
                        ip_addresses.append(ip)
        except Exception as e:
            logger.warning(f"IP address retrieval error: {e}")

        try:
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
        """Get list of available recording devices"""
        devices = []

        if not SOUNDDEVICE_AVAILABLE:
            return [(t('msg_device_not_installed'), -1)]

        try:
            device_list = sd.query_devices()

            for idx, device in enumerate(device_list):
                if device['max_input_channels'] > 0:
                    name = device['name']
                    channels = device['max_input_channels']
                    sample_rate = int(device['default_samplerate'])
                    device_info = f"[{idx}] {name} ({channels}ch, {sample_rate}Hz)"
                    devices.append((device_info, idx))

            if not devices:
                devices.append((t('msg_no_recording_device'), -1))

        except Exception as e:
            logger.error(f"Device list error: {e}")
            devices.append((f"Error: {e}", -1))

        return devices

    def create_recording_tab(self):
        """Create recording tab"""
        frame = ttk.LabelFrame(self.recording_tab, text=t('recording_settings'), padding=15)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0
        ttk.Label(frame, text=t('recording_device')).grid(row=row, column=0, sticky=tk.W, pady=5)

        device_frame = ttk.Frame(frame)
        device_frame.grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=5)

        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.device_var, width=60, state='readonly')
        self.device_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(device_frame, text=t('btn_refresh'), command=self.refresh_devices, width=10).pack(side=tk.LEFT)

        self.refresh_devices()

        row += 1
        ttk.Label(frame, text=t('sample_rate')).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.sample_rate_var = tk.StringVar(value=self.config.get('DEFAULT', 'sample_rate', fallback='44100'))
        sample_rate_combo = ttk.Combobox(frame, textvariable=self.sample_rate_var, width=20, state='readonly')
        sample_rate_combo['values'] = ['44100', '48000', '96000']
        sample_rate_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text="Hz").grid(row=row, column=2, sticky=tk.W)

        row += 1
        ttk.Label(frame, text=t('channels')).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.channels_var = tk.StringVar(value=self.config.get('DEFAULT', 'channels', fallback='2'))
        channels_combo = ttk.Combobox(frame, textvariable=self.channels_var, width=20, state='readonly')
        channels_combo['values'] = ['1', '2']
        channels_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text=t('channels_hint')).grid(row=row, column=2, sticky=tk.W, padx=5)

        row += 1
        ttk.Label(frame, text=t('bit_depth')).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.bit_depth_var = tk.StringVar(value=self.config.get('DEFAULT', 'bit_depth', fallback='16'))
        bit_depth_combo = ttk.Combobox(frame, textvariable=self.bit_depth_var, width=20, state='readonly')
        bit_depth_combo['values'] = ['16', '24', '32']
        bit_depth_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text="bit").grid(row=row, column=2, sticky=tk.W)

        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)

        row += 1
        meter_frame = ttk.LabelFrame(frame, text=t('level_meter'), padding=10)
        meter_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=10)

        l_frame = ttk.Frame(meter_frame)
        l_frame.pack(fill=tk.X, pady=5)
        ttk.Label(l_frame, text="L:", width=3).pack(side=tk.LEFT)
        self.meter_l_canvas = tk.Canvas(l_frame, height=20, bg='#2b2b2b', highlightthickness=0)
        self.meter_l_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.meter_l_label = ttk.Label(l_frame, text="-\u221e dB", width=10, anchor=tk.E)
        self.meter_l_label.pack(side=tk.LEFT)

        r_frame = ttk.Frame(meter_frame)
        r_frame.pack(fill=tk.X, pady=5)
        ttk.Label(r_frame, text="R:", width=3).pack(side=tk.LEFT)
        self.meter_r_canvas = tk.Canvas(r_frame, height=20, bg='#2b2b2b', highlightthickness=0)
        self.meter_r_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.meter_r_label = ttk.Label(r_frame, text="-\u221e dB", width=10, anchor=tk.E)
        self.meter_r_label.pack(side=tk.LEFT)

        row += 1
        monitor_frame = ttk.Frame(frame)
        monitor_frame.grid(row=row, column=0, columnspan=3, pady=10)

        self.monitor_button = ttk.Button(monitor_frame, text=t('btn_monitor_start'),
                                        command=self.toggle_monitor, width=20)
        self.monitor_button.pack(side=tk.LEFT, padx=5)

        row += 1
        control_frame = ttk.Frame(frame)
        control_frame.grid(row=row, column=0, columnspan=3, pady=20)

        self.rec_button = ttk.Button(control_frame, text=t('btn_rec_start'),
                                     command=self.start_recording, width=20)
        self.rec_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text=t('btn_stop'),
                                      command=self.stop_recording,
                                      width=20, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        row += 1
        self.rec_time_label = ttk.Label(frame, text=t('rec_time', time='00:00:00'), font=("Arial", 14))
        self.rec_time_label.grid(row=row, column=0, columnspan=3, pady=10)

        row += 1
        self.rec_file_label = ttk.Label(frame, text="", font=("Arial", 9), foreground="gray")
        self.rec_file_label.grid(row=row, column=0, columnspan=3, pady=5)

        frame.columnconfigure(1, weight=1)

    def create_archive_tab(self):
        """Create archive merge tab"""
        main_frame = ttk.Frame(self.archive_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        settings_frame = ttk.LabelFrame(main_frame, text=t('merge_settings'), padding=15)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        row = 0
        ttk.Label(settings_frame, text=t('start_time')).grid(row=row, column=0, sticky=tk.W, pady=5)

        time_frame_start = ttk.Frame(settings_frame)
        time_frame_start.grid(row=row, column=1, sticky=tk.W, pady=5)

        self.start_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(time_frame_start, textvariable=self.start_date_var, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_start, text="").pack(side=tk.LEFT, padx=2)

        self.start_hour_var = tk.StringVar(value='00')
        self.start_min_var = tk.StringVar(value='00')
        self.start_sec_var = tk.StringVar(value='00')

        ttk.Entry(time_frame_start, textvariable=self.start_hour_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_start, text=":").pack(side=tk.LEFT)
        ttk.Entry(time_frame_start, textvariable=self.start_min_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_start, text=":").pack(side=tk.LEFT)
        ttk.Entry(time_frame_start, textvariable=self.start_sec_var, width=4).pack(side=tk.LEFT, padx=2)

        ttk.Button(time_frame_start, text=t('btn_now'), command=self.set_start_now, width=10).pack(side=tk.LEFT, padx=10)

        row += 1
        ttk.Label(settings_frame, text=t('end_time')).grid(row=row, column=0, sticky=tk.W, pady=5)

        time_frame_end = ttk.Frame(settings_frame)
        time_frame_end.grid(row=row, column=1, sticky=tk.W, pady=5)

        self.end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(time_frame_end, textvariable=self.end_date_var, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_end, text="").pack(side=tk.LEFT, padx=2)

        self.end_hour_var = tk.StringVar(value='01')
        self.end_min_var = tk.StringVar(value='00')
        self.end_sec_var = tk.StringVar(value='00')

        ttk.Entry(time_frame_end, textvariable=self.end_hour_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_end, text=":").pack(side=tk.LEFT)
        ttk.Entry(time_frame_end, textvariable=self.end_min_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame_end, text=":").pack(side=tk.LEFT)
        ttk.Entry(time_frame_end, textvariable=self.end_sec_var, width=4).pack(side=tk.LEFT, padx=2)

        ttk.Button(time_frame_end, text=t('btn_now'), command=self.set_end_now, width=10).pack(side=tk.LEFT, padx=10)

        row += 1
        ttk.Label(settings_frame, text=t('output_dir')).grid(row=row, column=0, sticky=tk.W, pady=5)

        output_frame = ttk.Frame(settings_frame)
        output_frame.grid(row=row, column=1, sticky=tk.EW, pady=5)

        self.output_dir_var = tk.StringVar(value=self.config.get('DEFAULT', 'output_dir'))
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text=t('btn_browse'), command=self.browse_output_dir, width=10).pack(side=tk.LEFT)

        row += 1
        ttk.Separator(settings_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=15)

        row += 1
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)

        self.merge_button = ttk.Button(button_frame, text=t('btn_merge'),
                                      command=self.start_merge, width=25)
        self.merge_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text=t('btn_open_output'),
                  command=self.open_output_dir, width=25).pack(side=tk.LEFT, padx=5)

        settings_frame.columnconfigure(1, weight=1)

        log_frame = ttk.LabelFrame(main_frame, text=t('process_log'), padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.merge_log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80, state=tk.DISABLED)
        self.merge_log_text.pack(fill=tk.BOTH, expand=True)

        ttk.Button(log_frame, text=t('btn_clear_log'), command=self.clear_merge_log, width=15).pack(anchor=tk.E, pady=5)

    def create_webserver_tab(self):
        """Create web server tab"""
        frame = ttk.LabelFrame(self.webserver_tab, text=t('webserver_settings'), padding=15)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0
        ttk.Label(frame, text=t('port')).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value='5000')
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text=t('port_default')).grid(row=row, column=2, sticky=tk.W, padx=10)

        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)

        row += 1
        control_frame = ttk.Frame(frame)
        control_frame.grid(row=row, column=0, columnspan=3, pady=10)

        self.start_server_button = ttk.Button(control_frame, text=t('btn_start_server'),
                                             command=self.start_webserver, width=20)
        self.start_server_button.pack(side=tk.LEFT, padx=5)

        self.stop_server_button = ttk.Button(control_frame, text=t('btn_stop_server'),
                                            command=self.stop_webserver,
                                            width=20, state=tk.DISABLED)
        self.stop_server_button.pack(side=tk.LEFT, padx=5)

        self.open_browser_button = ttk.Button(control_frame, text=t('btn_open_browser'),
                                             command=self.open_webui,
                                             width=20, state=tk.DISABLED)
        self.open_browser_button.pack(side=tk.LEFT, padx=5)

        row += 1
        self.server_status_label = ttk.Label(frame, text=t('server_stopped'),
                                            foreground="red", font=("Arial", 12, "bold"))
        self.server_status_label.grid(row=row, column=0, columnspan=3, pady=10)

        row += 1
        self.server_url_label = ttk.Label(frame, text="", font=("Arial", 10), justify=tk.LEFT)
        self.server_url_label.grid(row=row, column=0, columnspan=3, pady=5, sticky=tk.W)

        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)

        row += 1
        info_label = ttk.Label(frame, text=t('webui_info'), justify=tk.LEFT, foreground="gray")
        info_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=10)

        row += 1
        ttk.Label(frame, text=t('system_log')).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=10)

        row += 1
        self.server_log_text = scrolledtext.ScrolledText(frame, height=12, width=80, state=tk.DISABLED)
        self.server_log_text.grid(row=row, column=0, columnspan=3, sticky=tk.NSEW, pady=5)

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(row, weight=1)

    def create_settings_tab(self):
        """Create settings tab"""
        frame = ttk.LabelFrame(self.settings_tab, text=t('directory_settings'), padding=15)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Language setting
        row = 0
        ttk.Label(frame, text=t('language_label')).grid(row=row, column=0, sticky=tk.W, pady=10)
        self.language_var = tk.StringVar(value=LANGUAGE_NAMES.get(current_lang, 'English'))
        language_combo = ttk.Combobox(frame, textvariable=self.language_var, width=20, state='readonly')
        language_combo['values'] = list(LANGUAGE_OPTIONS.keys())
        language_combo.grid(row=row, column=1, sticky=tk.W, pady=10)

        row += 1
        ttk.Label(frame, text=t('language_restart_note'),
                  font=("Arial", 8), foreground="gray").grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)

        # Recording directory
        row += 1
        ttk.Label(frame, text=t('recording_dir')).grid(row=row, column=0, sticky=tk.W, pady=10)
        self.recording_dir_var = tk.StringVar(value=self.config.get('DEFAULT', 'recording_dir'))
        ttk.Entry(frame, textvariable=self.recording_dir_var, width=50).grid(row=row, column=1, sticky=tk.EW, pady=10)
        ttk.Button(frame, text=t('btn_browse'), command=self.browse_recording_dir, width=10).grid(row=row, column=2, padx=5)

        row += 1
        ttk.Label(frame, text=t('recording_dir_note'),
                  font=("Arial", 8), foreground="gray").grid(row=row, column=1, sticky=tk.W)

        # Merged output directory
        row += 1
        ttk.Label(frame, text=t('merged_output_dir')).grid(row=row, column=0, sticky=tk.W, pady=10)
        default_output_var = tk.StringVar(value=self.config.get('DEFAULT', 'output_dir'))
        ttk.Entry(frame, textvariable=default_output_var, width=50).grid(row=row, column=1, sticky=tk.EW, pady=10)
        ttk.Button(frame, text=t('btn_browse'),
                  command=lambda: self.browse_directory(default_output_var, t('merged_output_dir')),
                  width=10).grid(row=row, column=2, padx=5)

        row += 1
        ttk.Label(frame, text=t('merged_output_note'),
                  font=("Arial", 8), foreground="gray").grid(row=row, column=1, sticky=tk.W)

        # Retention settings
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)

        row += 1
        ttk.Label(frame, text=t('retention_settings'), font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))

        row += 1
        ttk.Label(frame, text=t('recording_retention')).grid(row=row, column=0, sticky=tk.W, pady=5)

        retention_rec_frame = ttk.Frame(frame)
        retention_rec_frame.grid(row=row, column=1, sticky=tk.W, pady=5)

        self.recording_retention_var = tk.StringVar(value=self.config.get('DEFAULT', 'recording_retention_days', fallback='90'))
        ttk.Entry(retention_rec_frame, textvariable=self.recording_retention_var, width=10).pack(side=tk.LEFT)
        ttk.Label(retention_rec_frame, text=t('unit_days')).pack(side=tk.LEFT, padx=5)

        row += 1
        ttk.Label(frame, text=t('recording_retention_note'),
                  font=("Arial", 8), foreground="gray", justify=tk.LEFT).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(frame, text=t('merged_retention')).grid(row=row, column=0, sticky=tk.W, pady=5)

        retention_merged_frame = ttk.Frame(frame)
        retention_merged_frame.grid(row=row, column=1, sticky=tk.W, pady=5)

        self.merged_retention_var = tk.StringVar(value=self.config.get('DEFAULT', 'merged_retention_hours', fallback='2'))
        ttk.Entry(retention_merged_frame, textvariable=self.merged_retention_var, width=10).pack(side=tk.LEFT)
        ttk.Label(retention_merged_frame, text=t('unit_hours')).pack(side=tk.LEFT, padx=5)

        row += 1
        ttk.Label(frame, text=t('merged_retention_note'),
                  font=("Arial", 8), foreground="gray").grid(row=row, column=1, sticky=tk.W)

        # Create directories button
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)

        row += 1
        ttk.Button(frame, text=t('btn_create_dirs'),
                  command=self.create_directories, width=25).grid(row=row, column=1, sticky=tk.W, pady=10)

        # Save button
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)

        row += 1
        save_frame = ttk.Frame(frame)
        save_frame.grid(row=row, column=0, columnspan=3, pady=10)

        ttk.Button(save_frame, text=t('btn_save_settings'),
                  command=lambda: self.save_all_config(default_output_var),
                  width=20).pack(side=tk.LEFT, padx=5)

        ttk.Button(save_frame, text=t('btn_reset_default'),
                  command=lambda: self.reset_to_default(default_output_var),
                  width=20).pack(side=tk.LEFT, padx=5)

        # App info
        row += 1
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=15)

        row += 1
        info_frame = ttk.Frame(frame)
        info_frame.grid(row=row, column=0, columnspan=3, pady=10)

        ttk.Label(info_frame, text=t('app_info'), justify=tk.CENTER, foreground="gray").pack()

        frame.columnconfigure(1, weight=1)

    def create_status_bar(self):
        """Create status bar"""
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(status_frame, text=t('status_ready'), anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)

    # Event handlers - Recording
    def refresh_devices(self):
        """Refresh audio device list"""
        devices = self.get_audio_devices()

        device_names = [name for name, idx in devices]
        self.device_combo['values'] = device_names

        self.device_indices = {name: idx for name, idx in devices}

        saved_device = self.config.get('DEFAULT', 'audio_device', fallback='')

        if saved_device and saved_device in device_names:
            self.device_var.set(saved_device)
        elif device_names:
            self.device_var.set(device_names[0])

        if SOUNDDEVICE_AVAILABLE:
            self.log_merge(t('log_devices_updated', count=len(devices)))
        else:
            messagebox.showwarning(t('dlg_warning'), t('msg_sounddevice_not_installed'))

    def get_selected_device_index(self):
        """Get index of currently selected device"""
        device_name = self.device_var.get()
        return self.device_indices.get(device_name, -1)

    def toggle_monitor(self):
        """Toggle monitoring on/off"""
        if not SOUNDDEVICE_AVAILABLE:
            messagebox.showerror(t('dlg_error'), t('msg_sounddevice_missing'))
            return

        if self.monitoring:
            self.stop_monitor()
        else:
            self.start_monitor()

    def start_monitor(self):
        """Start monitoring"""
        try:
            device_idx = self.get_selected_device_index()
            if device_idx < 0:
                messagebox.showerror(t('dlg_error'), t('msg_select_valid_device'))
                return

            sample_rate = int(self.sample_rate_var.get())
            channels = int(self.channels_var.get())

            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Monitor status: {status}")

                if channels == 1:
                    rms = np.sqrt(np.mean(indata**2))
                    db = 20 * np.log10(rms) if rms > 0 else -100
                    self.update_meter(db, db)
                else:
                    rms_l = np.sqrt(np.mean(indata[:, 0]**2))
                    rms_r = np.sqrt(np.mean(indata[:, 1]**2))
                    db_l = 20 * np.log10(rms_l) if rms_l > 0 else -100
                    db_r = 20 * np.log10(rms_r) if rms_r > 0 else -100
                    self.update_meter(db_l, db_r)

            self.monitor_stream = sd.InputStream(
                device=device_idx,
                channels=channels,
                samplerate=sample_rate,
                callback=audio_callback,
                blocksize=1024
            )
            self.monitor_stream.start()
            self.monitoring = True

            self.monitor_button.config(text=t('btn_monitor_stop'))
            self.rec_button.config(state=tk.NORMAL)
            self.status_label.config(text=t('status_monitoring'))

            logger.info(f"Monitor started: device={device_idx}, {sample_rate}Hz, {channels}ch")

        except Exception as e:
            messagebox.showerror(t('dlg_error'), t('msg_monitor_error', error=e))
            logger.error(f"Monitor error: {e}")

    def stop_monitor(self):
        """Stop monitoring"""
        if self.monitor_stream:
            self.monitor_stream.stop()
            self.monitor_stream.close()
            self.monitor_stream = None

        self.monitoring = False

        self.meter_l_canvas.delete("all")
        self.meter_r_canvas.delete("all")
        self.meter_l_label.config(text="-\u221e dB")
        self.meter_r_label.config(text="-\u221e dB")

        self.monitor_button.config(text=t('btn_monitor_start'))
        self.status_label.config(text=t('status_ready'))

        logger.info("Monitor stopped")

    def update_meter(self, db_l, db_r):
        """Update level meter"""
        def update():
            def db_to_percent(db):
                if db < -60:
                    return 0
                elif db > 0:
                    return 100
                else:
                    return (db + 60) / 60 * 100

            self.draw_meter(self.meter_l_canvas, db_to_percent(db_l))
            self.meter_l_label.config(text=f"{db_l:.1f} dB" if db_l > -60 else "-\u221e dB")

            self.draw_meter(self.meter_r_canvas, db_to_percent(db_r))
            self.meter_r_label.config(text=f"{db_r:.1f} dB" if db_r > -60 else "-\u221e dB")

        self.root.after(0, update)

    def draw_meter(self, canvas, percent):
        """Draw meter on canvas"""
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1:
            width = 500

        green_end = int(width * 66.7 / 100)
        yellow_end = int(width * 90 / 100)

        canvas.create_rectangle(0, 0, green_end, height, fill='#00ff00', outline="")
        canvas.create_rectangle(green_end, 0, yellow_end, height, fill='#ffff00', outline="")
        canvas.create_rectangle(yellow_end, 0, width, height, fill='#ff0000', outline="")

        bar_width = int(width * percent / 100)
        if bar_width < width:
            canvas.create_rectangle(bar_width, 0, width, height, fill='#2b2b2b', outline="")

    def start_recording(self):
        """Start recording"""
        if not SOUNDDEVICE_AVAILABLE:
            messagebox.showerror(t('dlg_error'), t('msg_sounddevice_not_installed'))
            return

        if self.monitoring:
            self.stop_monitor()

        device_idx = self.get_selected_device_index()
        if device_idx == -1:
            messagebox.showerror(t('dlg_error'), t('msg_no_valid_device'))
            return

        recording_dir = self.config.get('DEFAULT', 'recording_dir')
        if not os.path.exists(recording_dir):
            try:
                Path(recording_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror(t('dlg_error'), t('msg_rec_dir_create_failed', error=e))
                return

        self.recording = True
        self.rec_start_time = datetime.now()

        self.rec_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.monitor_button.config(state=tk.DISABLED)
        self.status_label.config(text=t('status_recording'))

        self.recording_thread = threading.Thread(target=self.recording_worker, daemon=True)
        self.recording_thread.start()

        self.update_recording_time()

        logger.info(f"Recording started: device={device_idx}, dir={recording_dir}")

    def recording_worker(self):
        """Recording worker thread (timestamp-based + double buffer)"""
        try:
            device_idx = self.get_selected_device_index()
            sample_rate = int(self.sample_rate_var.get())
            channels = int(self.channels_var.get())
            bit_depth = int(self.bit_depth_var.get())
            recording_dir = self.config.get('DEFAULT', 'recording_dir')

            if bit_depth == 16:
                dtype = 'int16'
                sampwidth = 2
            elif bit_depth == 24:
                dtype = 'int32'
                sampwidth = 3
            else:
                dtype = 'int32'
                sampwidth = 4

            buffer_a = []
            buffer_b = []
            current_buffer = buffer_b
            buffer_lock = threading.Lock()

            current_file = None
            current_wav = None
            current_file_start_sample = 0
            total_samples = 0

            recording_start_time = datetime.now()

            next_boundary = recording_start_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
            next_boundary_sample = int((next_boundary - recording_start_time).total_seconds() * sample_rate)

            def audio_callback(indata, frames, time_info, status):
                nonlocal current_buffer, total_samples

                if status:
                    logger.warning(f"Recording status: {status}")

                with buffer_lock:
                    current_buffer.append((indata.copy(), total_samples))
                    total_samples += frames

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

            logger.info(f"Recording started: next_boundary={next_boundary.strftime('%H:%M:%S')}, sample_pos={next_boundary_sample}")

            while self.recording:
                with buffer_lock:
                    if current_buffer is buffer_b:
                        buffer_a, buffer_b = buffer_b, buffer_a
                        current_buffer = buffer_b
                    else:
                        buffer_b, buffer_a = buffer_a, buffer_b
                        current_buffer = buffer_a

                if buffer_a:
                    for audio_data, sample_position in buffer_a:
                        if current_wav is None or sample_position >= next_boundary_sample:
                            if current_wav:
                                current_wav.close()
                                logger.info(f"File closed: {current_file}")

                            filename = f"rec_{next_boundary.strftime('%Y%m%d-%H%M%S')}.wav"
                            current_file = os.path.join(recording_dir, filename)

                            current_wav = wave.open(current_file, 'wb')
                            current_wav.setnchannels(channels)
                            current_wav.setsampwidth(sampwidth)
                            current_wav.setframerate(sample_rate)

                            current_file_start_sample = next_boundary_sample

                            next_boundary += timedelta(minutes=1)
                            next_boundary_sample += sample_rate * 60

                            self.root.after(0, lambda f=filename: self.rec_file_label.config(
                                text=t('recording_file', filename=f)))

                            logger.info(f"New file created: {current_file}, next_boundary={next_boundary.strftime('%H:%M:%S')}")

                        if bit_depth == 24:
                            audio_data_converted = (audio_data >> 8).astype(np.int32)
                            current_wav.writeframes(audio_data_converted.tobytes())
                        else:
                            current_wav.writeframes(audio_data.tobytes())

                        if dtype == 'int16':
                            audio_normalized = audio_data.astype(np.float32) / 32768.0
                        else:
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

                    buffer_a.clear()

                threading.Event().wait(0.1)

            stream.stop()
            stream.close()

            with buffer_lock:
                remaining_buffer = buffer_a + buffer_b

            for audio_data, sample_position in remaining_buffer:
                if current_wav:
                    if bit_depth == 24:
                        audio_data_converted = (audio_data >> 8).astype(np.int32)
                        current_wav.writeframes(audio_data_converted.tobytes())
                    else:
                        current_wav.writeframes(audio_data.tobytes())

            if current_wav:
                current_wav.close()
                logger.info(f"Final file closed: {current_file}")

        except Exception as e:
            logger.error(f"Recording error: {e}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror(
                t('dlg_recording_error'), t('msg_recording_error', error=e)))
            self.root.after(0, self.stop_recording)

    def update_recording_time(self):
        """Update recording time display"""
        if self.recording:
            elapsed = datetime.now() - self.rec_start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)

            self.rec_time_label.config(text=t('rec_time', time=f"{hours:02d}:{minutes:02d}:{seconds:02d}"))

            self.root.after(1000, self.update_recording_time)

    def stop_recording(self):
        """Stop recording"""
        if not self.recording:
            return

        self.recording = False

        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)

        if self.recording_stream:
            try:
                self.recording_stream.stop()
                self.recording_stream.close()
            except:
                pass
            self.recording_stream = None

        self.meter_l_canvas.delete("all")
        self.meter_r_canvas.delete("all")
        self.meter_l_label.config(text="-\u221e dB")
        self.meter_r_label.config(text="-\u221e dB")

        self.rec_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.monitor_button.config(state=tk.NORMAL)
        self.rec_time_label.config(text=t('rec_time', time='00:00:00'))
        self.rec_file_label.config(text="")
        self.status_label.config(text=t('status_ready'))

        logger.info("Recording stopped")

    # Event handlers - Archive
    def set_start_now(self):
        """Set start time to now"""
        now = datetime.now()
        self.start_date_var.set(now.strftime('%Y-%m-%d'))
        self.start_hour_var.set(now.strftime('%H'))
        self.start_min_var.set(now.strftime('%M'))
        self.start_sec_var.set(now.strftime('%S'))

    def set_end_now(self):
        """Set end time to now"""
        now = datetime.now()
        self.end_date_var.set(now.strftime('%Y-%m-%d'))
        self.end_hour_var.set(now.strftime('%H'))
        self.end_min_var.set(now.strftime('%M'))
        self.end_sec_var.set(now.strftime('%S'))

    def browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title=t('output_dir'),
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)

    def open_output_dir(self):
        """Open output directory"""
        output_dir = self.output_dir_var.get()
        if os.path.exists(output_dir):
            if sys.platform == 'win32':
                os.startfile(output_dir)
            elif sys.platform == 'darwin':
                os.system(f'open "{output_dir}"')
            else:
                os.system(f'xdg-open "{output_dir}"')
        else:
            messagebox.showwarning(t('dlg_warning'), t('msg_dir_not_found', path=output_dir))

    def start_merge(self):
        """Start merge process"""
        try:
            start_date_str = f"{self.start_date_var.get()} {self.start_hour_var.get()}:{self.start_min_var.get()}:{self.start_sec_var.get()}"
            end_date_str = f"{self.end_date_var.get()} {self.end_hour_var.get()}:{self.end_min_var.get()}:{self.end_sec_var.get()}"

            start_time = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')

            if start_time >= end_time:
                messagebox.showerror(t('dlg_error'), t('msg_start_before_end'))
                return

            output_dir = self.output_dir_var.get()
            recording_dir = self.config.get('DEFAULT', 'recording_dir')

            if not os.path.exists(recording_dir):
                messagebox.showerror(t('dlg_error'), t('msg_rec_dir_not_found', path=recording_dir))
                return

            Path(output_dir).mkdir(parents=True, exist_ok=True)

            self.merge_button.config(state=tk.DISABLED)
            self.status_label.config(text=t('status_merging'))

            thread = threading.Thread(target=self.merge_files_thread,
                                    args=(start_time, end_time, recording_dir, output_dir),
                                    daemon=True)
            thread.start()

        except ValueError as e:
            messagebox.showerror(t('dlg_error'), t('msg_time_format_error', error=e))
        except Exception as e:
            messagebox.showerror(t('dlg_error'), t('msg_unexpected_error', error=e))
            self.merge_button.config(state=tk.NORMAL)

    def merge_files_thread(self, start_time, end_time, recording_dir, output_dir):
        """Merge process thread"""
        try:
            self.log_merge(t('log_merge_start'))
            self.log_merge(t('log_start_time', time=start_time.strftime('%Y-%m-%d %H:%M:%S')))
            self.log_merge(t('log_end_time', time=end_time.strftime('%Y-%m-%d %H:%M:%S')))
            self.log_merge(t('log_recording_dir', dir=recording_dir))
            self.log_merge(t('log_output_dir', dir=output_dir))

            wav_files = self.get_wav_files_in_timerange(start_time, end_time, recording_dir)

            if not wav_files:
                self.log_merge(t('log_no_wav'))
                messagebox.showwarning(t('dlg_warning'), t('msg_no_wav_in_range'))
                return

            self.log_merge(t('log_file_count', count=len(wav_files)))
            for f in wav_files:
                self.log_merge(f"  - {os.path.basename(f)}")

            start_str = start_time.strftime('%Y%m%d-%H%M%S')
            end_str = end_time.strftime('%Y%m%d-%H%M%S')
            output_filename = f"merged_{start_str}_{end_str}.wav"
            output_path = os.path.join(output_dir, output_filename)

            self.log_merge(t('log_output_file', filename=output_filename))

            self.merge_wav_files(wav_files, output_path)

            self.log_merge(t('log_merge_complete'))
            self.log_merge("")

            messagebox.showinfo(t('dlg_complete'), t('msg_merge_complete', filename=output_filename))

        except Exception as e:
            self.log_merge(f"ERROR: {e}")
            messagebox.showerror(t('dlg_error'), t('msg_merge_error', error=e))

        finally:
            self.root.after(0, lambda: self.merge_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_label.config(text=t('status_ready')))

    def get_wav_files_in_timerange(self, start_time, end_time, recording_dir):
        """Get WAV files within specified time range"""
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
                logger.warning(f"Error processing file {file}: {e}")
                continue

        files_with_timestamps.sort(key=lambda x: x[1])
        return [filepath for filepath, _ in files_with_timestamps]

    def get_wav_file_timestamp(self, filepath):
        """Get timestamp from WAV file"""
        try:
            filename = os.path.basename(filepath)
            if filename.startswith('rec_') and filename.endswith('.wav'):
                time_str = filename[4:19]
                return datetime.strptime(time_str, '%Y%m%d-%H%M%S')
        except (ValueError, IndexError):
            pass

        stat = os.stat(filepath)
        return datetime.fromtimestamp(stat.st_mtime)

    def merge_wav_files(self, input_files, output_file):
        """Merge WAV files using pure Python wave module"""
        if not input_files:
            raise ValueError(t('msg_no_files_specified'))

        self.log_merge(t('log_merging_files', count=len(input_files)))

        with wave.open(input_files[0], 'rb') as first_wav:
            params = first_wav.getparams()
            nchannels = params.nchannels
            sampwidth = params.sampwidth
            framerate = params.framerate

            self.log_merge(t('log_wav_format', ch=nchannels, bits=sampwidth*8, rate=framerate))

        with wave.open(output_file, 'wb') as output_wav:
            output_wav.setparams(params)

            for i, file_path in enumerate(input_files, 1):
                try:
                    with wave.open(file_path, 'rb') as input_wav:
                        if (input_wav.getnchannels() != nchannels or
                            input_wav.getsampwidth() != sampwidth or
                            input_wav.getframerate() != framerate):
                            self.log_merge(t('log_format_mismatch', filename=os.path.basename(file_path)))
                            continue

                        frames = input_wav.readframes(input_wav.getnframes())
                        output_wav.writeframes(frames)

                        self.log_merge(t('log_file_merged', i=i, total=len(input_files), filename=os.path.basename(file_path)))

                except Exception as e:
                    self.log_merge(t('log_file_merge_error', filepath=file_path, error=e))
                    continue

        self.log_merge(t('log_merged_output', filepath=output_file))

    def log_merge(self, message):
        """Add merge log entry"""
        def update():
            self.merge_log_text.config(state=tk.NORMAL)
            self.merge_log_text.insert(tk.END, f"{message}\n")
            self.merge_log_text.see(tk.END)
            self.merge_log_text.config(state=tk.DISABLED)

        self.root.after(0, update)

    def clear_merge_log(self):
        """Clear merge log"""
        self.merge_log_text.config(state=tk.NORMAL)
        self.merge_log_text.delete(1.0, tk.END)
        self.merge_log_text.config(state=tk.DISABLED)

    # Event handlers - Settings
    def browse_recording_dir(self):
        """Browse for recording directory"""
        directory = filedialog.askdirectory(
            title=t('recording_dir'),
            initialdir=self.recording_dir_var.get()
        )
        if directory:
            self.recording_dir_var.set(directory)

    def browse_directory(self, var, title):
        """Generic directory browser"""
        directory = filedialog.askdirectory(
            title=title,
            initialdir=var.get()
        )
        if directory:
            var.set(directory)

    def create_directories(self):
        """Create directories"""
        try:
            Path(self.recording_dir_var.get()).mkdir(parents=True, exist_ok=True)
            Path(self.config.get('DEFAULT', 'output_dir')).mkdir(parents=True, exist_ok=True)
            messagebox.showinfo(t('dlg_success'), t('msg_dirs_created'))
        except Exception as e:
            messagebox.showerror(t('dlg_error'), t('msg_dirs_create_failed', error=e))

    def save_all_config(self, default_output_var):
        """Save all settings"""
        self.config['DEFAULT']['recording_dir'] = self.recording_dir_var.get()
        self.config['DEFAULT']['output_dir'] = default_output_var.get()
        self.config['DEFAULT']['audio_device'] = self.device_var.get()
        self.config['DEFAULT']['sample_rate'] = self.sample_rate_var.get()
        self.config['DEFAULT']['channels'] = self.channels_var.get()
        self.config['DEFAULT']['bit_depth'] = self.bit_depth_var.get()
        self.config['DEFAULT']['recording_retention_days'] = self.recording_retention_var.get()
        self.config['DEFAULT']['merged_retention_hours'] = self.merged_retention_var.get()
        self.config['DEFAULT']['language'] = LANGUAGE_OPTIONS.get(self.language_var.get(), 'en')

        self.output_dir_var.set(default_output_var.get())

        self.save_config()

    def reset_to_default(self, default_output_var):
        """Reset to default settings"""
        if messagebox.askyesno(t('dlg_confirm'), t('msg_confirm_reset')):
            for key, value in self.default_config.items():
                self.config['DEFAULT'][key] = value

            self.recording_dir_var.set(self.config.get('DEFAULT', 'recording_dir'))
            default_output_var.set(self.config.get('DEFAULT', 'output_dir'))
            self.output_dir_var.set(self.config.get('DEFAULT', 'output_dir'))
            self.device_var.set(self.config.get('DEFAULT', 'audio_device'))
            self.sample_rate_var.set(self.config.get('DEFAULT', 'sample_rate'))
            self.channels_var.set(self.config.get('DEFAULT', 'channels'))
            self.bit_depth_var.set(self.config.get('DEFAULT', 'bit_depth'))
            self.recording_retention_var.set(self.config.get('DEFAULT', 'recording_retention_days'))
            self.merged_retention_var.set(self.config.get('DEFAULT', 'merged_retention_hours'))
            self.language_var.set(LANGUAGE_NAMES.get(self.config.get('DEFAULT', 'language'), 'English'))

            self.save_config()

    # Event handlers - Web server
    def auto_start_webserver(self):
        """Auto-start web server on app launch"""
        try:
            self.start_webserver()
            self.status_label.config(text=t('status_startup_complete'))
        except Exception as e:
            logger.error(f"Web server auto-start error: {e}")
            messagebox.showwarning(t('dlg_warning'), t('msg_webserver_autostart_failed', error=e))

    def start_webserver(self):
        """Start web server"""
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror(t('dlg_error'), t('msg_port_not_number'))
            return

        def run_server():
            try:
                logger.info(f"Starting web server... (port: {port})")
                flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
            except Exception as e:
                logger.error(f"Web server error: {e}")
                self.server_running = False

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.server_running = True

        self.start_server_button.config(state=tk.DISABLED)
        self.stop_server_button.config(state=tk.NORMAL)
        self.open_browser_button.config(state=tk.NORMAL)
        self.server_status_label.config(text=t('server_running'), foreground="green")

        ip_addresses = self.get_local_ip_addresses()

        if ip_addresses:
            url_text = t('access_url') + "\n"
            for ip in ip_addresses:
                url_text += f"  http://{ip}:{port}\n"
            url_text += f"  http://localhost:{port} {t('local_only')}"
        else:
            url_text = t('access_url') + f"\n  http://localhost:{port}"

        self.server_url_label.config(text=url_text)

        status_text = t('status_webserver_running')
        if ip_addresses:
            status_text += f": {ip_addresses[0]}:{port}"
        self.status_label.config(text=status_text)

        logger.info(f"Web server started (port: {port})")
        if ip_addresses:
            logger.info("Accessible URLs:")
            for ip in ip_addresses:
                logger.info(f"  http://{ip}:{port}")
        logger.info(f"  http://localhost:{port} (local only)")

    def stop_webserver(self):
        """Stop web server (notice only)"""
        messagebox.showwarning(t('dlg_notice'), t('msg_server_stop_notice'))

    def open_webui(self):
        """Open Web UI in browser"""
        try:
            port = int(self.port_var.get())
            url = f"http://localhost:{port}"
            webbrowser.open(url)
            logger.info(f"Opened browser: {url}")
        except Exception as e:
            messagebox.showerror(t('dlg_error'), t('msg_browser_open_failed', error=e))

    def cleanup_old_files(self):
        """Delete old files (periodic) - recording files and merged files"""
        try:
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
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        age_days = (now - file_mtime).total_seconds() / 86400

                        if age_days > recording_retention_days:
                            os.remove(filepath)
                            deleted_rec_count += 1
                            logger.info(f"Deleted old recording file: {filename} (age: {age_days:.1f} days)")

                    except Exception as e:
                        logger.warning(f"File deletion error: {filename} - {e}")

                if deleted_rec_count > 0:
                    logger.info(f"Recording cleanup complete: {deleted_rec_count} files deleted")

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
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        age_hours = (now - file_mtime).total_seconds() / 3600

                        if age_hours > merged_retention_hours:
                            os.remove(filepath)
                            deleted_merged_count += 1
                            logger.info(f"Deleted old merged file: {filename} (age: {age_hours:.1f} hours)")

                    except Exception as e:
                        logger.warning(f"File deletion error: {filename} - {e}")

                if deleted_merged_count > 0:
                    logger.info(f"Merged file cleanup complete: {deleted_merged_count} files deleted")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

        finally:
            self.root.after(600000, self.cleanup_old_files)

    def on_closing(self):
        """Window close handler"""
        if self.monitoring:
            self.stop_monitor()

        if self.recording:
            if messagebox.askyesno(t('dlg_confirm'), t('msg_confirm_quit_recording')):
                self.root.destroy()
        elif self.server_running:
            if messagebox.askyesno(t('dlg_confirm'), t('msg_confirm_quit_server')):
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = RadioArchiverGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
