"""Testes do módulo de vídeo Agnes (modules/agnes_video.py) — HTTP mockado.

Não toca na API real (não gasta cota). Cobre: payload do POST, extração da
URL em `metadata.url` (formato real de conclusão da Agnes), polling até
concluir e conversão base64.
"""
import asyncio
import json

import pytest

import modules.agnes_video as av


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode()
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeClient:
    """Fake do httpx.AsyncClient: devolve respostas por rota (POST/GET)."""

    def __init__(self, post_resp=None, get_resp=None):
        self.post_resp = post_resp
        self.get_resp = get_resp
        self.post_calls = []
        self.get_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, json=None):
        self.post_calls.append((url, json))
        return self.post_resp

    async def get(self, url, headers=None):
        self.get_calls.append(url)
        return self.get_resp

    async def close(self):
        pass


@pytest.fixture(autouse=True)
def _fake_key(monkeypatch):
    monkeypatch.setattr(av, "AGNES_VIDEO_API_KEY", "cpk-teste")
    yield
    monkeypatch.setattr(av, "AGNES_VIDEO_API_KEY", "")


def test_image_to_base64_prefix():
    b64 = av.image_to_base64(b"\x89PNG\r\n\x1a\n", mime="image/png")
    assert b64.startswith("data:image/png;base64,")
    assert "iVBORw0KGgo" in b64


@pytest.mark.asyncio
async def test_generate_payload_envia_modelo_e_imagem(monkeypatch):
    resp = FakeResponse(200, {"task_id": "task_abc", "status": "queued", "progress": 0})
    fake = FakeClient(post_resp=resp)
    monkeypatch.setattr(av.httpx, "AsyncClient", lambda *a, **k: fake)

    out = await av.agnes_video_generate("câmera lenta", image=b"foto")

    assert out["task_id"] == "task_abc"
    url, payload = fake.post_calls[0]
    assert url.endswith("/v1/videos")
    assert payload["model"] == "agnes-video-v2.0"
    assert payload["image"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_status_extrai_url_do_metadata(monkeypatch):
    # Formato REAL de conclusão da Agnes: a URL fica em metadata.url
    resp = FakeResponse(200, {
        "task_id": "task_x", "status": "completed", "progress": 100,
        "metadata": {"url": "https://platform-outputs.agnes-ai.space/videos/x.mp4"},
    })
    fake = FakeClient(get_resp=resp)
    monkeypatch.setattr(av.httpx, "AsyncClient", lambda *a, **k: fake)

    out = await av.agnes_video_status("task_x")

    assert out["status"] == "completed"
    assert out["url"] == "https://platform-outputs.agnes-ai.space/videos/x.mp4"
    assert fake.get_calls[0].endswith("/v1/videos/task_x")


@pytest.mark.asyncio
async def test_generate_and_wait_conclui(monkeypatch):
    monkeypatch.setattr(av.asyncio, "sleep", lambda s: asyncio.sleep(0))

    async def status_side(task_id):
        if task_id == "task_ok":
            return {
                "task_id": "task_ok", "status": "completed", "progress": 100,
                "url": "https://ex.com/v.mp4", "raw": {},
            }
        return {"task_id": task_id, "status": "queued", "progress": 0, "url": "", "raw": {}}

    async def fake_generate(*a, **k):
        return {"task_id": "task_ok", "status": "queued"}

    monkeypatch.setattr(av, "agnes_video_generate", fake_generate)
    monkeypatch.setattr(av, "agnes_video_status", status_side)

    out = await av.agnes_video_generate_and_wait("prompt", image=b"x")

    assert out["status"] == "completed"
    assert out["url"] == "https://ex.com/v.mp4"


@pytest.mark.asyncio
async def test_sem_chave_retorna_erro(monkeypatch):
    monkeypatch.setattr(av, "AGNES_VIDEO_API_KEY", "")
    out = await av.agnes_video_generate("prompt")
    assert "error" in out and "AGNES_API_KEY" in out["error"]
