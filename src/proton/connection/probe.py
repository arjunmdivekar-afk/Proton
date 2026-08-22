"""Connection probe utility to test connectivity and discover models."""

import asyncio
import socket
import time
from typing import List, Tuple, Optional
import httpx

from proton.connection.schema import ConnectionProfile, ConnectionTestResult, ConnectionStatus
from proton.core.types import ModelInfo, ModelCapabilities


async def test_tcp_connectivity(host: str, port: int, timeout: float = 3.0) -> Tuple[bool, Optional[str]]:
    """Test raw TCP connection to host:port."""
    loop = asyncio.get_running_loop()
    try:
        # Resolve hostname or IP
        await loop.run_in_executor(
            None,
            lambda: socket.create_connection((host, port), timeout=timeout).close()
        )
        return True, None
    except socket.timeout:
        return False, "Connection timed out. Target host or port unreachable."
    except ConnectionRefusedError:
        return False, "Connection refused. Server is not running or not listening on this port/interface."
    except socket.gaierror:
        return False, f"Could not resolve host: {host}"
    except Exception as e:
        return False, str(e)


async def probe_connection(profile: ConnectionProfile) -> ConnectionTestResult:
    """Perform comprehensive health probe, latency test, and model discovery."""
    result = ConnectionTestResult(
        success=False,
        connection_id=profile.id,
        host=profile.host,
        port=profile.port,
        base_url=profile.base_url,
    )

    # 1. TCP Check
    tcp_ok, tcp_err = await test_tcp_connectivity(profile.host, profile.port, timeout=profile.timeout_seconds / 2)
    result.tcp_reachable = tcp_ok
    if not tcp_ok:
        result.error_message = tcp_err
        result.remediation_advice = (
            f"1. Check if the AI server (LM Studio / Ollama) is running on {profile.host}:{profile.port}.\n"
            f"2. Ensure LM Studio server is bound to 0.0.0.0 (or local network IP), not just 127.0.0.1.\n"
            f"3. Verify your LAN firewall allows inbound connections on port {profile.port}."
        )
        return result

    # 2. HTTP & Models endpoint probe
    headers = {"Accept": "application/json"}
    if profile.api_key:
        headers["Authorization"] = f"Bearer {profile.api_key}"
    headers.update(profile.custom_headers)

    models_url = f"{profile.base_url}/models"
    t_start = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=profile.timeout_seconds) as client:
            resp = await client.get(models_url, headers=headers)
            latency = (time.perf_counter() - t_start) * 1000.0
            result.latency_ms = round(latency, 2)
            result.http_reachable = True

            if resp.status_code == 200:
                result.models_endpoint_reachable = True
                data = resp.json()
                models_list: List[str] = []

                # OpenAI / LM Studio / Ollama v1 format: {"data": [{"id": "model_id", ...}]}
                if "data" in data and isinstance(data["data"], list):
                    for item in data["data"]:
                        if isinstance(item, dict) and "id" in item:
                            models_list.append(item["id"])
                elif "models" in data and isinstance(data["models"], list):
                    # Ollama native format: {"models": [{"name": "qwen2.5:latest"}]}
                    for item in data["models"]:
                        if isinstance(item, dict) and "name" in item:
                            models_list.append(item["name"])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item:
                            models_list.append(item["id"])

                result.discovered_models = models_list
                result.success = True
            elif resp.status_code == 401 or resp.status_code == 403:
                result.error_message = f"Authentication required (HTTP {resp.status_code})."
                result.remediation_advice = "Please provide an API key for this connection."
            else:
                result.error_message = f"HTTP {resp.status_code}: {resp.text[:200]}"
                result.remediation_advice = f"Endpoint {models_url} returned unexpected status code."

    except httpx.ConnectTimeout:
        result.error_message = "HTTP request timed out."
        result.remediation_advice = "The server is taking too long to respond. Check server load or increase timeout."
    except httpx.ConnectError as e:
        result.error_message = f"HTTP connect error: {e}"
        result.remediation_advice = "Failed to establish HTTP connection. Verify URL protocol (http vs https)."
    except Exception as e:
        result.error_message = f"Unexpected probe error: {e}"

    return result
