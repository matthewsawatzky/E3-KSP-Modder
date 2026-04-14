import os
from flask import Blueprint, jsonify, request
from app import load_config, save_config
from app.services.mod_manager import (
    list_mods, detect_conflicts, toggle_mod, remove_mod, add_mod,
    get_enabled_mod_names, apply_profile
)

mods_bp = Blueprint('mods', __name__)


def get_ksp_path():
    config = load_config()
    path = config.get('ksp_path')
    if not path or not os.path.isdir(path):
        return None
    return path


@mods_bp.route('/api/mods')
def api_list_mods():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    mods = list_mods(ksp)
    conflicts = detect_conflicts(ksp)

    for mod in mods:
        mod['conflicts'] = conflicts.get(mod['name'], [])

    config = load_config()
    notes = config.get('mod_notes', {})

    for mod in mods:
        mod['note'] = notes.get(mod['name'], '')

    gamedata = os.path.join(ksp, 'GameData')
    total_size = 0
    if os.path.isdir(gamedata):
        for dirpath, dirnames, filenames in os.walk(gamedata):
            for f in filenames:
                try:
                    total_size += os.path.getsize(os.path.join(dirpath, f))
                except OSError:
                    pass

    return jsonify({
        'mods': mods,
        'total_count': len(mods),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
    })


@mods_bp.route('/api/mods/add', methods=['POST'])
def api_add_mod():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    f = request.files['file']
    if not f.filename or not f.filename.endswith('.zip'):
        return jsonify({'error': 'Only .zip files are supported'}), 400

    try:
        added = add_mod(ksp, f)
        return jsonify({'success': True, 'added': added})
    except PermissionError:
        return jsonify({'error': 'Permission denied writing to GameData'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mods_bp.route('/api/mods/<name>', methods=['DELETE'])
def api_remove_mod(name):
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    try:
        result = remove_mod(ksp, name)
        if result is None:
            return jsonify({'error': f'Mod "{name}" not found'}), 404
        return jsonify({
            'success': True,
            'warning': f'Removed large mod ({result["size_mb"]} MB)' if result['large'] else None,
            **result
        })
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mods_bp.route('/api/mods/<name>/toggle', methods=['POST'])
def api_toggle_mod(name):
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    try:
        result = toggle_mod(ksp, name)
        if result is None:
            return jsonify({'error': f'Mod "{name}" not found'}), 404
        return jsonify({'success': True, **result})
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mods_bp.route('/api/mods/bulk', methods=['POST'])
def api_bulk_action():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    data = request.get_json()
    if not data or 'action' not in data or 'mods' not in data:
        return jsonify({'error': 'Missing action or mods list'}), 400

    action = data['action']
    mod_names = data['mods']
    results = []
    errors = []

    for name in mod_names:
        try:
            if action == 'enable':
                gamedata = os.path.join(ksp, 'GameData')
                disabled_path = os.path.join(gamedata, name + '.disabled')
                enabled_path = os.path.join(gamedata, name)
                if os.path.isdir(disabled_path):
                    os.rename(disabled_path, enabled_path)
                    results.append(name)
                elif os.path.isdir(enabled_path):
                    results.append(name)
            elif action == 'disable':
                gamedata = os.path.join(ksp, 'GameData')
                enabled_path = os.path.join(gamedata, name)
                disabled_path = os.path.join(gamedata, name + '.disabled')
                if os.path.isdir(enabled_path) and not name.endswith('.disabled'):
                    os.rename(enabled_path, disabled_path)
                    results.append(name)
                elif os.path.isdir(disabled_path):
                    results.append(name)
            elif action == 'remove':
                result = remove_mod(ksp, name)
                if result:
                    results.append(name)
                else:
                    errors.append(f'{name}: not found')
            else:
                return jsonify({'error': f'Unknown action: {action}'}), 400
        except PermissionError:
            errors.append(f'{name}: permission denied')
        except Exception as e:
            errors.append(f'{name}: {str(e)}')

    return jsonify({
        'success': True,
        'action': action,
        'affected': results,
        'errors': errors,
    })


@mods_bp.route('/api/mods/notes', methods=['GET'])
def api_get_notes():
    config = load_config()
    return jsonify(config.get('mod_notes', {}))


@mods_bp.route('/api/mods/notes', methods=['POST'])
def api_set_note():
    data = request.get_json()
    if not data or 'mod' not in data:
        return jsonify({'error': 'Missing mod name'}), 400

    config = load_config()
    if 'mod_notes' not in config:
        config['mod_notes'] = {}

    note = data.get('note', '').strip()
    if note:
        config['mod_notes'][data['mod']] = note
    else:
        config['mod_notes'].pop(data['mod'], None)

    save_config(config)
    return jsonify({'success': True})


@mods_bp.route('/api/profiles')
def api_list_profiles():
    config = load_config()
    return jsonify(config.get('profiles', {}))


@mods_bp.route('/api/profiles/save', methods=['POST'])
def api_save_profile():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing profile name'}), 400

    name = data['name'].strip()
    if not name:
        return jsonify({'error': 'Profile name cannot be empty'}), 400

    enabled = get_enabled_mod_names(ksp)
    config = load_config()
    if 'profiles' not in config:
        config['profiles'] = {}
    config['profiles'][name] = enabled
    save_config(config)

    return jsonify({'success': True, 'name': name, 'mods': enabled})


@mods_bp.route('/api/profiles/load', methods=['POST'])
def api_load_profile():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing profile name'}), 400

    config = load_config()
    profiles = config.get('profiles', {})
    name = data['name']

    if name not in profiles:
        return jsonify({'error': f'Profile "{name}" not found'}), 404

    try:
        apply_profile(ksp, profiles[name])
        return jsonify({'success': True, 'name': name})
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mods_bp.route('/api/profiles/<name>', methods=['DELETE'])
def api_delete_profile(name):
    config = load_config()
    profiles = config.get('profiles', {})

    if name not in profiles:
        return jsonify({'error': f'Profile "{name}" not found'}), 404

    del profiles[name]
    config['profiles'] = profiles
    save_config(config)

    return jsonify({'success': True})
