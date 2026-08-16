"""Unit tests for ArtDirector (Agnes agent) — updated for cinematic pipeline."""

import pytest
from modules.art_director import ArtDirector, VIBES


def test_art_director_get_vibe():
    director = ArtDirector()
    vibe = director.get_vibe("claude")
    assert vibe["name"] == "Claude Editorial"
    assert "colors" in vibe
    assert "font" in vibe["fonts"]


def test_art_director_get_vibe_fallback():
    director = ArtDirector()
    # Fallback agora vai para "apple" (DEFAULT_VIBE atualizado)
    vibe = director.get_vibe("inexistente-vibe-abc")
    assert "colors" in vibe
    assert "fonts" in vibe


def test_art_director_brand_kit():
    director = ArtDirector()
    kit = director.generate_brand_kit("linear", niche="Finanças")
    assert kit["vibe_id"] == "linear"
    assert kit["nicho"] == "Finanças"
    assert "accent" in kit["colors"]
    # layout para linear agora é "tech-dark"
    assert kit["layout"] == "tech-dark"


def test_art_director_brand_kit_nintendo_layout():
    director = ArtDirector()
    kit = director.generate_brand_kit("nintendo")
    assert kit["layout"] == "console-retro"


def test_art_director_image_prompt():
    director = ArtDirector()
    prompt = director.generate_image_prompt(
        "claude", "a digital marketing expert", "sitting in a modern office", seed=42
    )
    assert "a digital marketing expert" in prompt
    assert "sitting in a modern office" in prompt
    assert "seed:42" in prompt
    # Deve conter estilo editorial do Claude
    assert "editorial" in prompt.lower()


def test_art_director_video_motion_prompt():
    director = ArtDirector()
    config = director.generate_video_motion_prompt("apple", "Super Product")
    assert "Super Product" in config["prompt"]
    assert "cinematic" in config["prompt"].lower()
    assert config["motion"] == 60  # apple usa 60 no novo sistema
    assert config["aspect_ratio"] == "16:9"
    assert "text warping" in config["negative_prompt"]
