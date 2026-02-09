# Bedtime Streamer

A self-contained, cross-platform media streaming server that transcodes your local movies and TV shows to HLS/CMAF format for playback on any device with a web browser.

## Features

- **Web-based interface** - Browse and stream from any device on your network
- **Real-time transcoding** - FFmpeg-powered on-the-fly encoding with multiple quality presets
- **Subtitle support** - Internal and external SRT/ASS subtitle burning
- **Cross-platform** - Works on Windows, macOS, and Linux
- **No external dependencies** - Single Python application with embedded web server
- **GPU acceleration** - Optional NVENC support for NVIDIA GPUs
- **CMAF streaming** - Modern fMP4-based streaming for better compatibility

## Requirements

- Python 3.8 or higher
- FFmpeg 4.0+ (auto-installed by setup script on Linux/macOS)

## Quick Start

### 1. Clone or download the repository

```bash
git clone https://github.com/Atlas2p0/my-bed-time-streamer.git
cd bedtime-streamer
```

### 2. Run the setup script

```bash
python setup.py
```

The setup script will:
- Check/install FFmpeg (Linux/macOS automatic, Windows manual)
- Create a Python virtual environment
- Install Python dependencies
- Configure your media library and stream output paths
- Create a launcher script

### 3. Start the server

**Windows:**
```bash
start.bat
```

**Linux/macOS:**
```bash
./start.sh
```

Or manually:
```bash
# Windows
.venv\Scripts\activate
python app.py

# Linux/macOS
source .venv/bin/activate
python app.py
```

### 4. Open in browser
http://localhost:5000

Or use the IP address shown in the console to access from other devices on your network.

## Configuration

During setup, you'll be prompted for two paths:

| Setting | Description | Default |
|---------|-------------|---------|
| **Media Library Path** | Where your movies/TV shows are stored | `~/Videos` |
| **Stream Output Path** | Where temporary stream chunks are cached | `~/.local/share/bedtime-streamer/stream-chunks` |

You can reconfigure these anytime:
```bash
python setup.py --config-only

export LIBRARY_PATH="/path/to/media"
export HLS_DIR="/path/to/stream/cache"
python app.py
```

### Expected Directory Hierarchy
Make sure your directory is structured similarly as shown below
	
	D:/Media Library/                    <- LIBRARY_PATH
	├── Movie Folder 1/               <- Folder with videos inside
	│   ├── movie.mp4/mkv/...
	│   └── subtitle_file.srt/ass/...
	└── Movie Folder 2/
	    └── movie.mp4/mkv/...
# Usage

1. **Browse** - Search and browse your media library on the home page

2. **Select** - Click a movie/show to see available episodes

3. **Configure** - Choose subtitle track and quality preset

4. **Stream** - Click Play to open the video player in a new tab

**Quality Presets**:

| Preset	| Codec	| Use Case|
| --------|-------|---------|
| CPU_FAST	| libx264 |	Best compatibility, no GPU needed |
| GPU_NVENC	| h264_nvenc |	Fast encoding with NVIDIA GPU |
| GPU_NVENC_HIGH_QUALITY	| h264_nvENC	| Better quality with NVIDIA GPU |

Project Structure

	bedtime-streamer/
	├── app.py                  # Main application entry point
	├── config.py               # Configuration (paths, presets)
	├── setup.py                # Cross-platform setup script
	├── requirements.txt        # Python dependencies
	├── routes/                 # Flask route handlers
	│   ├── __init__.py
	│   ├── library.py          # Media library API
	│   ├── stream.py           # Start/stop streaming
	│   └── ui.py               # Web pages
	├── utils/                  # Utility modules
	│   ├── __init__.py
	│   ├── ffmpeg.py           # FFmpeg command building
	│   └── filesystem.py       # Media scanning
	├── models.py               # Global state management
	├── web/                    # Web frontend
	│   ├── templates/
	│   │   ├── index.html      # Library browser
	│   │   ├── movie.html      # Movie detail page
	│   │   └── player.html     # Video player
	│   └── static/
	│       └── js/
	│           ├── app.js      # Main application JS
	│           ├── movie.js    # Movie page JS
	│           └── player/     # Player components
	└── start.sh / start.bat    # Launcher scripts

# Troubleshooting

## FFmpeg not found (Windows)

Install manually:

1. Download from https://ffmpeg.org/download.html

2. Extract to C:\ffmpeg

3. Add C:\ffmpeg\bin to your PATH environment variable

4. Restart terminal and verify: ffmpeg -version

Or use a package manager:

	# With Chocolatey
	choco install ffmpeg
	
	# With winget
	winget install Gyan.FFmpeg

## Stream fails to start

Check the console output for FFmpeg errors. Common issues:

- Path encoding: Non-ASCII characters in media paths
- Permissions: Cannot write to stream output directory
- GPU unavailable: NVENC fails without NVIDIA GPU, falls back to CPU

Cannot access from other devices

Ensure the server is binding to all interfaces (default). Check your firewall settings and that port 5000 is open.

# Development

## Running without setup
```terminal
	pip install -r requirements.txt
	python app.py
```
# Project architecture

- **Backend**: Flask with Waitress WSGI server
- **Frontend**: Vanilla JavaScript (no build step)
- **Streaming**: HLS/CMAF via FFmpeg subprocess
- **State**: Simple in-memory (no database)

# License


MIT License - See LICENSE file for details.

# Acknowledgments

- <a href="https://ffmpeg.org/">**FFmpeg**</a> - The universal multimedia toolkit
- <a href="https://flask.palletsprojects.com/en/stable/">**Flask**</a> - Python web framework
- <a href="https://github.com/video-dev/hls.js/">**hls.js**</a> - HLS player for browsers

