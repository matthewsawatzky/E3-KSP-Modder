import json
import os
from flask import Flask

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')

DEFAULT_CONFIG = {
    "ksp_path": None,
    "all_installs": [],
    "profiles": {},
    "mod_notes": {},
    "settings": {
        "accent_color": "#8AC04A",
        "log_lines": 500,
        "confirm_remove": True,
        "sort_mods_by": "name"
    }
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    from Python.app.routes.setup import setup_bp
    from Python.app.routes.mods import mods_bp
    from Python.app.routes.saves import saves_bp
    from Python.app.routes.logs import logs_bp
    from Python.app.routes.info import info_bp

    app.register_blueprint(setup_bp)
    app.register_blueprint(mods_bp)
    app.register_blueprint(saves_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(info_bp)

    return app
