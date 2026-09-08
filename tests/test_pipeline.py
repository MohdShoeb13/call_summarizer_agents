import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import AuthenticationError

from backend.agents.intake_agent import intake, MAX_BYTES
from backend.agents.quality_score_agent import validate_evidence
from backend.agents.routing_agent import process
from backend.config import Settings
from backend.models import CallResult, Summary, Quality, Dimension
from backend.provider import OpenAIProvider, ProviderFailure
from backend.samples import ReplayProvider, samples
from backend.store import Store


@pytest.fixture
def store(tmp_path):
    return Store(str(tmp_path / "calls.db"))


def new_call(id="test"):
    return CallResult(id=id, title="Test call", created_at="2026-09-06T00:00:00Z", status="queued", stage="intake")


@pytest.mark.parametrize("filename,body", [("a.exe",b"hello"),("a.txt",b""),("a.txt",b" \n"),("a.json",b"{"),("a.json",b"[]"),("a.json",b'{"segments":[]}'),("a.json",b'{"segments":[{"text":" "}]}'),("a.mp3",b"not audio"),("a.wav",b"RIFF1234XXXX"),("a.txt",b"\xff"),("a.txt",b"x"*100001)], ids=["extension","empty","blank","invalid-json","json-array","no-segments","blank-segment","fake-mp3","fake-wav","encoding","long-text"])
def test_invalid_intake(filename, body):
    with pytest.raises(ValueError):
        intake(filename, body)


def test_oversized():
    with pytest.raises(ValueError):
        intake("a.mp3", b"ID3" + b"x"*MAX_BYTES)


def test_json_and_unknown_speakers():
    audio, rows = intake("a.json", json.dumps({"segments":[{"speaker":"Agent","text":"Hello"},{"text":"Hi"}]}).encode())
    assert not audio and [r.id for r in rows] == [1,2]
    assert rows[1].speaker == "Unknown"
    assert intake("a.json",b'{"transcript":"Customer: Help"}')[1][0].speaker == "Customer"


@pytest.mark.parametrize("sample", samples(), ids=lambda s:s["id"])
def test_all_samples_complete(sample, store):
    call = new_call(sample["id"])
    with patch("backend.samples.time.sleep"):
        process(call, "sample.txt", sample["transcript"].encode(), ReplayProvider(sample, True), store)
    assert call.status == "completed", call.error
    assert call.summary.resolution == sample["expected"]["resolution"]
    assert len(call.quality.dimensions) == 4
    scores = [v for v in sample["scores"] if v is not None]
    assert call.overall_score == round(sum(scores)/len(scores),2)
    assert any("transcription skipped" in e.message for e in call.events)
    assert any("fallback" in e.message for e in call.events)


def test_audio_branch_and_partial_failure(store):
    sample = samples()[0]
    provider = MagicMock()
    provider.transcribe.return_value = sample["transcript"]
    provider.generate.side_effect = [Summary.model_validate(sample["expected"]),ProviderFailure("quality unavailable")]
    call = new_call()
    process(call,"test.wav",b"RIFF1234WAVEdata",provider,store)
    assert call.status == "failed" and call.summary and call.quality is None
    assert all(row.speaker == "Unknown" for row in call.transcript)
    assert store.get(call.id).summary == call.summary
    provider.transcribe.assert_called_once()


def test_evidence_and_rubric_validation():
    rows = intake("a.txt",b"Agent: I can help.")[1]
    with pytest.raises(ValueError):
        validate_evidence(Summary(issue="x",key_points=[],resolution="unknown",resolution_details="x",action_items=[],tags=[],evidence_ids=[999]),rows)
    duplicated = Quality(dimensions=[Dimension(name="tone",score=3,rationale="x",evidence_ids=[1]) for _ in range(4)])
    with pytest.raises(ValueError):
        validate_evidence(duplicated,rows)
    with pytest.raises(ValueError):
        Dimension(name="tone",score=6,rationale="x",evidence_ids=[1])


def test_fallback_and_bounded_attempts():
    sample=samples()[0]
    rows=intake("a.txt",sample["transcript"].encode())[1]
    primary, fallback = MagicMock(), MagicMock()
    primary.with_structured_output.return_value.invoke.side_effect=ValueError("invalid output")
    fallback.with_structured_output.return_value.invoke.return_value=Summary.model_validate(sample["expected"])
    config=Settings(openai_api_key="test",primary_model="primary",fallback_model="fallback")
    events=[]
    with patch("backend.provider.ChatOpenAI",side_effect=[primary,primary,fallback]) as factory,patch("backend.provider.time.sleep"):
        result=OpenAIProvider(config).generate(Summary,"prompt",rows,"summary",lambda *args:events.append(args))
    assert result.issue == sample["expected"]["issue"]
    assert factory.call_count == 3
    assert any("fallback" in e[1] for e in events)
    with patch("backend.provider.ChatOpenAI",return_value=primary) as factory,patch("backend.provider.time.sleep"):
        with pytest.raises(ProviderFailure):
            OpenAIProvider(config).generate(Summary,"prompt",rows,"summary",lambda *args:None)
    assert factory.call_count == 4


def test_authentication_does_not_retry():
    llm=MagicMock()
    llm.with_structured_output.return_value.invoke.side_effect=AuthenticationError("bad key",response=httpx.Response(401,request=httpx.Request("POST","https://example.test")),body=None)
    with patch("backend.provider.ChatOpenAI",return_value=llm) as factory:
        with pytest.raises(ProviderFailure,match="credentials"):
            OpenAIProvider(Settings(openai_api_key="test")).generate(Summary,"prompt",[],"summary",lambda *args:None)
    assert factory.call_count == 1


def test_history_isolation_and_restart(store):
    first, second = new_call("first"),new_call("second")
    first.status="completed"
    store.save(first);store.save(second)
    store.interrupt_pending()
    assert store.get("first").status == "completed"
    assert store.get("second").status == "interrupted"
    assert store.get("missing") is None
    assert len(store.list()) == 2
    # Connections are closed, including on Windows.
    from pathlib import Path
    Path(store.path).rename(Path(store.path).with_suffix(".renamed"))


@pytest.fixture
def client(tmp_path,monkeypatch):
    from backend.main import app,settings
    monkeypatch.setattr(settings,"database_path",str(tmp_path / "api.db"))
    monkeypatch.setattr(settings,"openai_api_key","")
    with TestClient(app) as c:
        yield c


def test_api_validation_and_secret_boundary(client):
    assert client.get("/api/health").json() == {"ready":False,"provider":"OpenAI"}
    assert len(client.get("/api/samples").json()) == 12
    assert client.post("/api/calls").status_code == 422
    assert client.post("/api/calls",files={"file":("x.exe",b"bad")}).status_code == 422
    assert client.post("/api/calls",files={"file":("x.txt",b"Hello")},data={"demo":"true"}).status_code == 422
    assert client.post("/api/calls",files={"file":("x.txt",b"Hello")}).status_code == 503
    assert client.post("/api/calls",data={"sample_id":"missing","demo":"true"}).status_code == 404
    assert client.get("/api/calls/missing").status_code == 404


def test_api_replay_and_export(client):
    import time
    with patch("backend.samples.time.sleep"):
        response=client.post("/api/calls",data={"sample_id":"billing-refund","demo":"true","simulate_failure":"true"})
        assert response.status_code == 202
        call_id=response.json()["id"]
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            call=client.get(f"/api/calls/{call_id}").json()
            if call["status"] not in {"queued","processing"}: break
            # Event.wait is unaffected by the mocked sample sleep.
            from threading import Event
            Event().wait(.01)
    assert call["status"] == "completed"
    exported=client.get(f"/api/calls/{call_id}/export")
    assert exported.json()["summary"] == call["summary"]
    assert "attachment" in exported.headers["content-disposition"]
    assert client.get("/api/calls").json()[0]["id"] == call_id
