#!/usr/bin/env python3
"""
Bedtime Streamer - Setup Script
Cross-platform setup for Linux, macOS, and Windows
"""

import os
import sys
import platform
import subprocess
import argparse
import json
from pathlib import Path


class Colors:
    """Terminal colors for pretty output"""
    GREEN = '\033[92m' if platform.system() != 'Windows' else ''
    YELLOW = '\033[93m' if platform.system() != 'Windows' else ''
    RED = '\033[91m' if platform.system() != 'Windows' else ''
    BLUE = '\033[94m' if platform.system() != 'Windows' else ''
    END = '\033[0m' if platform.system() != 'Windows' else ''


def print_step(msg):
    print(f"{Colors.BLUE}[*]{Colors.END} {msg}")


def print_success(msg):
    print(f"{Colors.GREEN}[+]{Colors.END} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}[!]{Colors.END} {msg}")


def print_error(msg):
    print(f"{Colors.RED}[-]{Colors.END} {msg}")


def run_command(cmd, shell=False, capture=True):
    """Run a shell command and return success status"""
    try:
        if capture:
            result = subprocess.run(
                cmd, 
                shell=shell, 
                capture_output=True, 
                text=True,
                check=False
            )
            return result.returncode == 0, result.stdout, result.stderr
        else:
            subprocess.run(cmd, shell=shell, check=True)
            return True, "", ""
    except Exception as e:
        return False, "", str(e)


def check_python_version():
    """Check if Python version is 3.8+"""
    print_step("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error("Python 3.8 or higher is required")
        sys.exit(1)
    print_success(f"Python {version.major}.{version.minor}.{version.micro} OK")


def get_platform():
    """Get current platform"""
    system = platform.system().lower()
    if system == 'darwin':
        return 'macos'
    return system


def install_ffmpeg():
    """Install FFmpeg based on platform"""
    plat = get_platform()
    print_step(f"Installing FFmpeg on {plat}...")
    
    if plat == 'linux':
        # Try different package managers
        managers = [
            (['apt-get', 'update'], ['apt-get', 'install', '-y', 'ffmpeg']),
            (['pacman', '-Sy'], ['pacman', '-S', '--noconfirm', 'ffmpeg']),
            (['dnf', 'check-update'], ['dnf', 'install', '-y', 'ffmpeg']),
            (['yum', 'check-update'], ['yum', 'install', '-y', 'ffmpeg']),
        ]
        
        for update_cmd, install_cmd in managers:
            success, _, _ = run_command(['which', install_cmd[0]])
            if success:
                print_step(f"Using {install_cmd[0]}...")
                run_command(update_cmd, capture=False)
                success, _, stderr = run_command(install_cmd, capture=False)
                if success:
                    print_success("FFmpeg installed")
                    return True
                else:
                    print_warning(f"Failed with {install_cmd[0]}: {stderr}")
        
        # Try snap
        success, _, _ = run_command(['which', 'snap'])
        if success:
            print_step("Trying snap...")
            run_command(['snap', 'install', 'ffmpeg'], capture=False)
        
        print_error("Could not install FFmpeg automatically. Please install manually.")
        return False
        
    elif plat == 'macos':
        # Check for Homebrew
        success, _, _ = run_command(['which', 'brew'])
        if not success:
            print_step("Installing Homebrew...")
            brew_install = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            success = run_command(brew_install, shell=True, capture=False)
            if not success:
                print_error("Failed to install Homebrew. Please install manually.")
                return False
        
        print_step("Installing FFmpeg via Homebrew...")
        success, _, stderr = run_command(['brew', 'install', 'ffmpeg'], capture=False)
        if success:
            print_success("FFmpeg installed")
            return True
        else:
            print_error(f"Failed to install FFmpeg: {stderr}")
            return False
            
    elif plat == 'windows':
        # Check for chocolatey
        success, _, _ = run_command(['where', 'choco'])
        if success:
            print_step("Installing FFmpeg via Chocolatey...")
            run_command(['choco', 'install', 'ffmpeg', '-y'], capture=False)
            return True
        
        # Check for winget
        success, _, _ = run_command(['where', 'winget'])
        if success:
            print_step("Installing FFmpeg via winget...")
            run_command(['winget', 'install', 'Gyan.FFmpeg', '--accept-source-agreements', '--accept-package-agreements'], capture=False)
            return True
        
        print_warning("Please install FFmpeg manually from https://ffmpeg.org/download.html")
        print_warning("Or install Chocolatey: https://chocolatey.org/install")
        print_warning("Or install winget (Windows 10 1709+ / Windows 11)")
        return False
    
    return False


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print_step("Checking FFmpeg...")
    success, version, _ = run_command(['ffmpeg', '-version'])
    if success:
        version_line = version.split('\n')[0]
        print_success(f"FFmpeg found: {version_line}")
        return True
    return False


def create_virtual_env():
    """Create Python virtual environment"""
    print_step("Creating virtual environment...")
    
    venv_path = Path('.venv')
    if venv_path.exists():
        print_warning("Virtual environment already exists")
        return True
    
    success, _, stderr = run_command([sys.executable, '-m', 'venv', '.venv'])
    if success:
        print_success("Virtual environment created")
        return True
    else:
        print_error(f"Failed to create virtual environment: {stderr}")
        return False


def get_venv_python():
    """Get path to virtual environment Python"""
    plat = get_platform()
    if plat == 'windows':
        return str(Path('.venv/Scripts/python.exe').resolve())
    else:
        return str(Path('.venv/bin/python').resolve())


def get_venv_pip():
    """Get path to virtual environment pip"""
    plat = get_platform()
    if plat == 'windows':
        return str(Path('.venv/Scripts/pip.exe').resolve())
    else:
        return str(Path('.venv/bin/pip').resolve())


def install_requirements():
    """Install Python requirements"""
    print_step("Installing Python packages...")
    
    pip = get_venv_pip()
    
    # Upgrade pip first
    run_command([pip, 'install', '--upgrade', 'pip'])
    
    # Install requirements
    success, _, stderr = run_command([pip, 'install', '-r', 'requirements.txt'])
    if success:
        print_success("Requirements installed")
        return True
    else:
        print_error(f"Failed to install requirements: {stderr}")
        return False


def configure_paths():
    """Interactive configuration for media and stream paths"""
    print_step("Configuring paths...")
    
    config = {}
    
    # Default paths based on platform
    plat = get_platform()
    if plat == 'windows':
        default_media = 'C:\\Users\\' + os.getlogin() + '\\Videos'
        default_stream = 'C:\\temp\\bedtime-streamer'
    else:
        default_media = str(Path.home() / 'Videos')
        default_stream = '/tmp/bedtime-streamer'
    
    print(f"\n{Colors.YELLOW}Media Library Path{Colors.END}")
    print("This is where your movies/TV shows are stored")
    media_path = input(f"Enter path [{default_media}]: ").strip()
    config['media_path'] = media_path if media_path else default_media
    
    print(f"\n{Colors.YELLOW}Stream Output Path{Colors.END}")
    print("This is where temporary stream chunks are stored")
    stream_path = input(f"Enter path [{default_stream}]: ").strip()
    config['stream_path'] = stream_path if stream_path else default_stream
    
    # Create directories if they don't exist
    Path(config['media_path']).mkdir(parents=True, exist_ok=True)
    Path(config['stream_path']).mkdir(parents=True, exist_ok=True)
    
    # Save config
    config_file = Path('config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Update config.py
    update_config_py(config)
    
    print_success(f"Configuration saved to {config_file}")
    return config


def update_config_py(config):
    """Update config.py with user paths"""
    config_py = Path('config.py')
    
    if not config_py.exists():
        print_warning("config.py not found, creating default...")
        default_config = f'''"""Configuration for Bedtime Streamer"""

import os

# Paths (can be overridden by environment variables)
LIBRARY_PATH = os.environ.get("LIBRARY_PATH", "{config['media_path']}")
HLS_DIR = os.environ.get("HLS_DIR", "{config['stream_path']}")
VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov')

# Ensure directories exist
os.makedirs(HLS_DIR, exist_ok=True)

PRESETS = {{
    "cpu_fast": {{
        "v_codec": "libx264",
        "v_profile": ["-preset", "veryfast", "-crf", "23"],
        "a_codec": "aac",
    }},
    "gpu_nvenc": {{
        "v_codec": "h264_nvenc",
        "v_profile": ["-preset", "p4", "-b:v", "4M"],
        "a_codec": "aac",
    }},
    "gpu_nvenc_high_quality": {{
        "v_codec": "h264_nvenc",
        "v_profile": ["-preset", "p7", "-b:v", "8M"],
        "a_codec": "aac",
    }}
}}
'''
        with open(config_py, 'w') as f:
            f.write(default_config)
        return
    
    # Read existing and update
    content = config_py.read_text()
    
    # Replace paths
    content = content.replace(
        'LIBRARY_PATH = "/media/atlas/Gaming/Media Library/"',
        f'LIBRARY_PATH = "{config["media_path"]}"'
    )
    content = content.replace(
        'HLS_DIR = "/var/www/hls"',
        f'HLS_DIR = "{config["stream_path"]}"'
    )
    
    with open(config_py, 'w') as f:
        f.write(content)


def create_launcher():
    """Create platform-specific launcher script"""
    plat = get_platform()
    
    if plat == 'windows':
        launcher = 'start.bat'
        content = '''@echo off
call .venv\\Scripts\\activate.bat
python app.py
pause
'''
    else:
        launcher = 'start.sh'
        content = '''#!/bin/bash
source .venv/bin/activate
python app.py
'''
    
    with open(launcher, 'w') as f:
        f.write(content)
    
    if plat != 'windows':
        os.chmod(launcher, 0o755)
    
    print_success(f"Created launcher: {launcher}")


def print_final_instructions(config):
    """Print final setup instructions"""
    print(f"\n{Colors.GREEN}{'='*50}{Colors.END}")
    print(f"{Colors.GREEN}Setup Complete!{Colors.END}")
    print(f"{Colors.GREEN}{'='*50}{Colors.END}")
    print(f"\nConfiguration:")
    print(f"  Media Library: {config['media_path']}")
    print(f"  Stream Output: {config['stream_path']}")
    print(f"\nTo start the server:")
    
    plat = get_platform()
    if plat == 'windows':
        print(f"  1. Run: start.bat")
        print(f"  2. Or: .venv\\Scripts\\activate && python app.py")
    else:
        print(f"  1. Run: ./start.sh")
        print(f"  2. Or: source .venv/bin/activate && python app.py")
    
    print(f"\nThen open: http://localhost:5000")
    print(f"{Colors.YELLOW}Note:{Colors.END} Make sure FFmpeg is in your PATH")
    print(f"{Colors.GREEN}{'='*50}{Colors.END}\n")


def main():
    parser = argparse.ArgumentParser(description='Setup Bedtime Streamer')
    parser.add_argument('--skip-ffmpeg', action='store_true', help='Skip FFmpeg installation')
    parser.add_argument('--skip-venv', action='store_true', help='Skip virtual environment creation')
    parser.add_argument('--config-only', action='store_true', help='Only run configuration')
    args = parser.parse_args()
    
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}  Bedtime Streamer Setup{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}\n")
    
    # Configuration only mode
    if args.config_only:
        config = configure_paths()
        print_final_instructions(config)
        return
    
    # Full setup
    check_python_version()
    
    # Check/install FFmpeg
    if not args.skip_ffmpeg:
        if not check_ffmpeg():
            install_ffmpeg()
            if not check_ffmpeg():
                print_warning("FFmpeg not found. Please install manually and re-run.")
    
    # Setup Python environment
    if not args.skip_venv:
        create_virtual_env()
        install_requirements()
    
    # Configure paths
    config = configure_paths()
    
    # Create launcher
    create_launcher()
    
    # Done
    print_final_instructions(config)


if __name__ == '__main__':
    main()