"""Launch local SiteSafe services without passing Unicode commands through CMD."""
from pathlib import Path
import argparse
import json
import os
import socket
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser

APP = Path(__file__).resolve().parent
ROOT = APP / 'detectmodel/Site_Safety_OpenRisk'
LOGS = APP / 'runtime/sitesafe-start'
PIDS = APP / 'runtime/pids'
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def get(url):
    with HTTP.open(url, timeout=2) as response:
        return response.read().decode('utf-8')

def listening(port):
    with socket.socket() as sock:
        sock.settimeout(1)
        return sock.connect_ex(('127.0.0.1', port)) == 0

def ensure(name, port, command, cwd, health, validate):
    def ready():
        try:
            return validate(get(health))
        except Exception:
            return False
    if ready():
        print(f'[OK] {name}: already running', flush=True)
        return
    if listening(port):
        raise RuntimeError(f'Port {port} is occupied but {name} is not healthy. Existing process was left running.')
    logfile = LOGS / f'{name}.log'
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUNBUFFERED'] = '1'
    env['PATH'] = str(Path(sys.executable).parent / 'nodejs') + os.pathsep + env['PATH']
    with logfile.open('ab') as log:
        proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                stdout=log, stderr=subprocess.STDOUT,
                                creationflags=(subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == 'nt' else 0,
                                start_new_session=os.name != 'nt')
    (PIDS / f'{name}.pid').write_text(str(proc.pid), encoding='ascii')
    print(f'[START] {name} (PID {proc.pid})', flush=True)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f'{name} exited with code {proc.returncode}. Log: {logfile}')
        if ready():
            print(f'[OK] {name}', flush=True)
            return
        time.sleep(0.5)
    raise RuntimeError(f'{name} did not become ready within 60 seconds. Log: {logfile}')

def find_node():
    override = os.environ.get('SITESAFE_NODE')
    if override:
        if not Path(override).is_file():
            raise RuntimeError('SITESAFE_NODE must point to a Node.js executable.')
        return Path(override)
    name = 'node.exe' if os.name == 'nt' else 'node'
    candidates = [Path(sys.executable).parent / 'nodejs' / name,
                  shutil.which('node'), APP / 'node-runtime' / name]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise RuntimeError('Node.js was not found. Install Node.js and add it to PATH, or set SITESAFE_NODE.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', choices=['demo', 'offline', 'standard'], default='demo')
    parser.add_argument('--select', action='store_true')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--displays', action='store_true')
    args = parser.parse_args()
    if args.select:
        print('1: Demo (installed)   2: Offline models   3: Standard models')
        try:
            choice = input('Select mode [1]: ').strip() or '1'
        except EOFError:
            choice = '1'
        if choice not in ('1', '2', '3'):
            raise RuntimeError('Invalid mode. Select 1, 2 or 3.')
        args.profile = {'1': 'demo', '2': 'offline', '3': 'standard'}[choice]
    LOGS.mkdir(parents=True, exist_ok=True)
    PIDS.mkdir(parents=True, exist_ok=True)
    node = find_node()
    for file in (ROOT / 'app_server.py', ROOT / 'detect_bridge.py', node,
                 APP / 'pc-admin/node_modules/vite/bin/vite.js'):
        if not file.is_file():
            raise RuntimeError(f'Required file missing: {file}')
    print(f'Python: {sys.executable}\nProfile: {args.profile}', flush=True)
    ensure('business-8800', 8800,
           [sys.executable, 'app_server.py', '--host', '127.0.0.1', '--port', '8800',
            '--data-dir', 'results/seven_examples_release/frontend'], ROOT,
           'http://127.0.0.1:8800/api/health',
           lambda s: json.loads(s).get('service') == 'znt-business-api' and json.loads(s).get('ok'))
    ensure('detect-8810', 8810,
           [sys.executable, 'detect_bridge.py', '--profile', args.profile, '--host', '127.0.0.1', '--port', '8810'], ROOT,
           'http://127.0.0.1:8810/api/detect/health',
           lambda s: json.loads(s).get('service') == 'site-OpenRisk-detect-bridge' and json.loads(s).get('ok'))
    for name, port in [('pc-admin', 5173)] + ([('big-screen', 5174), ('mobile', 5175)] if args.displays else []):
        folder = APP / name
        ensure(f'{name}-{port}', port,
               [str(node), str(folder / 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1',
                '--port', str(port), '--strictPort'], folder, f'http://127.0.0.1:{port}/',
               lambda s: '/@vite/client' in s and '<html' in s.lower())
    url = 'http://127.0.0.1:5173/login'
    print(f'READY: {url}\nLogin: admin / admin123\nLogs: {LOGS}', flush=True)
    if not args.no_browser:
        webbrowser.open(url)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'\n[ERROR] {exc}', file=sys.stderr, flush=True)
        sys.exit(1)
