"""Tests for Bidu Visual Agent + Agnes Client — DEZAFIRA (stdlib unittest).

Sem chamadas reais: AgnesClient usa httpx mockado; BiduVisualAgent usa um
cliente fake que grava PNGs locais; query_llm e mockada.
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.agnes_client import AgnesClient
from modules.bidu_visual import BiduVisualAgent

from services.pwa_generator import PWAGenerator


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None, content=b""):
        self.status_code = status_code
        self._json = json_data or {}
        self.content = content
        self.text = json.dumps(self._json)

    def json(self):
        return self._json


class _FakeAgnesClient:
    """Cliente fake que grava PNGs reais em output_path e retorna o caminho."""

    def __init__(self, png_bytes, fails=False):
        self.png_bytes = png_bytes
        self.fails = fails

    async def generate_image(self, prompt, size="1024x1024", ratio="1:1",
                             ref_images=None, timeout=90.0, output_path=None):
        if self.fails:
            return None
        if output_path:
            dirname = os.path.dirname(output_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(output_path, "wb") as fh:
                fh.write(self.png_bytes)
            return output_path
        return self.png_bytes


ASSET_NAMES = [
    "mascot-front.png",
    "mascot-happy.png",
    "mascot-thinking.png",
    "mascot-pose.png",
    "logo-icon.png",
    "logo-horizontal.png",
    "favicon.png",
    "og-image.png",
]

BRIEF_JSON = ('{"species":"owl","color":"#10B981","emotion":"determined",'
              '"pose":"thumbs up","style":"flat vector mascot"}')


class TestAgnesClientGenerateImage(IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = AgnesClient(api_key="test-key")
        self.tmp = tempfile.mkdtemp()

    @patch("modules.agnes_client.httpx.AsyncClient")
    async def test_200_saves_png(self, MockClient):
        png = b"\x89PNG\r\n\x1a\n" + b"x" * 64
        post_resp = _FakeResponse(200, {"data": [{"url": "https://img/out.png"}]})
        get_resp = _FakeResponse(200, content=png)

        class _AC:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None, **kw):
                return post_resp

            async def get(self, url, **kw):
                return get_resp

        MockClient.return_value = _AC()
        out = os.path.join(self.tmp, "o.png")
        result = await self.client.generate_image("a cute owl", output_path=out)
        self.assertEqual(result, out)
        self.assertTrue(os.path.exists(out))

    @patch("modules.agnes_client.httpx.AsyncClient")
    async def test_429_retries_then_success(self, MockClient):
        png = b"\x89PNG\r\n\x1a\n" + b"y" * 64
        get_resp = _FakeResponse(200, content=png)
        queue = [
            {"status": 429, "json": {}},
            {"status": 200, "json": {"data": [{"url": "https://img/o.png"}]}},
        ]

        class _AC:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None, **kw):
                item = queue.pop(0)
                return _FakeResponse(item["status"], item["json"])

            async def get(self, url, **kw):
                return get_resp

        MockClient.return_value = _AC()
        out = os.path.join(self.tmp, "retry.png")
        result = await self.client.generate_image("prompt", output_path=out)
        self.assertEqual(result, out)
        self.assertTrue(os.path.exists(out))

    @patch("modules.agnes_client.httpx.AsyncClient")
    async def test_500_returns_none(self, MockClient):
        class _AC:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, json=None, **kw):
                return _FakeResponse(500, {"error": "boom"})

        MockClient.return_value = _AC()
        out = os.path.join(self.tmp, "none.png")
        result = await self.client.generate_image("prompt", output_path=out)
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(out))


class TestBiduVisualAgentGenerateAssets(IsolatedAsyncioTestCase):
    async def _make_agent(self, fails=False):
        png = PWAGenerator.generate_icons("T", size=64)
        fake = _FakeAgnesClient(png_bytes=png, fails=fails)
        agent = BiduVisualAgent(client=fake)

        async def fake_brief(brand, pain, app_name):
            return {"species": "owl", "color": "#10B981", "emotion": "determined",
                    "pose": "thumbs up", "style": "flat vector mascot"}

        async def fake_master(brief, app_name, pain):
            return f"{brief['style']} owl mascot"

        agent._brief = fake_brief
        agent._master_prompt = fake_master
        return agent

    async def test_creates_full_kit_with_exact_names(self):
        brand = {
            "brand_name": "Meu App",
            "brand_voice": "Tom direto",
            "theme": {"primary": "#10B981", "emoji": "🦉"},
            "header_symbol": "🦉",
        }
        agent = await self._make_agent()
        tmp = tempfile.mkdtemp()

        result = await agent.generate_assets(
            brand=brand, pain="ajuda a calcular", app_name="Meu App",
            slug="meu-app", output_dir=tmp,
        )

        files = sorted(os.listdir(tmp))
        self.assertIn("character-brief.json", files)
        for name in ASSET_NAMES:
            self.assertIn(name, files, f"faltou {name}")

        self.assertTrue(result["logo_url"])
        self.assertTrue(result["banner_url"])
        self.assertTrue(result["favicon_url"])
        self.assertTrue(result["og_image_url"])
        self.assertTrue(result["character_brief"])
        self.assertIn("front", result["mascot"])

        with open(os.path.join(tmp, "character-brief.json"), encoding="utf-8") as fh:
            brief = json.load(fh)
        self.assertEqual(brief["species"], "owl")
        self.assertIn("master_prompt", brief)
        self.assertEqual(len(brief["generated_files"]), len(ASSET_NAMES) + 1)

    async def test_fallback_ricardo_when_agnes_fails(self):
        brand = {"brand_name": "App", "brand_voice": "",
                 "theme": {"primary": "#3B82F6"}}
        agent = await self._make_agent(fails=True)
        tmp = tempfile.mkdtemp()

        async def fake_ricardo(app_name):
            return {"logo_url": "", "banner_url": ""}

        agent._fallback_ricardo = fake_ricardo

        result = await agent.generate_assets(
            brand=brand, pain="x", app_name="App", slug="app", output_dir=tmp
        )
        # Nunca lanca; garante estrutura basica do retorno
        self.assertEqual(result["provider"], "fallback_ricardo")
        self.assertIn("logo_url", result)
        self.assertIn("banner_url", result)
        self.assertIn("character_brief", result)

    async def test_brief_fallback_when_llm_fails(self):
        """Se o LLM falhar, o _brief cai no fallback deterministico."""
        import modules.bidu_visual as bb
        brand = {"brand_name": "App", "brand_voice": "",
                 "theme": {"primary": "#FF0000"}}
        agent = BiduVisualAgent(client=_FakeAgnesClient(PWAGenerator.generate_icons("T", size=32)))
        with patch.object(bb, "query_llm", return_value="[[ERRO]] todos falharam"):
            brief = await agent._brief(brand, pain="dor", app_name="App")
        self.assertEqual(brief["color"], "#FF0000")
        self.assertTrue(brief["species"])


if __name__ == '__main__':
    unittest.main(verbosity=2)
