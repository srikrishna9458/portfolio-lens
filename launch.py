"""Start Portfolio Lens locally, with useful errors and a movable project folder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / 'runtime'
URL = 'http://127.0.0.1:8765/'


def health(port):
    path = 'api/health' if port == 8765 else 'health'
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/{path}', timeout=1) as response:
            data = json.load(response)
        return data.get('status') == 'ok' and (port != 8765 or data.get('app') == 'Portfolio Lens')
    except (OSError, ValueError):
        return False


def port_busy(port):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=1):
            return True
    except OSError:
        return False


def start(args, name):
    with (RUNTIME / (name + '.log')).open('ab') as log:
        process = subprocess.Popen(
            args, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
    (RUNTIME / (name + '.pid')).write_text(str(process.pid), encoding='ascii')
    return process


def wait_ready(port, process, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if health(port):
            return True
        if process is not None and process.poll() is not None:
            return False
        time.sleep(0.5)
    return health(port)


def configure_powerbi():
    """Update only the data-folder parameter; preserve the report and other settings."""
    model_path = ROOT / 'powerbi' / 'PortfolioLens.SemanticModel' / 'model.bim'
    if not model_path.exists():
        return
    model = json.loads(model_path.read_text(encoding='utf-8-sig'))
    folder = (ROOT / 'powerbi' / 'exports').as_posix() + '/'
    value = '"' + folder.replace('"', '""') + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
    for expression in model.get('model', {}).get('expressions', []):
        if expression.get('name') == 'DataFolder':
            if expression.get('expression') != value:
                expression['expression'] = value
                pending = model_path.with_suffix('.bim.tmp')
                pending.write_text(json.dumps(model, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                pending.replace(model_path)
            return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--no-model', action='store_true', help='Start the dashboard without the optional AI service.')
    parser.add_argument('--stay-running', action='store_true', help='Keep a terminal session attached to services started here.')
    args = parser.parse_args()
    RUNTIME.mkdir(exist_ok=True)
    try:
        configure_powerbi()
    except (OSError, ValueError) as error:
        print(f'Power BI folder update could not finish: {error}\nYou can set DataFolder in Power Query manually.')

    processes = []
    if not health(8765):
        if port_busy(8765):
            raise RuntimeError('Port 8765 is in use by another application. Close that application and start Portfolio Lens again.')
        print('Starting your dashboard...', flush=True)
        dashboard = start([sys.executable, '-I', str(ROOT / 'app.py'), '--no-browser'], 'dashboard')
        processes.append(dashboard)
        if not wait_ready(8765, dashboard, 20):
            raise RuntimeError('The dashboard did not start. Open runtime/dashboard.log for the error details.')
    print(f'Dashboard ready: {URL}', flush=True)
    if not args.no_browser:
        webbrowser.open(URL)

    binary = RUNTIME / 'llama' / 'llama-server.exe'
    model = RUNTIME / 'model.gguf'
    if not args.no_model and binary.exists() and model.exists():
        if health(8766):
            print('Local AI is ready.', flush=True)
        elif port_busy(8766):
            print('The AI port is busy. The dashboard and evidence search still work.', flush=True)
        else:
            key = RUNTIME / 'model.key'
            if not key.exists():
                key.write_text(secrets.token_urlsafe(32), encoding='ascii')
            print('Loading the optional local AI model...', flush=True)
            try:
                process = start([
                    str(binary), '-m', str(model), '--host', '127.0.0.1', '--port', '8766',
                    '-c', '8192', '-t', '4', '--parallel', '1', '--no-webui',
                    '--cors-origins', URL.rstrip('/'), '--no-cors-credentials',
                    '--api-key-file', str(key),
                ], 'model')
                processes.append(process)
                if wait_ready(8766, process, 45):
                    print('Local AI is ready.', flush=True)
                else:
                    print('The model is not ready yet. Evidence search works without it; see runtime/model.log.', flush=True)
            except OSError as error:
                print(f'The optional AI service could not start: {error}\nThe dashboard and evidence search still work.', flush=True)
    elif not args.no_model:
        print('AI files are absent. The dashboard and evidence search are ready.', flush=True)

    if args.stay_running and processes:
        print('Keeping this session connected. Press Ctrl+C to stop services started by this session.', flush=True)
        try:
            while any(process.poll() is None for process in processes):
                time.sleep(1)
        except KeyboardInterrupt:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
            for process in processes:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        message = f'Portfolio Lens could not start: {error}'
        print(message, file=sys.stderr, flush=True)
        try:
            RUNTIME.mkdir(exist_ok=True)
            (RUNTIME / 'launcher-error.txt').write_text(message + '\n', encoding='utf-8')
        except OSError:
            pass
        raise SystemExit(1)
