"""Unit tests for transparent scene rendering and FFMPEG overlay compilation."""

import os
import subprocess
from unittest.mock import MagicMock, patch
import pytest

from modules.vsl_video import (
    _scene_html,
    _render_scene_pillow,
    render_scene_png,
    _build_segment_overlay,
)


def test_scene_html_transparent():
    design = {
        "colors": {"bg": "#ffffff", "bg2": "#f0f0f0", "accent": "#ff0000", "text": "#000", "muted": "#666"},
        "fonts": {"font": "Georgia", "font_sans": "Arial"},
    }
    html_normal = _scene_html("Olá", "Título", design, 1, 3, transparent=False)
    html_trans = _scene_html("Olá", "Título", design, 1, 3, transparent=True)
    
    assert "background: linear-gradient" in html_normal
    assert "background: transparent;" in html_trans


def test_render_scene_pillow_transparent():
    design = {
        "colors": {"bg": "#ffffff", "bg2": "#f0f0f0", "accent": "#ff0000", "text": "#000", "muted": "#666"},
    }
    png_bytes = _render_scene_pillow("Texto longo para quebrar linha", design, 100, 100, transparent=True)
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 0


@pytest.mark.asyncio
async def test_render_scene_png_transparent(tmp_path):
    design = {
        "colors": {"bg": "#ffffff", "bg2": "#f0f0f0", "accent": "#ff0000", "text": "#000", "muted": "#666"},
        "fonts": {"font": "Georgia", "font_sans": "Arial"},
    }
    out_file = os.path.join(tmp_path, "scene_trans.png")
    # Usa o renderizador que faz fallback para Pillow caso o browser não esteja rodando
    ok = await render_scene_png("Texto do teste", "Curso de Teste", design, 1, 1, out_file, transparent=True)
    assert ok is True
    assert os.path.isfile(out_file)
    assert os.path.getsize(out_file) > 0


@pytest.mark.asyncio
async def test_build_segment_overlay_ffmpeg_call():
    ffmpeg_bin = "mock-ffmpeg"
    video_in = "bg.mp4"
    overlay_in = "overlay.png"
    audio_in = "voice.mp3"
    video_out = "output.mp4"

    # Caso com áudio
    with patch("subprocess.run") as mock_run, patch("os.path.isfile", return_value=True):
        mock_run.return_value = MagicMock(returncode=0)
        
        ok = await _build_segment_overlay(video_in, overlay_in, audio_in, video_out, ffmpeg_bin)
        
        assert ok is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == ffmpeg_bin
        assert "-filter_complex" in cmd
        assert "[0:v][1:v]overlay=0:0[v]" in cmd
        assert "-map" in cmd
        assert "2:a" in cmd

    # Caso sem áudio
    with patch("subprocess.run") as mock_run, patch("os.path.isfile", return_value=True):
        mock_run.return_value = MagicMock(returncode=0)
        
        ok = await _build_segment_overlay(video_in, overlay_in, None, video_out, ffmpeg_bin)
        
        assert ok is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == ffmpeg_bin
        assert "-an" in cmd
        assert "[0:v][1:v]overlay=0:0" in cmd
