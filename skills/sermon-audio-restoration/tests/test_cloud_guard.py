from dataclasses import replace
import hashlib
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from audio_pipeline.cloud import run_auphonic_free
from audio_pipeline.models import CloudRequest
from audio_pipeline.policy import PolicyError


class FakeResponse:
    def __init__(self, payload=None, *, content=b""):
        self._payload = payload
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, account, status=None, download=b""):
        self.account = account
        self.status = status
        self.download = download
        self.calls = []
        self.upload_data = None

    def get(self, url, **kwargs):
        self.calls.append(("GET", url))
        if url.endswith("/api/user.json"):
            return FakeResponse({"data": self.account})
        if url.endswith("/status.json"):
            return FakeResponse({"data": self.status})
        return FakeResponse(content=self.download)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url))
        self.upload_data = kwargs.get("data")
        return FakeResponse({"data": {"uuid": "free-production-id"}})


@pytest.fixture()
def cloud_request(tmp_path: Path) -> CloudRequest:
    source = tmp_path / "input.wav"
    time = np.arange(48000, dtype=np.float64) / 48000
    sf.write(source, 0.1 * np.sin(2 * np.pi * 440 * time), 48000, subtype="FLOAT")
    return CloudRequest(
        input_path=str(source),
        duration_hours=1.0 / 3600.0,
        target_lufs=-16.0,
        true_peak_dbtp=-1.5,
        cloud_mode="auphonic-free",
        upload_consent=True,
        output_path=str(tmp_path / "output.wav"),
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"cloud_mode": "off"},
        {"upload_consent": False},
    ],
)
def test_cloud_requires_explicit_mode_and_consent(cloud_request, changes):
    session = FakeSession({})
    with pytest.raises(PolicyError):
        run_auphonic_free(
            replace(cloud_request, **changes),
            session=session,
            api_key="test-key",
        )
    assert session.calls == []


def test_cloud_requires_api_key_before_network(cloud_request, monkeypatch):
    monkeypatch.delenv("AUPHONIC_API_KEY", raising=False)
    session = FakeSession({})
    with pytest.raises(PolicyError):
        run_auphonic_free(cloud_request, session=session, api_key=None)
    assert session.calls == []


@pytest.mark.parametrize(
    "account",
    [
        {
            "recurring_credits": 0.0,
            "recharge_recurring_credits": 2.0,
            "onetime_credits": 100.0,
        },
        {
            "recurring_credits": 5.0,
            "recharge_recurring_credits": 10.0,
            "onetime_credits": 0.0,
        },
    ],
)
def test_paid_or_insufficient_credit_state_never_uploads(cloud_request, account):
    session = FakeSession(account)
    with pytest.raises(PolicyError):
        run_auphonic_free(cloud_request, session=session, api_key="test-key")
    assert all(method != "POST" for method, _url in session.calls)


def test_free_request_disables_all_cutters_and_preserves_samples(cloud_request):
    source_bytes = Path(cloud_request.input_path).read_bytes()
    checksum = hashlib.md5(source_bytes).hexdigest()
    status = {
        "status": 3,
        "status_string": "Done",
        "output_files": [
            {
                "format": "wav",
                "download_url": "https://download.test/result.wav",
                "checksum": checksum,
            }
        ],
    }
    session = FakeSession(
        {
            "recurring_credits": 1.5,
            "recharge_recurring_credits": 2.0,
            "onetime_credits": 0.0,
        },
        status=status,
        download=source_bytes,
    )

    output = run_auphonic_free(
        cloud_request,
        session=session,
        api_key="test-key",
        poll_interval=0.0,
    )

    assert output == Path(cloud_request.output_path)
    assert sf.info(output).frames == sf.info(cloud_request.input_path).frames
    assert session.upload_data["silence_cutter"] == "false"
    assert session.upload_data["filler_cutter"] == "false"
    assert session.upload_data["cough_cutter"] == "false"
    assert session.upload_data["music_cutter"] == "false"
    assert session.upload_data["leveler"] == "true"
    assert session.upload_data["normloudness"] == "true"
    assert session.upload_data["loudnesstarget"] == "-16.0"
    assert session.upload_data["maxpeak"] == "-1.5"
