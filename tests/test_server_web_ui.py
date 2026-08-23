"""Unit tests for Proton Web UI and Developer/Workspace/Terminal API routes."""

import pytest
from fastapi.testclient import TestClient
from proton.server.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Fixture providing TestClient with temp workspace."""
    monkeypatch.setenv("PROTON_HOME", str(tmp_path / ".proton"))
    app = create_app()
    return TestClient(app)


def test_spa_root_and_static_serving(client):
    """Test that visiting / or /chat serves the SPA index.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Proton" in response.text

    chat_resp = client.get("/chat")
    assert chat_resp.status_code == 200
    assert "Proton" in chat_resp.text


def test_developer_status_and_logs(client):
    """Test developer status and logs API."""
    status_resp = client.get("/v1/developer/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "running"
    assert "reachability" in data
    assert "hardware" in data

    logs_resp = client.get("/v1/developer/logs")
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert "logs" in logs


def test_workspace_tree_and_file_crud(client, tmp_path, monkeypatch):
    """Test workspace file explorer and write/read/diff APIs."""
    # Write a test file
    write_resp = client.post(
        "/v1/workspace/file",
        json={"path": "test_script.py", "content": "print('Hello from Proton Web UI')\n"},
    )
    assert write_resp.status_code == 200
    assert write_resp.json()["success"] is True

    # Read back file
    read_resp = client.get("/v1/workspace/file?path=test_script.py")
    assert read_resp.status_code == 200
    assert read_resp.json()["content"] == "print('Hello from Proton Web UI')\n"

    # Search
    search_resp = client.post("/v1/workspace/search", json={"query": "Hello from Proton"})
    assert search_resp.status_code == 200
    assert len(search_resp.json()["results"]) > 0

    # Diff
    diff_resp = client.post(
        "/v1/workspace/diff",
        json={"path": "test_script.py", "modified_content": "print('Modified line')\n"},
    )
    assert diff_resp.status_code == 200
    assert diff_resp.json()["has_changes"] is True


def test_terminal_run_and_status(client):
    """Test terminal runner and process inspection."""
    run_resp = client.post("/v1/terminal/run", json={"command": "echo 'Proton Terminal OK'"})
    assert run_resp.status_code == 200
    data = run_resp.json()
    assert data["success"] is True
    assert "Proton Terminal OK" in data["stdout"]

    status_resp = client.get("/v1/terminal/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["is_running"] is False
