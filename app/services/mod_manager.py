import json
import os
import shutil
import tempfile
import zipfile
from collections import defaultdict


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


def parse_version_file(mod_path):
    for fname in os.listdir(mod_path):
        if fname.endswith('.version'):
            vfile = os.path.join(mod_path, fname)
            try:
                with open(vfile, 'r', errors='ignore') as f:
                    data = json.load(f)
                ver = data.get('VERSION', data.get('version', None))
                if ver and isinstance(ver, dict):
                    major = ver.get('MAJOR', ver.get('major', 0))
                    minor = ver.get('MINOR', ver.get('minor', 0))
                    patch = ver.get('PATCH', ver.get('patch', 0))
                    return f"{major}.{minor}.{patch}"
                elif ver and isinstance(ver, str):
                    return ver
            except (json.JSONDecodeError, OSError):
                pass
    return None


def list_mods(ksp_path):
    gamedata = os.path.join(ksp_path, 'GameData')
    if not os.path.isdir(gamedata):
        return []

    skip = {'Squad', 'SquadExpansion', 'Squad Expansion'}
    mods = []

    for entry in sorted(os.listdir(gamedata)):
        entry_path = os.path.join(gamedata, entry)
        if not os.path.isdir(entry_path):
            continue

        base_name = entry
        enabled = True
        if entry.endswith('.disabled'):
            base_name = entry[:-9]
            enabled = False

        if base_name in skip:
            continue

        size_bytes = get_folder_size(entry_path)
        size_mb = round(size_bytes / (1024 * 1024), 2)
        version = parse_version_file(entry_path)

        mods.append({
            'name': base_name,
            'folder': entry,
            'enabled': enabled,
            'size_mb': size_mb,
            'version': version,
        })

    return mods


def detect_conflicts(ksp_path):
    gamedata = os.path.join(ksp_path, 'GameData')
    if not os.path.isdir(gamedata):
        return {}

    file_owners = defaultdict(list)

    for entry in os.listdir(gamedata):
        entry_path = os.path.join(gamedata, entry)
        if not os.path.isdir(entry_path):
            continue
        if entry.endswith('.disabled'):
            continue

        base_name = entry
        for dirpath, dirnames, filenames in os.walk(entry_path):
            for fname in filenames:
                rel = os.path.relpath(os.path.join(dirpath, fname), entry_path)
                file_owners[rel].append(base_name)

    conflicts = {}
    for rel_path, owners in file_owners.items():
        if len(owners) > 1:
            for owner in owners:
                if owner not in conflicts:
                    conflicts[owner] = []
                conflicts[owner].append({
                    'file': rel_path,
                    'shared_with': [o for o in owners if o != owner]
                })

    return conflicts


def toggle_mod(ksp_path, mod_name):
    gamedata = os.path.join(ksp_path, 'GameData')
    enabled_path = os.path.join(gamedata, mod_name)
    disabled_path = os.path.join(gamedata, mod_name + '.disabled')

    if os.path.isdir(enabled_path):
        os.rename(enabled_path, disabled_path)
        return {'name': mod_name, 'enabled': False}
    elif os.path.isdir(disabled_path):
        os.rename(disabled_path, enabled_path)
        return {'name': mod_name, 'enabled': True}
    else:
        return None


def remove_mod(ksp_path, mod_name):
    gamedata = os.path.join(ksp_path, 'GameData')
    for suffix in ['', '.disabled']:
        path = os.path.join(gamedata, mod_name + suffix)
        if os.path.isdir(path):
            size = get_folder_size(path)
            size_mb = round(size / (1024 * 1024), 2)
            shutil.rmtree(path)
            return {'name': mod_name, 'size_mb': size_mb, 'large': size_mb > 50}
    return None


def add_mod(ksp_path, zip_file):
    gamedata = os.path.join(ksp_path, 'GameData')
    if not os.path.isdir(gamedata):
        os.makedirs(gamedata)

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'mod.zip')
        zip_file.save(zip_path)

        extract_dir = os.path.join(tmpdir, 'extracted')
        os.makedirs(extract_dir)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)

        extracted_gamedata = os.path.join(extract_dir, 'GameData')
        if not os.path.isdir(extracted_gamedata):
            contents = os.listdir(extract_dir)
            if len(contents) == 1:
                single = os.path.join(extract_dir, contents[0])
                if os.path.isdir(single):
                    inner_gd = os.path.join(single, 'GameData')
                    if os.path.isdir(inner_gd):
                        extracted_gamedata = inner_gd

        added_mods = []
        if os.path.isdir(extracted_gamedata):
            for entry in os.listdir(extracted_gamedata):
                src = os.path.join(extracted_gamedata, entry)
                dst = os.path.join(gamedata, entry)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    added_mods.append(entry)
                else:
                    shutil.copy2(src, dst)
        else:
            contents = os.listdir(extract_dir)
            if len(contents) == 1 and os.path.isdir(os.path.join(extract_dir, contents[0])):
                src = os.path.join(extract_dir, contents[0])
                dst = os.path.join(gamedata, contents[0])
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                added_mods.append(contents[0])
            else:
                zip_basename = os.path.splitext(zip_file.filename)[0]
                dst = os.path.join(gamedata, zip_basename)
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(extract_dir, dst)
                added_mods.append(zip_basename)

        return added_mods


def get_enabled_mod_names(ksp_path):
    gamedata = os.path.join(ksp_path, 'GameData')
    if not os.path.isdir(gamedata):
        return []
    skip = {'Squad', 'SquadExpansion', 'Squad Expansion'}
    enabled = []
    for entry in os.listdir(gamedata):
        if not os.path.isdir(os.path.join(gamedata, entry)):
            continue
        if entry.endswith('.disabled'):
            continue
        if entry in skip:
            continue
        enabled.append(entry)
    return sorted(enabled)


def apply_profile(ksp_path, enabled_list):
    gamedata = os.path.join(ksp_path, 'GameData')
    if not os.path.isdir(gamedata):
        return

    skip = {'Squad', 'SquadExpansion', 'Squad Expansion'}
    enabled_set = set(enabled_list)

    for entry in os.listdir(gamedata):
        entry_path = os.path.join(gamedata, entry)
        if not os.path.isdir(entry_path):
            continue

        if entry.endswith('.disabled'):
            base = entry[:-9]
            if base in skip:
                continue
            if base in enabled_set:
                os.rename(entry_path, os.path.join(gamedata, base))
        else:
            if entry in skip:
                continue
            if entry not in enabled_set:
                os.rename(entry_path, os.path.join(gamedata, entry + '.disabled'))
