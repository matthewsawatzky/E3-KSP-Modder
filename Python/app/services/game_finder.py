import os
import platform


def get_candidate_paths():
    system = platform.system()
    home = os.path.expanduser('~')
    candidates = []

    if system == 'Darwin':
        candidates.extend([
            {
                'label': 'Steam (KSP1)',
                'path': os.path.join(home, 'Library', 'Application Support', 'Steam',
                                     'steamapps', 'common', 'Kerbal Space Program')
            },
            {
                'label': 'GOG (KSP1) - User Apps',
                'path': os.path.join(home, 'Applications', 'Kerbal Space Program')
            },
            {
                'label': 'GOG (KSP1) - System Apps',
                'path': '/Applications/Kerbal Space Program'
            },
            {
                'label': 'Steam (KSP2)',
                'path': os.path.join(home, 'Library', 'Application Support', 'Steam',
                                     'steamapps', 'common', 'Kerbal Space Program 2')
            },
        ])
    elif system == 'Windows':
        candidates.extend([
            {
                'label': 'Steam (KSP1) - Program Files x86',
                'path': r'C:\Program Files (x86)\Steam\steamapps\common\Kerbal Space Program'
            },
            {
                'label': 'Steam (KSP1) - Program Files',
                'path': r'C:\Program Files\Steam\steamapps\common\Kerbal Space Program'
            },
            {
                'label': 'GOG (KSP1)',
                'path': r'C:\GOG Games\Kerbal Space Program'
            },
            {
                'label': 'Epic (KSP1)',
                'path': r'C:\Program Files\Epic Games\KerbalSpaceProgram'
            },
            {
                'label': 'Steam (KSP2) - Program Files x86',
                'path': r'C:\Program Files (x86)\Steam\steamapps\common\Kerbal Space Program 2'
            },
            {
                'label': 'Steam (KSP2) - Program Files',
                'path': r'C:\Program Files\Steam\steamapps\common\Kerbal Space Program 2'
            },
            {
                'label': 'Epic (KSP2)',
                'path': r'C:\Program Files\Epic Games\KerbalSpaceProgram2'
            },
        ])

    return candidates


def validate_ksp_install(path):
    if not os.path.isdir(path):
        return False

    ksp1_executables = ['KSP.app', 'KSP_x64.app', 'KSP.exe', 'KSP_x64.exe']
    ksp2_executables = ['KSP2.app', 'KSP2.exe']

    for exe in ksp1_executables + ksp2_executables:
        if os.path.exists(os.path.join(path, exe)):
            return True

    if os.path.isdir(os.path.join(path, 'GameData')):
        return True

    return False


def detect_installs():
    found = []
    candidates = get_candidate_paths()

    for candidate in candidates:
        if validate_ksp_install(candidate['path']):
            found.append(candidate)

    return found
