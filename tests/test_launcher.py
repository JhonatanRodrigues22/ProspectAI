import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from launcher.main import (
    LauncherError,
    build_backend_command,
    build_streamlit_command,
    configure_google_api_key,
    ensure_env_file,
    find_available_port,
    is_port_available,
    main,
    stop_process,
)


def _write_env_example(project_root: Path) -> None:
    (project_root / ".env.example").write_text(
        "APP_NAME=ProspectAI\nGOOGLE_PLACES_API_KEY=\n",
        encoding="utf-8",
    )


def test_ensure_env_file_creates_copy(tmp_path: Path) -> None:
    _write_env_example(tmp_path)

    env_path = ensure_env_file(tmp_path)

    assert env_path.read_text(encoding="utf-8").startswith(
        "APP_NAME=ProspectAI"
    )


def test_ensure_env_file_preserves_existing_file(tmp_path: Path) -> None:
    _write_env_example(tmp_path)
    env_path = tmp_path / ".env"
    env_path.write_text("CUSTOM=value\n", encoding="utf-8")

    ensure_env_file(tmp_path)

    assert env_path.read_text(encoding="utf-8") == "CUSTOM=value\n"


def test_configure_google_api_key_accepts_existing_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    _write_env_example(tmp_path)
    (tmp_path / ".env").write_text(
        "GOOGLE_PLACES_API_KEY=already-configured\n",
        encoding="utf-8",
    )
    prompt = Mock()

    configured = configure_google_api_key(
        tmp_path,
        interactive=True,
        prompt=prompt,
    )

    assert configured is True
    prompt.assert_not_called()


def test_configure_google_api_key_prompts_and_saves_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    _write_env_example(tmp_path)

    configured = configure_google_api_key(
        tmp_path,
        interactive=True,
        prompt=lambda _: "new-secret-key",
    )

    assert configured is True
    assert "GOOGLE_PLACES_API_KEY=new-secret-key" in (
        tmp_path / ".env"
    ).read_text(encoding="utf-8")


def test_configure_google_api_key_rejects_empty_noninteractive_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    _write_env_example(tmp_path)

    assert configure_google_api_key(tmp_path, interactive=False) is False


def test_is_port_available_detects_occupied_port() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        port = occupied.getsockname()[1]

        assert is_port_available("127.0.0.1", port) is False


def test_find_available_port_skips_occupied_port() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        port = occupied.getsockname()[1]

        selected = find_available_port("127.0.0.1", port, attempts=2)

    assert selected == port + 1


def test_find_available_port_raises_when_range_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "launcher.main.is_port_available",
        lambda host, port: False,
    )

    with pytest.raises(LauncherError):
        find_available_port("127.0.0.1", 8000, attempts=2)


def test_find_available_port_respects_excluded_ports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "launcher.main.is_port_available",
        lambda host, port: True,
    )

    selected = find_available_port(
        "127.0.0.1",
        8501,
        attempts=2,
        excluded_ports={8501},
    )

    assert selected == 8502


def test_launcher_commands_use_current_python_and_selected_ports() -> None:
    backend = build_backend_command("127.0.0.1", 8010)
    streamlit = build_streamlit_command("127.0.0.1", 8510)

    assert backend[0] == sys.executable
    assert backend[-1] == "8010"
    assert streamlit[0] == sys.executable
    assert "ui/streamlit_app.py" in streamlit
    assert "8510" in streamlit


def test_stop_process_terminates_running_process() -> None:
    process = Mock(spec=subprocess.Popen)
    process.poll.return_value = None

    stop_process(process)

    process.terminate.assert_called_once_with()
    process.wait.assert_called_once_with(timeout=5)


def test_main_reports_expected_launcher_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(*, open_browser: bool) -> None:
        raise LauncherError("falha simulada")

    monkeypatch.setattr("launcher.main.run_application", fail)

    exit_code = main(["--no-browser"])

    assert exit_code == 1
    assert "falha simulada" in capsys.readouterr().out
