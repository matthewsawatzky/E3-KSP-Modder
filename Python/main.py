import json
import os
import threading
import webbrowser

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

DEFAULT_CONFIG = {
    "ksp_path": None,
    "all_installs": [],
    "profiles": {},
    "mod_notes": {}
}


def ensure_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)


def open_browser():
    webbrowser.open('http://localhost:5050')


if __name__ == '__main__':
    ensure_config()
    from Python.app import create_app
    app = create_app()
    print("KSP Moder running at http://localhost:5050")
    threading.Timer(1.0, open_browser).start()
    app.run(host='0.0.0.0', port=5050, debug=True, use_reloader=False)
