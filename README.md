# RadioArchiver

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/stcatcom/RadioArchiver)
[![PayPal](https://img.shields.io/badge/PayPal-Donate-blue.svg)](https://paypal.me/stcatcom?locale.x=ja_JP&country.x=JP)

[日本語版 README はこちら](README_JP.md)

Integrated Recording & Archive System for Broadcast Stations

## Overview

RadioArchiver is an integrated application for managing simultaneous recording and audio archiving for radio broadcast stations and internet radio.

### Key Features

- 🎙️ **Continuous Recording**: Auto-split every 1 minute, aligned to the :00 second mark
- 📼 **Archive Merge**: Merge WAV files within a specified time range
- 🌐 **Web UI**: Operable from smartphones and tablets
- 🗑️ **Auto Cleanup**: Automatically delete old files (configurable)
- 📊 **Level Meter**: Real-time audio level monitoring
- 🌍 **Multilingual**: English and Japanese support

## System Requirements

### Supported OS
- Windows 10/11
- Linux (Ubuntu 20.04 or later recommended)
- macOS (10.14 or later)

### Required Software
- Python 3.8 or later
- Audio device (for recording)

### Storage
- **90-day recording (default settings)**: Approx. 1.3TB
- **Recommended**: 2TB or larger HDD/SSD
- See [STORAGE_REQUIREMENTS.md](STORAGE_REQUIREMENTS.md) for details

## Installation

### 1. Install Python

#### Windows
Download and install from the [Python official site](https://www.python.org/downloads/)

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install Flask sounddevice numpy
```

## Usage

### Launch

```bash
python RadioArchiver.py
```

### Initial Setup

1. Open the **⚙️ Settings** tab
2. Set the **Language** (English / Japanese)
3. Set the **Recording Directory** and **Merged File Output** directory
4. Click **📁 Create Directories**
5. Click **💾 Save Settings**

### Recording

1. Open the **📻 Recording** tab
2. Select a **Recording Device** (click 🔄 Refresh to update the list)
3. Set **Sample Rate**, **Channels**, and **Bit Depth**
4. Click **🎧 Start Monitor** to check audio levels
5. Click **⏺ Start Recording** to begin

### File Merge

#### From GUI
1. Open the **📼 Archive Merge** tab
2. Enter start and end times
3. Click **🔄 Start Merge**

#### From Web UI
1. Open the **🌐 Web UI** tab
2. Open the displayed URL in a browser (auto-started)
3. Enter the time range and click **🔄 Start Merge**

## File Formats

### Recording Files
- Format: `rec_YYYYMMDD-HHMMSS.wav`
- Example: `rec_20250105-143000.wav` (Jan 5, 2025, 14:30:00)
- Split: Every 1 minute (aligned to :00 seconds)

### Merged Files
- Format: `merged_starttime_endtime.wav`
- Example: `merged_20250105-140000_20250105-150000.wav`

## Configuration

### config.ini

Automatically generated in the same directory as the application.

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
language = en
```

### File Retention Periods

#### Recording Files (rec_*.wav)
- **Default**: 90 days
- **Purpose**: Compliance with broadcasting regulations (terrestrial broadcasters are required to retain recordings for 3 months in Japan)
- **Internet radio**: Freely configurable (7 days, 30 days, etc.)

#### Merged Files (merged_*.wav)
- **Default**: 2 hours
- **Purpose**: Short retention since files are typically downloaded immediately

## Troubleshooting

### Cannot install sounddevice

**Windows**:
```bash
pip install sounddevice --user
```

**Linux**:
```bash
sudo apt install portaudio19-dev
pip install sounddevice
```

### Recording devices not showing

1. Verify that the audio device is properly connected
2. Click the **🔄 Refresh** button
3. Ensure no other application is using the device

### Cannot access Web UI

1. Check that port 5000 is allowed through the firewall
2. Try a different port number (change in the Settings tab)

## Storage Management

### Capacity Estimates

| Retention Period | Required Space (Stereo 16bit 44.1kHz) |
|---------|----------------------------------|
| 7 days | ~100GB |
| 30 days | ~426GB |
| 90 days | ~1.3TB |

### Tips for Reducing Storage

1. **Mono recording**: Reduces storage by ~50%
2. **Shorter retention**: Consider 7-30 days for internet radio
3. **Auto cleanup**: Adjust retention in the Settings tab

See [STORAGE_REQUIREMENTS.md](STORAGE_REQUIREMENTS.md) for details.

## Technical Specifications

### Recording
- **Double buffering**: Zero audio dropout
- **Timestamp-based**: Sample-accurate splitting
- **Supported formats**:
  - Sample rate: 44.1kHz / 48kHz / 96kHz
  - Channels: Mono / Stereo
  - Bit depth: 16bit / 24bit / 32bit

### Merging
- **±1 minute margin**: Ensures no audio is missed at time boundaries
- **Pure Python implementation**: No FFmpeg required
- **Format validation**: Skips files with mismatched formats

## License

MIT License

Copyright (c) 2026 Masaya Miyazaki / Office Stray Cat

See the [LICENSE](LICENSE) file for details.

**Note**: Please do not remove the copyright notice when modifying or creating derivative works.

## Author

- **Masaya Miyazaki** / Office Stray Cat
- Website: https://stcat.com/
- Email: info@stcat.com
- GitHub: [@stcatcom](https://github.com/stcatcom)

## Support

If you encounter any issues, check the log output:
- Console output
- Python stderr

For bug reports and feature requests, please visit [GitHub Issues](https://github.com/stcatcom/RadioArchiver/issues).

If you find this project helpful, consider supporting development:

[![PayPal](https://img.shields.io/badge/PayPal-Donate-blue.svg)](https://paypal.me/stcatcom?locale.x=ja_JP&country.x=JP)

## Changelog

### Version 0.2.0 (2026-02-15)
- Added English language support
- Added language switching in Settings tab (English / Japanese)
- Default language changed to English
- Web UI now supports both English and Japanese
- Updated README to English, added README_JP.md for Japanese

### Version 0.1.1 (2026-01-09)
- Fixed leftover test environment settings in the code

### Version 0.1.0 (2026-01-06)
- Initial release
- Integrated recording, merging, Web UI, and auto-cleanup features
