from __future__ import annotations

import argparse
import getpass
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from collections.abc import Callable, Sequence
from pathlib import Path

from backend.app.core.config import get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_PORT = 8501
PORT_SEARCH_LIMIT = 20
STARTUP_TIMEOUT_SECONDS = 30


class LauncherError(RuntimeError):
    """Erro esperado durante a inicialização local."""


def ensure_env_file(project_root: Path = PROJECT_ROOT) -> Path:
    env_path = project_root / ".env"
    if not env_path.exists():
        shutil.copyfile(project_root / ".env.example", env_path)
    return env_path


def configure_google_api_key(
    project_root: Path = PROJECT_ROOT,
    *,
    interactive: bool | None = None,
    prompt: Callable[[str], str] = getpass.getpass,
) -> bool:
    env_path = ensure_env_file(project_root)
    configured_key = (
        os.environ.get("GOOGLE_PLACES_API_KEY")
        or _read_env_value(env_path, "GOOGLE_PLACES_API_KEY")
    )
    if configured_key and configured_key.strip():
        os.environ["GOOGLE_PLACES_API_KEY"] = configured_key.strip()
        return True

    if interactive is None:
        interactive = sys.stdin.isatty()
    if not interactive:
        return False

    print("\nConfiguração inicial")
    print(
        "A busca precisa de uma chave Google com as APIs Places e "
        "Geocoding habilitadas."
    )
    key = prompt("Cole a GOOGLE_PLACES_API_KEY (a entrada ficará oculta): ")
    if not key.strip():
        return False

    _write_env_value(env_path, "GOOGLE_PLACES_API_KEY", key.strip())
    os.environ["GOOGLE_PLACES_API_KEY"] = key.strip()
    print("Chave salva localmente no arquivo .env.")
    return True


def is_port_available(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host, port))
    except OSError:
        return False
    return True


def find_available_port(
    host: str,
    preferred_port: int,
    *,
    attempts: int = PORT_SEARCH_LIMIT,
    excluded_ports: set[int] | None = None,
) -> int:
    excluded_ports = excluded_ports or set()
    for port in range(preferred_port, preferred_port + attempts):
        if port not in excluded_ports and is_port_available(host, port):
            return port
    raise LauncherError(
        f"Nenhuma porta livre encontrada entre {preferred_port} e "
        f"{preferred_port + attempts - 1}."
    )


def build_backend_command(host: str, port: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]


def build_streamlit_command(host: str, port: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "ui/streamlit_app.py",
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]


def wait_for_url(
    url: str,
    process: subprocess.Popen[bytes],
    *,
    timeout_seconds: float = STARTUP_TIMEOUT_SECONDS,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise LauncherError(
                f"Um componente encerrou antes de responder em {url}."
            )
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    raise LauncherError(f"Tempo limite ao aguardar {url}.")


def stop_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def run_application(*, open_browser: bool = True) -> None:
    os.chdir(PROJECT_ROOT)
    if not configure_google_api_key():
        raise LauncherError(
            "A chave Google não foi configurada. Execute novamente em um "
            "terminal interativo ou preencha GOOGLE_PLACES_API_KEY no .env."
        )

    get_settings.cache_clear()
    settings = get_settings()
    host = settings.app_host
    backend_port = find_available_port(host, settings.app_port)
    streamlit_port = find_available_port(
        host,
        STREAMLIT_PORT,
        excluded_ports={backend_port},
    )

    if backend_port != settings.app_port:
        print(
            f"Porta {settings.app_port} ocupada; a API usará "
            f"{backend_port}."
        )
    if streamlit_port != STREAMLIT_PORT:
        print(
            f"Porta {STREAMLIT_PORT} ocupada; a interface usará "
            f"{streamlit_port}."
        )

    backend_process: subprocess.Popen[bytes] | None = None
    streamlit_process: subprocess.Popen[bytes] | None = None
    backend_url = f"http://{host}:{backend_port}"
    streamlit_url = f"http://{host}:{streamlit_port}"

    try:
        print("Iniciando API...")
        backend_process = subprocess.Popen(
            build_backend_command(host, backend_port),
            cwd=PROJECT_ROOT,
        )
        wait_for_url(f"{backend_url}/api/health", backend_process)

        print("Iniciando interface...")
        streamlit_process = subprocess.Popen(
            build_streamlit_command(host, streamlit_port),
            cwd=PROJECT_ROOT,
        )
        wait_for_url(streamlit_url, streamlit_process)

        print(f"ProspectAI disponível em {streamlit_url}")
        print(f"Documentação da API em {backend_url}/docs")
        print("Pressione Ctrl+C para encerrar.")
        if open_browser and not webbrowser.open(streamlit_url):
            print(f"Não foi possível abrir o navegador. Acesse {streamlit_url}")

        while True:
            if backend_process.poll() is not None:
                raise LauncherError("A API foi encerrada inesperadamente.")
            if streamlit_process.poll() is not None:
                raise LauncherError(
                    "A interface foi encerrada inesperadamente."
                )
            time.sleep(0.5)
    finally:
        print("\nEncerrando ProspectAI...")
        stop_process(streamlit_process)
        stop_process(backend_process)


def _read_env_value(env_path: Path, key: str) -> str:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == key:
            return value.strip()
    return ""


def _write_env_value(env_path: Path, key: str, value: str) -> None:
    lines = env_path.read_text(encoding="utf-8").splitlines()
    replacement = f"{key}={value}"
    updated = False
    for index, line in enumerate(lines):
        name, separator, _ = line.partition("=")
        if separator and name.strip() == key:
            lines[index] = replacement
            updated = True
            break
    if not updated:
        lines.append(replacement)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inicia o ProspectAI.")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Não abrir o navegador automaticamente.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        run_application(open_browser=not args.no_browser)
    except KeyboardInterrupt:
        print("\nProspectAI encerrado pelo usuário.")
    except LauncherError as exc:
        print(f"\nNão foi possível iniciar o ProspectAI: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
