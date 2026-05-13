from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_DIR = ROOT_DIR / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
BACKEND_RUNTIME_REQUIREMENTS = BACKEND_DIR / "requirements-runtime.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inicializa o backend Flask e o frontend Vite do HydraSensor."
    )
    parser.add_argument("--install", action="store_true", help="Cria o .venv e instala dependencias.")
    parser.add_argument("--backend-only", action="store_true", help="Inicializa apenas o backend.")
    parser.add_argument("--frontend-only", action="store_true", help="Inicializa apenas o frontend.")
    parser.add_argument("--backend-host", default="127.0.0.1", help="Host do backend.")
    parser.add_argument("--backend-port", type=int, default=5000, help="Porta do backend.")
    parser.add_argument("--frontend-host", default="127.0.0.1", help="Host do frontend.")
    parser.add_argument("--frontend-port", type=int, default=5173, help="Porta do frontend.")
    return parser.parse_args()


def python_command() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)

    return sys.executable


def npm_command() -> str:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        raise RuntimeError("Nao foi possivel localizar o npm no PATH.")
    return npm


def ensure_virtualenv() -> None:
    if VENV_PYTHON.exists():
        return

    print("Criando ambiente virtual em .venv...")
    subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)],
        cwd=str(ROOT_DIR),
        check=True,
    )


def run_installers() -> None:
    ensure_virtualenv()

    print("Instalando dependencias do backend...")
    subprocess.run(
        [python_command(), "-m", "pip", "install", "-r", str(BACKEND_RUNTIME_REQUIREMENTS)],
        cwd=str(ROOT_DIR),
        check=True,
    )

    print("Instalando dependencias do frontend...")
    subprocess.run(
        [npm_command(), "install"],
        cwd=str(FRONTEND_DIR),
        check=True,
    )


def backend_dependencies_ready() -> bool:
    if not VENV_PYTHON.exists():
        return False

    check = subprocess.run(
        [python_command(), "-c", "import flask, pubnub"],
        cwd=str(ROOT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return check.returncode == 0


def preflight_checks(start_backend: bool, start_frontend: bool) -> None:
    if start_backend:
        if not VENV_PYTHON.exists():
            raise RuntimeError(
                "Ambiente virtual ausente em `.venv`. Execute `python main.py --install`."
            )

        if not backend_dependencies_ready():
            raise RuntimeError(
                "Dependencias Python ausentes no `.venv`. Execute `python main.py --install`."
            )

    if start_frontend and not (FRONTEND_DIR / "node_modules").exists():
        raise RuntimeError(
            "Dependencias do frontend ausentes em `frontend/node_modules`. "
            "Execute `python main.py --install`."
        )


def stream_process_output(label: str, process: subprocess.Popen[str]) -> None:
    assert process.stdout is not None

    for line in process.stdout:
        print(f"[{label}] {line}", end="")


def start_process(label: str, command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    threading.Thread(
        target=stream_process_output,
        args=(label, process),
        daemon=True,
    ).start()

    return process


def stop_process(process: subprocess.Popen[str], label: str) -> None:
    if process.poll() is not None:
        return

    print(f"Encerrando {label}...")
    process.terminate()

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print(f"Forcando encerramento de {label}...")
        process.kill()
        process.wait(timeout=5)


def proxy_backend_url(backend_host: str, backend_port: int) -> str:
    if backend_host in {"0.0.0.0", "::"}:
        return f"http://127.0.0.1:{backend_port}"

    return f"http://{backend_host}:{backend_port}"


def main() -> int:
    args = parse_args()

    if args.backend_only and args.frontend_only:
        print("Escolha apenas uma entre `--backend-only` e `--frontend-only`.")
        return 2

    start_backend = not args.frontend_only
    start_frontend = not args.backend_only

    if args.install:
        run_installers()

    try:
        preflight_checks(start_backend, start_frontend)
    except RuntimeError as exc:
        print(exc)
        return 1

    processes: list[tuple[str, subprocess.Popen[str]]] = []

    backend_url = f"http://{args.backend_host}:{args.backend_port}"
    frontend_url = f"http://{args.frontend_host}:{args.frontend_port}"

    if start_backend:
        backend_env = os.environ.copy()
        backend_env["PYTHONUNBUFFERED"] = "1"
        backend_env["APP_HOST"] = args.backend_host
        backend_env["APP_PORT"] = str(args.backend_port)
        backend_env["APP_DEBUG"] = "false"
        backend_env["APP_USE_RELOADER"] = "false"

        processes.append((
            "backend",
            start_process(
                "backend",
                [python_command(), "app.py"],
                BACKEND_DIR,
                backend_env,
            ),
        ))

    if start_frontend:
        frontend_env = os.environ.copy()
        frontend_env["VITE_API_PROXY_TARGET"] = proxy_backend_url(
            args.backend_host,
            args.backend_port,
        )

        processes.append((
            "frontend",
            start_process(
                "frontend",
                [
                    npm_command(),
                    "run",
                    "dev",
                    "--",
                    "--host",
                    args.frontend_host,
                    "--port",
                    str(args.frontend_port),
                ],
                FRONTEND_DIR,
                frontend_env,
            ),
        ))

    print("HydraSensor em inicializacao:")
    if start_backend:
        print(f"- Backend: {backend_url}")
    if start_frontend:
        print(f"- Frontend: {frontend_url}")

    exit_code = 0

    try:
        while True:
            for label, process in processes:
                process_exit_code = process.poll()

                if process_exit_code is not None:
                    print(f"{label} finalizado com codigo {process_exit_code}.")
                    exit_code = process_exit_code
                    return exit_code

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Interrupcao recebida. Encerrando processos...")
        return exit_code
    finally:
        for label, process in reversed(processes):
            stop_process(process, label)


if __name__ == "__main__":
    raise SystemExit(main())
