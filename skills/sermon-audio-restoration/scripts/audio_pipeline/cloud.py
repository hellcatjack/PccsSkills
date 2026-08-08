from __future__ import annotations

import hashlib
import os
from pathlib import Path
import time
from typing import Any

import requests
import soundfile as sf

from .models import CloudRequest
from .policy import (
    PolicyError,
    assert_cloud_free_allowed,
    assert_safe_output,
    validate_auphonic_algorithms,
)


USER_URL = "https://auphonic.com/api/user.json"
SIMPLE_URL = "https://auphonic.com/api/simple/productions.json"


class CloudProcessingError(RuntimeError):
    pass


def _response_data(response: Any) -> Any:
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or "data" not in payload:
        raise CloudProcessingError("Auphonic response does not contain data")
    return payload["data"]


def _eligible_account(session: Any, headers: dict[str, str], duration_hours: float) -> None:
    account = _response_data(session.get(USER_URL, headers=headers, timeout=30))
    try:
        recurring_credits = float(account["recurring_credits"])
        recurring_cap = float(account["recharge_recurring_credits"])
    except (KeyError, TypeError, ValueError) as error:
        raise PolicyError("Auphonic free recurring-credit state is unknown") from error
    assert_cloud_free_allowed(
        duration_hours=duration_hours,
        recurring_credits=recurring_credits,
        recurring_cap=recurring_cap,
    )


def _algorithm_fields(request: CloudRequest) -> dict[str, str]:
    algorithms: dict[str, Any] = {
        "leveler": True,
        "normloudness": True,
        "silence_cutter": False,
        "filler_cutter": False,
        "cough_cutter": False,
        "music_cutter": False,
    }
    validate_auphonic_algorithms(algorithms)
    return {
        "leveler": "true",
        "levelerstrength": "70",
        "compressor_speech": "medium",
        "normloudness": "true",
        "loudnesstarget": str(request.target_lufs),
        "maxpeak": str(request.true_peak_dbtp),
        "loudnessmethod": "dialog",
        "silence_cutter": "false",
        "filler_cutter": "false",
        "cough_cutter": "false",
        "music_cutter": "false",
        "cut_mode": "export_uncut_audio",
        "output_files": "wav",
        "action": "start",
    }


def _find_wav_output(production: dict[str, Any]) -> dict[str, Any]:
    for output in production.get("output_files", []):
        if output.get("format") in {"wav", "wav-24bit"} and output.get("download_url"):
            return output
    raise CloudProcessingError("Auphonic production has no lossless WAV result")


def run_auphonic_free(
    request: CloudRequest,
    *,
    session: Any | None = None,
    api_key: str | None = None,
    poll_interval: float = 5.0,
    max_polls: int = 120,
) -> Path:
    if request.cloud_mode != "auphonic-free":
        raise PolicyError("Cloud processing was not explicitly enabled")
    if not request.upload_consent:
        raise PolicyError("Cloud upload requires explicit user consent")
    token = api_key or os.environ.get("AUPHONIC_API_KEY")
    if not token:
        raise PolicyError("AUPHONIC_API_KEY is not configured")

    source = Path(request.input_path).resolve()
    output = Path(request.output_path).resolve()
    assert_safe_output(source, output)
    if not source.is_file():
        raise PolicyError(f"Cloud input does not exist: {source}")

    client = session or requests.Session()
    headers = {"Authorization": f"bearer {token}"}
    _eligible_account(client, headers, request.duration_hours)
    data = _algorithm_fields(request)

    with source.open("rb") as media:
        creation = _response_data(
            client.post(
                SIMPLE_URL,
                headers=headers,
                data=data,
                files={"input_file": (source.name, media, "audio/wav")},
                timeout=300,
            )
        )
    production_id = creation.get("uuid") if isinstance(creation, dict) else None
    if not production_id:
        raise CloudProcessingError("Auphonic did not return a production UUID")

    status_url = f"https://auphonic.com/api/production/{production_id}/status.json"
    production: dict[str, Any] | None = None
    for _ in range(max_polls):
        status = _response_data(client.get(status_url, headers=headers, timeout=30))
        if not isinstance(status, dict):
            raise CloudProcessingError("Auphonic returned an invalid status payload")
        status_code = int(status.get("status", -1))
        if status_code == 3:
            production = status
            break
        if status_code < 0 or status_code >= 4:
            raise CloudProcessingError(
                f"Auphonic production failed: {status.get('status_string', status_code)}"
            )
        if poll_interval > 0:
            time.sleep(poll_interval)
    if production is None:
        raise CloudProcessingError("Auphonic production did not finish within the poll limit")

    if not production.get("output_files"):
        detail_url = f"https://auphonic.com/api/production/{production_id}.json"
        detail = _response_data(client.get(detail_url, headers=headers, timeout=30))
        if not isinstance(detail, dict):
            raise CloudProcessingError("Auphonic production detail is invalid")
        production = detail

    output_record = _find_wav_output(production)
    download = client.get(output_record["download_url"], headers=headers, timeout=300)
    download.raise_for_status()
    content = download.content
    expected_checksum = output_record.get("checksum")
    if expected_checksum:
        actual_checksum = hashlib.md5(content).hexdigest()
        if actual_checksum.casefold() != str(expected_checksum).casefold():
            raise CloudProcessingError("Auphonic result checksum mismatch")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f"{output.name}.download")
    temporary.write_bytes(content)
    source_info = sf.info(source)
    result_info = sf.info(temporary)
    if (
        source_info.frames != result_info.frames
        or source_info.samplerate != result_info.samplerate
        or source_info.channels != result_info.channels
    ):
        raise PolicyError(
            "Auphonic result changed sample count, sample rate, or channel layout"
        )
    os.replace(temporary, output)
    return output
