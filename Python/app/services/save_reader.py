import os
import shutil
import zipfile
from datetime import datetime


def get_folder_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def list_saves(ksp_path):
    saves_dir = os.path.join(ksp_path, 'saves')
    if not os.path.isdir(saves_dir):
        return []

    skip = {'backups', 'scenarios', 'training'}
    saves = []

    for entry in sorted(os.listdir(saves_dir)):
        entry_path = os.path.join(saves_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        if entry.lower() in skip:
            continue

        size_bytes = get_folder_size(entry_path)
        size_mb = round(size_bytes / (1024 * 1024), 2)

        try:
            mtime = os.path.getmtime(entry_path)
            modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except OSError:
            modified = 'Unknown'

        backups = list_backups_for_save(ksp_path, entry)

        saves.append({
            'name': entry,
            'size_mb': size_mb,
            'modified': modified,
            'backups': backups,
        })

    return saves


def list_backups_for_save(ksp_path, save_name):
    backups_dir = os.path.join(ksp_path, 'saves', 'backups')
    if not os.path.isdir(backups_dir):
        return []

    backups = []
    prefix = save_name + '_'
    for fname in sorted(os.listdir(backups_dir)):
        if fname.startswith(prefix) and fname.endswith('.zip'):
            fpath = os.path.join(backups_dir, fname)
            try:
                size_bytes = os.path.getsize(fpath)
                size_mb = round(size_bytes / (1024 * 1024), 2)
                mtime = os.path.getmtime(fpath)
                modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            except OSError:
                size_mb = 0
                modified = 'Unknown'
            backups.append({
                'filename': fname,
                'size_mb': size_mb,
                'created': modified,
            })

    return backups


def backup_save(ksp_path, save_name):
    saves_dir = os.path.join(ksp_path, 'saves')
    save_path = os.path.join(saves_dir, save_name)

    if not os.path.isdir(save_path):
        return None

    backups_dir = os.path.join(saves_dir, 'backups')
    os.makedirs(backups_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_name = f"{save_name}_{timestamp}.zip"
    zip_path = os.path.join(backups_dir, zip_name)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(save_path):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                arcname = os.path.join(save_name, os.path.relpath(fpath, save_path))
                zf.write(fpath, arcname)

    size_bytes = os.path.getsize(zip_path)
    size_mb = round(size_bytes / (1024 * 1024), 2)

    return {
        'filename': zip_name,
        'path': zip_path,
        'size_mb': size_mb,
    }
