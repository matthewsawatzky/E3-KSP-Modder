import os
from flask import Blueprint, jsonify
from app import load_config
from app.services.save_reader import list_saves, backup_save

saves_bp = Blueprint('saves', __name__)


def get_ksp_path():
    config = load_config()
    path = config.get('ksp_path')
    if not path or not os.path.isdir(path):
        return None
    return path


@saves_bp.route('/api/saves')
def api_list_saves():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    saves = list_saves(ksp)
    return jsonify(saves)


@saves_bp.route('/api/saves/<name>/backup', methods=['POST'])
def api_backup_save(name):
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    try:
        result = backup_save(ksp, name)
        if result is None:
            return jsonify({'error': f'Save "{name}" not found'}), 404
        return jsonify({'success': True, **result})
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
