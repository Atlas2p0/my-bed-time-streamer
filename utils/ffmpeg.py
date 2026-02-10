import os
import subprocess
import json
from pathlib import Path

from config import HLS_DIR


def escape_path_for_ffmpeg(path):
    """Escape path for FFmpeg filter expressions."""
    path = Path(path).as_posix()
    return path.replace("'", "'\\\\\\''").replace(":", "\\:")


def get_video_metadata(file_path):
    """Uses ffprobe to check for video info and subtitle tracks."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_streams',
        '-of', 'json',
        file_path
    ]
    try:
        result = subprocess.check_output(cmd).decode('utf-8')
        data = json.loads(result)

        text_sub_index = None
        pgs_sub_index = None
        text_formats = ['ass', 'ssa', 'subrip', 'srt', 'mov_text']

        sub_count = 0
        for s in data['streams']:
            if s['codec_type'] == 'subtitle':
                codec = s.get('codec_name', '')
                if codec in text_formats and text_sub_index is None:
                    text_sub_index = sub_count
                elif codec == 'hdmv_pgs_subtitle' and pgs_sub_index is None:
                    pgs_sub_index = sub_count
                sub_count += 1

        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        return {
            "has_internal_subs": (text_sub_index is not None or pgs_sub_index is not None),
            "text_sub_index": text_sub_index,
            "pgs_sub_index": pgs_sub_index,
            "codec": video_stream.get('codec_name') if video_stream else "unknown",
            "resolution": f"{video_stream.get('width')}x{video_stream.get('height')}" if video_stream else "unknown"
        }
    except Exception as e:
        print(f"Error probing {file_path}: {e}")
        return None

def build_ffmpeg_cmd_force_sync_av(movie_path, preset, metadata, sub_path=None):
    """MKV-specific handling with forced A/V sync fixes."""
    
    hls_native = Path(HLS_DIR)
    hls_native.mkdir(parents=True, exist_ok=True)
    
    init_file = "init.mp4"
    segment_file = "chunk_%d.m4s"
    playlist_file = "index.m3u8"
    
    cmd = ["ffmpeg", "-y"]
    
    # MKV-specific input flags
    cmd += [
        "-fflags", "+genpts",
        "-thread_queue_size", "512",
    ]
    
    cmd += ["-i", movie_path]
    
    # Sync and timing fixes
    cmd += [
        "-vsync", "cfr",
        "-async", "1",
        "-max_muxing_queue_size", "1024",
    ]
    
    # Explicit stream mapping
    cmd += ["-map", "0:v:0", "-map", "0:a:0"]

    # Filter logic with timestamp normalization
    base_vf = "setpts=PTS-STARTPTS,format=yuv420p"
    
    if sub_path and sub_path != "":
        esc_sub = escape_path_for_ffmpeg(sub_path)
        filter_str = f"subtitles='{esc_sub}',{base_vf}"
        cmd += ["-vf", filter_str]
    elif metadata.get('text_sub_index') is not None:
        esc_path = escape_path_for_ffmpeg(movie_path)
        idx = metadata.get('text_sub_index')
        filter_str = f"subtitles='{esc_path}':si={idx},{base_vf}"
        cmd += ["-vf", filter_str]
    elif metadata.get('pgs_sub_index') is not None:
        idx = metadata.get('pgs_sub_index')
        cmd += ["-filter_complex", f"[0:v][0:s:{idx}]overlay,setpts=PTS-STARTPTS,format=yuv420p"]
    else:
        cmd += ["-vf", base_vf]

    # Video encoding
    cmd += ["-c:v", preset['v_codec']] + preset['v_profile']
    cmd += [
        "-g", "48",
        "-keyint_min", "48",
        "-sc_threshold", "0",
    ]

    # Audio encoding with sync
    cmd += [
        "-c:a", preset['a_codec'],
        "-b:a", "192k",
        "-ac", "2",
        "-af", "aresample=async=1:min_hard_comp=0.100000:first_pts=0",
    ]

    # CMAF output
    cmd += [
        "-f", "hls",
        "-hls_playlist_type", "event",
        "-hls_flags", "independent_segments+omit_endlist",
        "-hls_segment_type", "fmp4",
        "-hls_time", "6",
        "-hls_list_size", "0",
        "-hls_fmp4_init_filename", init_file,
        "-hls_segment_filename", segment_file,
        playlist_file
    ]
    
    return cmd, str(hls_native)

def build_ffmpeg_command(movie_path, preset, metadata, sub_path=None, force_sync=False):
    """Build the FFmpeg command for CMAF streaming."""
    
    # Route to force sync handler when flag is set
    if force_sync:
        return build_ffmpeg_cmd_force_sync_av(movie_path, preset, metadata, sub_path)
    
    # Original logic for all other cases (completely unchanged)
    hls_native = Path(HLS_DIR)
    hls_native.mkdir(parents=True, exist_ok=True)
    
    init_file = "init.mp4"
    segment_file = "chunk_%d.m4s"
    playlist_file = "index.m3u8"
    
    cmd = ["ffmpeg", "-y", "-i", movie_path]

    # Filter Logic
    if sub_path and sub_path != "":
        esc_sub = escape_path_for_ffmpeg(sub_path)
        filter_str = f"subtitles='{esc_sub}',format=yuv420p"
        cmd += ["-vf", filter_str]
    elif metadata.get('text_sub_index') is not None:
        esc_path = escape_path_for_ffmpeg(movie_path)
        idx = metadata.get('text_sub_index')
        filter_str = f"subtitles='{esc_path}':si={idx},format=yuv420p"
        cmd += ["-vf", filter_str]
    elif metadata.get('pgs_sub_index') is not None:
        idx = metadata.get('pgs_sub_index')
        cmd += ["-filter_complex", f"[0:v][0:s:{idx}]overlay,format=yuv420p"]
    else:
        cmd += ["-vf", "format=yuv420p"]

    # Video/audio encoding
    cmd += ["-c:v", preset['v_codec']] + preset['v_profile']
    cmd += ["-c:a", preset['a_codec'], "-b:a", "192k", "-ac", "2"]

    # CMAF settings with relative paths
    cmd += [
        "-f", "hls",
        "-hls_playlist_type", "event",
        "-hls_flags", "independent_segments+omit_endlist",
        "-hls_segment_type", "fmp4",
        "-hls_time", "6",
        "-hls_list_size", "0",
        "-hls_fmp4_init_filename", init_file,
        "-hls_segment_filename", segment_file,
        playlist_file
    ]
    
    return cmd, str(hls_native)

def cleanup_hls_directory():
    """Remove old CMAF segments and playlist files."""
    extensions = (".m4s", ".m3u8", ".mp4")
    
    hls_dir_native = Path(HLS_DIR)
    
    if not hls_dir_native.exists():
        return
        
    for f in hls_dir_native.iterdir():
        if f.suffix in extensions:
            try:
                f.unlink()
            except:
                pass