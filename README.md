[README.md](https://github.com/user-attachments/files/24444393/README.md)
# RadioArchiver

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/stcatcom/RadioArchiver)

放送局向け録音・アーカイブ統合システム

## 概要

RadioArchiverは、ラジオ放送局やネットラジオの同時録音（同録）と音声アーカイブを管理するための統合アプリケーションです。

### 主な機能

- 🎙️ **連続録音**: 1分ごとに自動分割、毎分00秒で区切り
- 📼 **アーカイブ結合**: 指定時間範囲のWAVファイルを結合
- 🌐 **Web UI**: スマホ・タブレットから操作可能
- 🗑️ **自動削除**: 古いファイルを自動削除（設定可能）
- 📊 **レベルメーター**: リアルタイムの音量確認

## システム要件

### 対応OS
- Windows 10/11
- Linux (Ubuntu 20.04以降推奨)
- macOS (10.14以降)

### 必要なソフトウェア
- Python 3.8以上
- オーディオデバイス（録音用）

### ストレージ容量
- **90日間録音（標準設定）**: 約1.3TB
- **推奨**: 2TB以上のHDD/SSD
- 詳細は [STORAGE_REQUIREMENTS.md](STORAGE_REQUIREMENTS.md) を参照

## インストール

### 1. Pythonのインストール

#### Windows
[Python公式サイト](https://www.python.org/downloads/)から最新版をダウンロードしてインストール

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

または個別にインストール:
```bash
pip install Flask sounddevice numpy
```

## 使い方

### 起動

```bash
python RadioArchiver.py
```

### 初回設定

1. **⚙️ 設定タブ** を開く
2. **録音ディレクトリ** と **結合ファイル保存先** を設定
3. **📁 ディレクトリを作成** をクリック
4. **💾 設定を保存** をクリック

### 録音

1. **📻 録音タブ** を開く
2. **録音デバイス** を選択（🔄更新で一覧更新）
3. **サンプルレート・チャンネル数・ビット深度** を設定
4. **🎧 モニター開始** で音量確認
5. **⏺ 録音開始** で録音スタート

### ファイル結合

#### GUIから
1. **📼 アーカイブ結合タブ** を開く
2. 開始時刻・終了時刻を入力
3. **🔄 結合開始** をクリック

#### Web UIから
1. **🌐 Web UIタブ** を開く
2. 表示されたURLをブラウザで開く（自動起動済み）
3. 時刻を入力して **🔄 結合開始**

## ファイル形式

### 録音ファイル
- 形式: `rec_YYYYMMDD-HHMMSS.wav`
- 例: `rec_20250105-143000.wav` (2025年1月5日 14:30:00)
- 分割: 1分ごと（毎時00秒区切り）

### 結合ファイル
- 形式: `merged_開始時刻_終了時刻.wav`
- 例: `merged_20250105-140000_20250105-150000.wav`

## 設定

### config.ini

アプリケーションと同じディレクトリに自動生成されます。

```ini
[DEFAULT]
recording_dir = C:/RadioArchiver/rec
output_dir = C:/RadioArchiver/merged
audio_device = [2] Line In (USB Audio)
sample_rate = 44100
channels = 2
bit_depth = 16
recording_retention_days = 90
merged_retention_hours = 2
```

### ファイル保持期間

#### 同録ファイル（rec_*.wav）
- **デフォルト**: 90日
- **用途**: 放送法対応（地上波放送局は3ヶ月保存義務）
- **ネットラジオ**: 7日・30日など自由に設定可能

#### 結合ファイル（merged_*.wav）
- **デフォルト**: 2時間
- **用途**: ダウンロード後は不要なため短期間

## トラブルシューティング

### sounddeviceがインストールできない

**Windows**:
```bash
pip install sounddevice --user
```

**Linux**:
```bash
sudo apt install portaudio19-dev
pip install sounddevice
```

### 録音デバイスが表示されない

1. オーディオデバイスが正しく接続されているか確認
2. **🔄 更新** ボタンをクリック
3. 他のアプリがデバイスを使用していないか確認

### Web UIにアクセスできない

1. ファイアウォールでポート5000が許可されているか確認
2. 別のポート番号を試す（設定タブで変更）

## ストレージ管理

### 容量の目安

| 保持期間 | 必要容量（ステレオ 16bit 44.1kHz） |
|---------|----------------------------------|
| 7日 | 約100GB |
| 30日 | 約426GB |
| 90日 | 約1.3TB |

### 容量削減のヒント

1. **モノラル録音**: 容量を約50%削減
2. **保持期間の短縮**: ネットラジオなら7〜30日も検討
3. **自動削除機能**: 設定タブで保持期間を調整可能

詳細は [STORAGE_REQUIREMENTS.md](STORAGE_REQUIREMENTS.md) を参照してください。

## 技術仕様

### 録音
- **ダブルバッファリング**: 音の取りこぼしゼロ
- **タイムスタンプベース**: サンプル単位で正確な分割
- **対応フォーマット**:
  - サンプルレート: 44.1kHz / 48kHz / 96kHz
  - チャンネル: モノラル / ステレオ
  - ビット深度: 16bit / 24bit / 32bit

### 結合
- **±1分マージン**: 時刻のエッジ部分を漏らさない
- **純粋Python実装**: FFmpeg不要
- **フォーマット検証**: 不整合ファイルはスキップ

## ライセンス

MIT License

Copyright (c) 2026 Masaya Miyazaki / Office Stray Cat

詳細は [LICENSE](LICENSE) ファイルを参照してください。

**注意**: このソフトウェアを改変・派生する際は、著作権表示を削除しないでください。

## 作者

- **Masaya Miyazaki** / Office Stray Cat
- Website: https://stcat.com/
- Email: info@stcat.com
- GitHub: [@stcatcom](https://github.com/stcatcom)

## サポート

問題が発生した場合は、ログファイルを確認してください：
- コンソール出力
- Pythonの標準エラー出力

バグ報告や機能要望は [GitHub Issues](https://github.com/stcatcom/RadioArchiver/issues) までお願いします。

## 更新履歴

### Version 0.1.0 (2026-01-06)
- 初回リリース
- 録音・結合・Web UI・自動削除機能を統合
