import os
from datetime import datetime


def get_folder_size(path):
    if not os.path.isdir(path):
        return 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def get_disk_usage(ksp_path):
    folders = {
        'GameData': os.path.join(ksp_path, 'GameData'),
        'saves': os.path.join(ksp_path, 'saves'),
        'Screenshots': os.path.join(ksp_path, 'Screenshots'),
        'Ships': os.path.join(ksp_path, 'Ships'),
    }

    usage = {}
    total = 0
    for name, path in folders.items():
        size = get_folder_size(path)
        usage[name] = round(size / (1024 * 1024), 2)
        total += size

    install_size = get_folder_size(ksp_path)
    usage['Total'] = round(install_size / (1024 * 1024), 2)

    return usage


def get_game_version(ksp_path):
    for fname in ['buildID.txt', 'buildID64.txt']:
        fpath = os.path.join(ksp_path, fname)
        if os.path.isfile(fpath):
            try:
                with open(fpath, 'r') as f:
                    for line in f:
                        if line.lower().startswith('build id ='):
                            return line.split('=', 1)[1].strip()
            except OSError:
                pass

    readme = os.path.join(ksp_path, 'readme.txt')
    if os.path.isfile(readme):
        try:
            with open(readme, 'r') as f:
                return f.readline().strip()
        except OSError:
            pass

    return 'Unknown'


def list_screenshots(ksp_path):
    ss_dir = os.path.join(ksp_path, 'Screenshots')
    if not os.path.isdir(ss_dir):
        return []

    screenshots = []
    for fname in sorted(os.listdir(ss_dir)):
        fpath = os.path.join(ss_dir, fname)
        if not os.path.isfile(fpath):
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.bmp', '.tga'):
            continue
        try:
            size_bytes = os.path.getsize(fpath)
            size_mb = round(size_bytes / (1024 * 1024), 2)
        except OSError:
            size_mb = 0
        screenshots.append({
            'filename': fname,
            'size_mb': size_mb,
        })

    return screenshots


def list_crafts(ksp_path):
    crafts = []
    ships_dir = os.path.join(ksp_path, 'Ships')

    for craft_type in ['VAB', 'SPH']:
        type_dir = os.path.join(ships_dir, craft_type)
        if not os.path.isdir(type_dir):
            continue
        for fname in sorted(os.listdir(type_dir)):
            if not fname.endswith('.craft'):
                continue
            fpath = os.path.join(type_dir, fname)
            try:
                size_bytes = os.path.getsize(fpath)
                size_kb = round(size_bytes / 1024, 1)
                mtime = os.path.getmtime(fpath)
                modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            except OSError:
                size_kb = 0
                modified = 'Unknown'
            crafts.append({
                'name': os.path.splitext(fname)[0],
                'type': craft_type,
                'size_kb': size_kb,
                'modified': modified,
            })

    return crafts
