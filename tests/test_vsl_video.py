"""Testes do VSL Video — cenas + narração TTS + montagem MP4 (offline-safe)."""

import os
import shutil
import sys

import pytest

from modules.vsl_video import _split_scenes

try:
    import imageio_ffmpeg  # noqa: F401
    HAS_FFMPEG = bool(imageio_ffmpeg.get_ffmpeg_exe())
except Exception:  # noqa: BLE001
    HAS_FFMPEG = False

VSL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "vsl")


def _cleanup():
    if os.path.isdir(VSL_DIR):
        shutil.rmtree(VSL_DIR, ignore_errors=True)


def test_split_scenes_divide_paragrafos_e_limita_8():
    script = "\n\n".join(f"Parágrafo {i} com conteúdo de vendas." for i in range(12))
    scenes = _split_scenes(script)
    assert len(scenes) == 8  # cap
    assert scenes[0].startswith("Parágrafo 0")


def test_split_scenes_quebra_paragrafo_longo():
    long_para = "Frase um. " * 40
    scenes = _split_scenes(long_para)
    assert len(scenes) >= 2
    assert all(len(s) <= 400 for s in scenes)


def test_split_scenes_vazio_usa_fallback():
    assert _split_scenes("") == ["Conteúdo"]
    assert _split_scenes(None) == ["Conteúdo"]


@pytest.mark.asyncio
async def test_render_scene_png_fallback_pillow(monkeypatch):
    """Sem Chrome (OBSCURA_ENABLED=false) → cena sai pelo Pillow com o tamanho certo."""
    import modules.vsl_video as m
    from modules.agnes_studio import AgnesStudio

    monkeypatch.setenv("OBSCURA_ENABLED", "false")
    os.makedirs(VSL_DIR, exist_ok=True)
    out = os.path.join(VSL_DIR, "scene_test.png")
    studio = AgnesStudio()
    design = studio._make_design("elegante", "Vendas")
    await m.render_scene_png("Texto da cena de teste", "Título", design, 1, 2, out)
    assert os.path.isfile(out)
    from PIL import Image
    with Image.open(out) as img:
        assert img.size == (1280, 720)
    os.unlink(out)


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg não disponível")
@pytest.mark.asyncio
async def test_generate_vsl_video_sem_tts_usa_duracao_minima(monkeypatch):
    """Sem TTS (offline) → cenas silenciosas com duração mínima; vídeo montado."""
    import modules.vsl_video as m
    from modules.agnes_studio import AgnesStudio

    monkeypatch.setenv("OBSCURA_ENABLED", "false")

    async def _fake_false(*a, **k):
        return False

    monkeypatch.setattr(m, "synthesize_audio", _fake_false)

    script = "Primeira cena de teste.\n\nSegunda cena de teste.\n\nTerceira cena."
    try:
        res = await m.generate_vsl_video("vsl_test_vid", script, "Curso", "Vendas", style_id="moderno")
        assert res["status"] == "ok"
        assert res["video_url"].endswith("vsl_test_vid.mp4")
        assert len(res["scenes"]) == 3
        assert os.path.isfile(os.path.join(VSL_DIR, "vsl_test_vid.mp4"))
    finally:
        _cleanup()


@pytest.mark.asyncio
async def test_generate_vsl_video_degrada_sem_ffmpeg(monkeypatch):
    """Sem ffmpeg → status no-ffmpeg sem levantar exceção."""
    import modules.vsl_video as m

    monkeypatch.setattr(m, "_ffmpeg", lambda: None)
    res = await m.generate_vsl_video("vsl_x", "Cena única.", "T", "N")
    assert res["status"] == "no-ffmpeg"
