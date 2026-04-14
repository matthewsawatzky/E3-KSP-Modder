import os
import platform


def find_log_file(ksp_path):
    candidates = [
        os.path.join(ksp_path, 'KSP.log'),
        os.path.join(ksp_path, 'KSP2.log'),
    ]

    if platform.system() == 'Darwin':
        candidates.append(os.path.join(os.path.expanduser('~'),
                                       'Library', 'Logs', 'Unity', 'Player.log'))

    if platform.system() == 'Windows':
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            local = os.path.join(os.path.dirname(appdata), 'LocalLow',
                                 'Squad', 'Kerbal Space Program', 'Player.log')
            candidates.append(local)

    for path in candidates:
        if os.path.isfile(path):
            return path

    return None


def read_log(ksp_path, filter_mode='all'):
    log_path = find_log_file(ksp_path)
    if not log_path:
        return {'error': 'No log file found', 'lines': [], 'path': None}

    try:
        with open(log_path, 'r', errors='replace') as f:
            all_lines = f.readlines()
    except OSError as e:
        return {'error': str(e), 'lines': [], 'path': log_path}

    if filter_mode == 'all':
        lines = all_lines[-500:]
    elif filter_mode == 'errors':
        lines = [l for l in all_lines if is_error_line(l)]
        lines = lines[-500:]
    elif filter_mode == 'warnings':
        lines = [l for l in all_lines if is_warning_line(l)]
        lines = lines[-500:]
    elif filter_mode == 'errors+warnings':
        lines = [l for l in all_lines if is_error_line(l) or is_warning_line(l)]
        lines = lines[-500:]
    else:
        lines = all_lines[-500:]

    return {
        'lines': [l.rstrip('\n\r') for l in lines],
        'path': log_path,
        'total_lines': len(all_lines),
        'error': None,
    }


def is_error_line(line):
    markers = ['[ERR]', '[EXC]', 'Exception', 'Error']
    return any(m in line for m in markers)


def is_warning_line(line):
    markers = ['[WRN]', 'Warning']
    return any(m in line for m in markers)


def scan_mod_errors(ksp_path, mod_names):
    """Scan the full log file and group error lines by which mod they mention."""
    log_path = find_log_file(ksp_path)
    if not log_path:
        return {
            'error': 'No log file found',
            'results': {},
            'unattributed_count': 0,
            'total_errors': 0,
        }

    try:
        with open(log_path, 'r', errors='replace') as f:
            all_lines = f.readlines()
    except OSError as e:
        return {
            'error': str(e),
            'results': {},
            'unattributed_count': 0,
            'total_errors': 0,
        }

    error_lines = [l.rstrip('\n\r') for l in all_lines if is_error_line(l)]

    # Build lowercase name → original name lookup
    mod_lookup = {name.lower(): name for name in mod_names if name}

    MAX_LINES_PER_MOD = 20
    results = {}   # original_name -> {'lines': [...], 'total': int}
    unattributed_count = 0

    for line in error_lines:
        line_lower = line.lower()
        matched = [
            orig for lower, orig in mod_lookup.items()
            if lower in line_lower
        ]

        if matched:
            for mod_name in matched:
                if mod_name not in results:
                    results[mod_name] = {'lines': [], 'total': 0}
                results[mod_name]['total'] += 1
                if len(results[mod_name]['lines']) < MAX_LINES_PER_MOD:
                    results[mod_name]['lines'].append(line)
        else:
            unattributed_count += 1

    # Sort by error count, highest first
    sorted_results = dict(
        sorted(results.items(), key=lambda x: x[1]['total'], reverse=True)
    )

    return {
        'error': None,
        'results': sorted_results,
        'unattributed_count': unattributed_count,
        'total_errors': len(error_lines),
    }
