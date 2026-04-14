import os
from flask import Blueprint, jsonify, send_from_directory
from app import load_config
from app.services.disk_usage import get_disk_usage, get_game_version, list_screenshots, list_crafts

info_bp = Blueprint('info', __name__)


def get_ksp_path():
    config = load_config()
    path = config.get('ksp_path')
    if not path or not os.path.isdir(path):
        return None
    return path


@info_bp.route('/api/info')
def api_info():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    version = get_game_version(ksp)
    usage = get_disk_usage(ksp)

    return jsonify({
        'version': version,
        'disk_usage': usage,
        'path': ksp,
    })


@info_bp.route('/api/screenshots')
def api_screenshots():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    screenshots = list_screenshots(ksp)
    return jsonify(screenshots)


@info_bp.route('/screenshots/<filename>')
def serve_screenshot(filename):
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 404

    ss_dir = os.path.join(ksp, 'Screenshots')
    if not os.path.isdir(ss_dir):
        return jsonify({'error': 'Screenshots folder not found'}), 404

    safe = os.path.basename(filename)
    return send_from_directory(ss_dir, safe)


@info_bp.route('/api/crafts')
def api_crafts():
    ksp = get_ksp_path()
    if not ksp:
        return jsonify({'error': 'No KSP path configured'}), 400

    crafts = list_crafts(ksp)
    return jsonify(crafts)
