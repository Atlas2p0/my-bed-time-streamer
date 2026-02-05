"""Filesystem utilities for scanning and discovering media files."""

import os
from pathlib import Path

from config import LIBRARY_PATH, VIDEO_EXTENSIONS


def scan_library():
    """Scan the media library and return folder/episode structure."""
    library_data = []
    
    # Convert forward-slash path back to native path for OS operations
    lib_path_native = Path(LIBRARY_PATH)
    
    # Check if path exists
    if not lib_path_native.exists():
        print(f"Warning: Library path does not exist: {lib_path_native}")
        return library_data
    
    # We list the top-level directories in your Media Library
    for entry in os.scandir(lib_path_native):
        if entry.is_dir():
            folder_path = entry.path
            episodes = []
            local_subs = []

            # Scan inside this specific folder
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    full_p = os.path.join(root, f)
                    if f.lower().endswith(VIDEO_EXTENSIONS):
                        episodes.append({
                            "name": f,
                            "path": full_p
                        })
                    elif f.lower().endswith('.srt'):
                        local_subs.append({
                            "name": f,
                            "path": full_p
                        })

            if episodes:
                library_data.append({
                    "folder_name": entry.name,
                    "local_subs": local_subs,
                    "episodes": sorted(episodes, key=lambda x: x['name'])
                })

    return library_data