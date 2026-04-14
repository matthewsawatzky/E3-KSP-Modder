import os
from flask import Blueprint, jsonify, request
from app import load_config
from app.services.log_reader import read_log, scan_mod_errors

logs_bp = Blueprint('logs', __name__)


def get_ksp_path():
    config = load_config()
    path = config.get('ksp_path')
    if not path or not os.path.isdir(path):
        return None
    return path


@logs_bp.route('/api/logs')
def api_logs():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    filter_mode = request.args.get('filter', 'all')
    valid_filters = ['all', 'errors', 'warnings', 'errors+warnings']
    if filter_mode not in valid_filters:
        filter_mode = 'all'

    result = read_log(ksp, filter_mode)
    if result.get('error') and not result.get('lines'):
        return jsonify(result), 404

    return jsonify(result)


@logs_bp.route('/api/logs/mod-errors')
def api_mod_errors():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    from app.services.mod_manager import list_mods
    mod_names = [m['name'] for m in list_mods(ksp)]

    result = scan_mod_errors(ksp, mod_names)
    if result.get('error') and not result.get('results'):
        return jsonify(result), 404

    return jsonify(result)
