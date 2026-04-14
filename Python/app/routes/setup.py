import os
from flask import Blueprint, jsonify, request
from Python.app import load_config, save_config
from Python.app.services.game_finder import detect_installs, validate_ksp_install

setup_bp = Blueprint('setup', __name__)


@setup_bp.route('/api/detect-installs')
def api_detect_installs():
    installs = detect_installs()
    config = load_config()
    config['all_installs'] = [i['path'] for i in installs]
    save_config(config)
    return jsonify(installs)


@setup_bp.route('/api/set-path', methods=['POST'])
def api_set_path():
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'Missing path'}), 400

    path = data['path']
    if not validate_ksp_install(path):
        return jsonify({'error': 'Not a valid KSP install directory'}), 400

    config = load_config()
    config['ksp_path'] = path
    if path not in config['all_installs']:
        config['all_installs'].append(path)
    save_config(config)

    return jsonify({'success': True, 'path': path})


@setup_bp.route('/api/current-path')
def api_current_path():
    config = load_config()
    path = config.get('ksp_path')
    exists = path and os.path.isdir(path) if path else False
    return jsonify({'path': path, 'exists': exists})


@setup_bp.route('/api/settings', methods=['GET'])
def api_get_settings():
    config = load_config()
    defaults = {
        'accent_color': '#8AC04A',
        'log_lines': 500,
        'confirm_remove': True,
        'sort_mods_by': 'name',
    }
    settings = config.get('settings', {})
    for k, v in defaults.items():
        settings.setdefault(k, v)
    return jsonify(settings)


@setup_bp.route('/api/settings', methods=['POST'])
def api_save_settings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No settings provided'}), 400

    config = load_config()
    if 'settings' not in config:
        config['settings'] = {}

    allowed = {'accent_color', 'log_lines', 'confirm_remove', 'sort_mods_by'}
    for key in allowed:
        if key in data:
            config['settings'][key] = data[key]

    save_config(config)
    return jsonify({'success': True, 'settings': config['settings']})
