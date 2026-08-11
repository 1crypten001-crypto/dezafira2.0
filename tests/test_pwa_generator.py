"""Tests for PWA Generator — DEZAFIRA (stdlib unittest)."""
import json
import os
import struct
import sys
import unittest
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pwa_generator import PWAGenerator


class TestSlugify(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(PWAGenerator.slugify("Hello World"), "hello-world")

    def test_accents(self):
        self.assertEqual(PWAGenerator.slugify("Acao Rapida"), "acao-rapida")
        self.assertEqual(PWAGenerator.slugify("Ação Rápida"), "acao-rapida")
        self.assertEqual(PWAGenerator.slugify("Finanças & Negócios!"), "financas-negocios")

    def test_multiple_spaces(self):
        self.assertEqual(PWAGenerator.slugify("  Multi   Espacos  "), "multi-espacos")

    def test_empty(self):
        self.assertEqual(PWAGenerator.slugify(""), "app")
        self.assertEqual(PWAGenerator.slugify(None), "app")


class TestNicheTheme(unittest.TestCase):
    def test_known_niches(self):
        self.assertEqual(PWAGenerator.niche_theme("financas")["primary"], "#10B981")
        self.assertEqual(PWAGenerator.niche_theme("Emagrecimento")["primary"], "#F97316")
        self.assertEqual(PWAGenerator.niche_theme("marketing")["primary"], "#8B5CF6")
        self.assertEqual(PWAGenerator.niche_theme("ESPIRITUAL")["primary"], "#A78BFA")
        self.assertEqual(PWAGenerator.niche_theme("saude")["primary"], "#EF4444")
        self.assertEqual(PWAGenerator.niche_theme("tecnologia")["primary"], "#3B82F6")

    def test_has_emoji(self):
        for niche in ["financas", "emagrecimento", "marketing", "espiritual", "saude", "tecnologia"]:
            t = PWAGenerator.niche_theme(niche)
            self.assertIn("emoji", t)
            self.assertIn("tagline", t)
            self.assertIn("gradient", t)

    def test_fallback_unknown(self):
        t = PWAGenerator.niche_theme("astrologia_extrema")
        self.assertEqual(t["primary"], "#3B82F6")

    def test_fallback_empty_and_none(self):
        self.assertEqual(PWAGenerator.niche_theme("")["primary"], "#3B82F6")
        self.assertEqual(PWAGenerator.niche_theme(None)["primary"], "#3B82F6")

    def test_fallback_is_copy_not_ref(self):
        t = PWAGenerator.niche_theme("zzz_unknown")
        t["primary"] = "modified"
        self.assertEqual(PWAGenerator.FALLBACK_THEME["primary"], "#3B82F6")


class TestBuildManifest(unittest.TestCase):
    def setUp(self):
        self.theme = PWAGenerator.niche_theme("financas")

    def test_manifest_structure(self):
        m = PWAGenerator.build_manifest("app_abc123", "meu-app", "Meu App", self.theme, "Uma descricao")
        self.assertEqual(m["name"], "Meu App")
        self.assertEqual(m["start_url"], "/app/meu-app")
        self.assertEqual(m["scope"], "/app/meu-app/")
        self.assertEqual(m["display"], "standalone")
        self.assertEqual(m["background_color"], self.theme["bg"])
        self.assertEqual(m["theme_color"], self.theme["primary"])
        self.assertEqual(m["orientation"], "portrait")
        self.assertEqual(len(m["icons"]), 3)

    def test_manifest_long_name(self):
        theme = PWAGenerator.FALLBACK_THEME
        m = PWAGenerator.build_manifest("a", "s", "Nome Muito Longo Aqui", theme)
        self.assertLessEqual(len(m["short_name"]), 12)

    def test_short_name_no_trailing_space(self):
        """Regressao: 'Calculadora de Juros Cartao' nao pode virar 'Calculadora '."""
        s = PWAGenerator._short_name("Calculadora de Juros Cartao")
        self.assertEqual(s, "Calculadora")
        self.assertFalse(s.startswith(" ") or s.endswith(" "))

    def test_short_name_word_boundary(self):
        """Regressao: truncar em limite de palavra, sem cortar palavra no meio."""
        s = PWAGenerator._short_name("Nome Muito Longo Aqui")
        self.assertEqual(s, "Nome Muito")

    def test_short_name_short_and_empty(self):
        self.assertEqual(PWAGenerator._short_name("Calculadora"), "Calculadora")
        self.assertEqual(PWAGenerator._short_name(""), "App")

    def test_short_name_single_word_long(self):
        s = PWAGenerator._short_name("PalavraUnicaMuitoGrande")
        self.assertEqual(s, "PalavraUnica")
        self.assertLessEqual(len(s), 12)

    def test_manifest_icons(self):
        theme = PWAGenerator.FALLBACK_THEME
        m = PWAGenerator.build_manifest("x", "slug-x", "X", theme)
        sizes = [i["sizes"] for i in m["icons"]]
        self.assertIn("192x192", sizes)
        self.assertIn("512x512", sizes)
        purposes = [i.get("purpose", "") for i in m["icons"]]
        self.assertIn("maskable", purposes)
        self.assertIn("any", purposes)

    def test_manifest_shortcuts(self):
        theme = PWAGenerator.FALLBACK_THEME
        m = PWAGenerator.build_manifest("a", "my-slug", "Test", theme)
        self.assertEqual(len(m["shortcuts"]), 2)
        self.assertEqual(m["shortcuts"][0]["url"], "/app/my-slug?action=quiz")

    def test_manifest_json_serializable(self):
        theme = PWAGenerator.FALLBACK_THEME
        m = PWAGenerator.build_manifest("a", "s", "T", theme)
        dumped = json.dumps(m)
        loaded = json.loads(dumped)
        self.assertEqual(loaded["name"], "T")
        self.assertEqual(len(loaded["icons"]), 3)


class TestGenerateIcons(unittest.TestCase):
    def test_png_signature(self):
        png = PWAGenerator.generate_icons("Teste App", size=192)
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')

    def test_png_size_192(self):
        png = PWAGenerator.generate_icons("App", size=192)
        sig_len = 8
        chunk_len = struct.unpack('>I', png[sig_len:sig_len+4])[0]
        chunk_type = png[sig_len+4:sig_len+8]
        self.assertEqual(chunk_type, b'IHDR')
        ihdr = png[sig_len+8:sig_len+8+chunk_len]
        w, h = struct.unpack('>II', ihdr[:8])
        self.assertEqual(w, 192)
        self.assertEqual(h, 192)

    def test_png_size_512(self):
        png = PWAGenerator.generate_icons("App", size=512)
        sig_len = 8
        chunk_len = struct.unpack('>I', png[sig_len:sig_len+4])[0]
        ihdr = png[sig_len+8:sig_len+8+chunk_len]
        w, h = struct.unpack('>II', ihdr[:8])
        self.assertEqual(w, 512)
        self.assertEqual(h, 512)

    def test_png_default_size(self):
        png = PWAGenerator.generate_icons("Default")
        sig_len = 8
        chunk_len = struct.unpack('>I', png[sig_len:sig_len+4])[0]
        ihdr = png[sig_len+8:sig_len+8+chunk_len]
        w, h = struct.unpack('>II', ihdr[:8])
        self.assertEqual(w, 512)
        self.assertEqual(h, 512)

    def test_png_is_valid_zlib(self):
        png = PWAGenerator.generate_icons("Test", size=64)
        sig_len = 8
        chunk_len_ihdr = struct.unpack('>I', png[sig_len:sig_len+4])[0]
        idat_start = sig_len + 4 + 4 + chunk_len_ihdr + 4
        chunk_len_idat = struct.unpack('>I', png[idat_start:idat_start+4])[0]
        chunk_type = png[idat_start+4:idat_start+8]
        self.assertEqual(chunk_type, b'IDAT')
        idat_data = png[idat_start+8:idat_start+8+chunk_len_idat]
        decompressed = zlib.decompress(idat_data)
        expected = 64 * (1 + 64 * 4)
        self.assertEqual(len(decompressed), expected)

    def test_theme_colors_influence_output(self):
        t1 = PWAGenerator.niche_theme("financas")
        t2 = PWAGenerator.niche_theme("saude")
        png1 = PWAGenerator.generate_icons("A", theme=t1, size=32)
        png2 = PWAGenerator.generate_icons("A", theme=t2, size=32)
        self.assertNotEqual(png1, png2)

    def test_inits_letter_rendered(self):
        png1 = PWAGenerator.generate_icons("Alpha", size=64)
        png2 = PWAGenerator.generate_icons("Zeta", size=64)
        self.assertNotEqual(png1, png2)


class TestBuildServiceWorker(unittest.TestCase):
    def test_sw_contains_slug(self):
        sw = PWAGenerator.build_service_worker("meu-slug", "app_123")
        self.assertIn("/app/meu-slug", sw)
        self.assertIn("dezafira-meu-slug-v1", sw)

    def test_sw_contains_caching_logic(self):
        sw = PWAGenerator.build_service_worker("test", "id")
        self.assertIn("caches.open", sw)
        self.assertIn("skipWaiting", sw)

    def test_sw_contains_offline_fallback(self):
        sw = PWAGenerator.build_service_worker("slug", "id")
        self.assertTrue("offline" in sw.lower() or "Offline" in sw)


class TestGenerateQuizPwa(unittest.TestCase):
    def _sample_questions(self):
        return [{"question": "Q1", "options": ["A", "B"], "result": {"title": "R1", "desc": "D1"}}]

    def test_html_contains_manifest_link(self):
        res = PWAGenerator.generate_quiz_pwa("app_test1", "Quiz Test", "marketing", self._sample_questions())
        self.assertTrue(res["success"])
        self.assertIn('manifest.json', res["html"])
        self.assertIn('<link rel="manifest"', res["html"])

    def test_html_contains_sw_registration(self):
        res = PWAGenerator.generate_quiz_pwa("app_test2", "SW Test", "financas", self._sample_questions())
        self.assertIn("serviceWorker.register", res["html"])

    def test_html_contains_app_name(self):
        res = PWAGenerator.generate_quiz_pwa("app_t3", "Meu Quiz Personalizado", "saude", self._sample_questions())
        self.assertIn("Meu Quiz Personalizado", res["html"])

    def test_manifest_in_result(self):
        res = PWAGenerator.generate_quiz_pwa("app_m", "M Test", "geral", self._sample_questions())
        self.assertIsInstance(res["manifest"], dict)
        self.assertIn("icons", res["manifest"])

    def test_service_worker_in_result(self):
        res = PWAGenerator.generate_quiz_pwa("app_sw2", "SW Result Test", "tecnologia", self._sample_questions())
        self.assertIsInstance(res["service_worker"], str)
        self.assertGreater(len(res["service_worker"]), 100)

    def test_icons_in_result(self):
        res = PWAGenerator.generate_quiz_pwa("app_icons", "Icon Test", "espiritual", self._sample_questions())
        self.assertIn("192", res["icons"])
        self.assertIn("512", res["icons"])
        self.assertIn("maskable", res["icons"])

    def test_string_questions_tolerated(self):
        res = PWAGenerator.generate_quiz_pwa("app_str", "String Test", "geral", ["Pergunta 1", "Pergunta 2"])
        self.assertTrue(res["success"])

    def test_mixed_questions_tolerated(self):
        q = [
            {"question": "Q1", "options": ["A", "B"]},
            "Pergunta simples",
            {"questionText": "Q2", "options": [{"text": "X"}]},
        ]
        res = PWAGenerator.generate_quiz_pwa("app_mix", "Mixed", "geral", q)
        self.assertTrue(res["success"])

    def test_empty_questions_works(self):
        res = PWAGenerator.generate_quiz_pwa("app_empty", "Empty", "geral", [])
        self.assertTrue(res["success"])
        self.assertTrue(res["html"])

    def test_app_url_format(self):
        res = PWAGenerator.generate_quiz_pwa("app_url", "Meu App Teste", "financas", self._sample_questions())
        self.assertTrue(res["app_url"].startswith("/app/"))
        self.assertIn("meu-app-teste", res["app_url"])

    def test_placeholder_resolution(self):
        res = PWAGenerator.generate_quiz_pwa("app_ph", "Test Placeholder!", "marketing", self._sample_questions())
        self.assertNotIn("{{APP_ID}}", res["html"])
        self.assertIn("app_ph", res["html"])


class TestGenerateFromAppRecord(unittest.TestCase):
    def test_returns_html(self):
        record = {"id": "app_test1", "app_name": "Teste DB", "niche": "saude", "pwa_html": ""}
        res = PWAGenerator.generate_from_app_record(record)
        self.assertTrue(res["success"])
        self.assertGreater(len(res["html"]), 500)
        self.assertIn("Teste DB", res["html"])

    def test_manifest_included(self):
        record = {"id": "app_man", "app_name": "Manifest App", "niche": "tecnologia", "pwa_html": ""}
        res = PWAGenerator.generate_from_app_record(record)
        self.assertIsInstance(res["manifest"], dict)

    def test_service_worker_included(self):
        record = {"id": "app_sw2", "app_name": "SW Record", "niche": "financas"}
        res = PWAGenerator.generate_from_app_record(record)
        self.assertIn("skipWaiting", res["service_worker"])

    def test_substantial_pwa_html_wrapped(self):
        long_html = "<div>" + ("x" * 600) + "</div>"
        record = {"id": "app_big", "app_name": "Big HTML", "niche": "geral", "pwa_html": long_html}
        res = PWAGenerator.generate_from_app_record(record)
        self.assertIn("stored-content", res["html"])


class TestGenerateCheckoutPage(unittest.TestCase):
    def test_returns_valid_html(self):
        res = PWAGenerator.generate_checkout_page("Produto X", "https://checkout.com")
        self.assertTrue(res["success"])
        self.assertIn("<!DOCTYPE html>", res["html"])
        self.assertIn("Produto X", res["html"])
        self.assertIn("https://checkout.com", res["html"])

    def test_theme_applied(self):
        theme = PWAGenerator.niche_theme("financas")
        res = PWAGenerator.generate_checkout_page("P", "https://c.com", theme)
        self.assertIn(theme["bg"], res["html"])
        self.assertIn(theme["primary"], res["html"])

    def test_slug_returned(self):
        res = PWAGenerator.generate_checkout_page("Meu Produto", "https://c.com")
        self.assertEqual(res["slug"], "meu-produto")


class TestNormalizeQuestions(unittest.TestCase):
    def test_simple_dict_questions(self):
        q = [{"question": "Q", "options": ["A", "B"], "result": {"title": "R", "desc": "D"}}]
        n = PWAGenerator._normalize_questions(q)
        self.assertEqual(len(n), 1)
        self.assertEqual(n[0]["question"], "Q")
        self.assertEqual(len(n[0]["options"]), 2)
        self.assertEqual(n[0]["options"][0]["text"], "A")
        self.assertEqual(n[0]["options"][0]["points"], 1)

    def test_string_questions(self):
        n = PWAGenerator._normalize_questions(["Q1", "Q2"])
        self.assertEqual(len(n), 2)
        self.assertEqual(n[0]["question"], "Q1")
        self.assertEqual(n[0]["options"][0]["text"], "Q1")

    def test_mixed_option_formats(self):
        q = [{"question": "Q", "options": [
            "Simple string",
            {"text": "Dict text", "points": 5},
            {"text": "Dict value", "value": 3},
        ]}]
        n = PWAGenerator._normalize_questions(q)
        self.assertEqual(len(n[0]["options"]), 3)
        self.assertEqual(n[0]["options"][0]["points"], 1)
        self.assertEqual(n[0]["options"][1]["points"], 5)
        self.assertEqual(n[0]["options"][2]["points"], 3)

    def test_alternative_keys(self):
        q = [{"questionText": "Alt Q", "options": [{"text": "A"}], "resultado": {"titulo": "RT", "descricao": "RD"}}]
        n = PWAGenerator._normalize_questions(q)
        self.assertEqual(n[0]["question"], "Alt Q")
        self.assertEqual(n[0]["result"]["title"], "RT")
        self.assertEqual(n[0]["result"]["desc"], "RD")

    def test_string_result(self):
        q = [{"question": "Q", "options": ["A"], "result": "Resultado simples"}]
        n = PWAGenerator._normalize_questions(q)
        self.assertEqual(n[0]["result"]["title"], "Resultado simples")
        self.assertEqual(n[0]["result"]["desc"], "")


if __name__ == '__main__':
    unittest.main(verbosity=2)
