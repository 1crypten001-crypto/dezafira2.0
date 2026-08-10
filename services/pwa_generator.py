"""PWA Generator — deterministic single-file PWA builder for DEZAFIRA."""
import json
import os
import re
import struct
import zlib
import unicodedata


class PWAGenerator:

    NICHE_PALETTES = {
        "financas": {
            "primary": "#10B981", "accent": "#34D399",
            "gradient": "135deg, #064E3B, #10B981",
            "bg": "#090D16", "surface": "#0F1F1A",
            "emoji": "💰", "tagline": "Transforme sua relação com o dinheiro"
        },
        "emagrecimento": {
            "primary": "#F97316", "accent": "#FB923C",
            "gradient": "135deg, #7C2D12, #F97316",
            "bg": "#090D16", "surface": "#1F1A12",
            "emoji": "🔥", "tagline": "O corpo que você merece começa aqui"
        },
        "marketing": {
            "primary": "#8B5CF6", "accent": "#A78BFA",
            "gradient": "135deg, #4C1D95, #8B5CF6",
            "bg": "#090D16", "surface": "#151320",
            "emoji": "🚀", "tagline": "Escale seus resultados com estratégia"
        },
        "espiritual": {
            "primary": "#A78BFA", "accent": "#C4B5FD",
            "gradient": "135deg, #2E1065, #7C3AED",
            "bg": "#090D16", "surface": "#161320",
            "emoji": "✨", "tagline": "Desperte sua melhor versão interior"
        },
        "saude": {
            "primary": "#EF4444", "accent": "#F87171",
            "gradient": "135deg, #7F1D1D, #EF4444",
            "bg": "#090D16", "surface": "#1F1216",
            "emoji": "❤️", "tagline": "Saúde plena, vida plena"
        },
        "tecnologia": {
            "primary": "#3B82F6", "accent": "#60A5FA",
            "gradient": "135deg, #1E3A5F, #3B82F6",
            "bg": "#090D16", "surface": "#131A2C",
            "emoji": "💻", "tagline": "Inovação que transforma realidades"
        },
    }

    FALLBACK_THEME = {
        "primary": "#3B82F6", "accent": "#60A5FA",
        "gradient": "135deg, #1E3A5F, #3B82F6",
        "bg": "#090D16", "surface": "#131A2C",
        "emoji": "⚡", "tagline": "Soluções inteligentes para você"
    }

    # Simple 6x8 bitmap font for uppercase letters A-Z
    _FONT = {
        'A': [0b011110, 0b110011, 0b110011, 0b111111, 0b111111, 0b110011, 0b110011, 0b110011],
        'B': [0b111110, 0b110011, 0b110011, 0b111110, 0b111110, 0b110011, 0b110011, 0b111110],
        'C': [0b011110, 0b110011, 0b110000, 0b110000, 0b110000, 0b110000, 0b110011, 0b011110],
        'D': [0b111100, 0b110110, 0b110011, 0b110011, 0b110011, 0b110011, 0b110110, 0b111100],
        'E': [0b111111, 0b110000, 0b110000, 0b111100, 0b111100, 0b110000, 0b110000, 0b111111],
        'F': [0b111111, 0b110000, 0b110000, 0b111110, 0b111110, 0b110000, 0b110000, 0b110000],
        'G': [0b011110, 0b110011, 0b110000, 0b110000, 0b110111, 0b110011, 0b110011, 0b011110],
        'H': [0b110011, 0b110011, 0b110011, 0b111111, 0b111111, 0b110011, 0b110011, 0b110011],
        'I': [0b111111, 0b001100, 0b001100, 0b001100, 0b001100, 0b001100, 0b001100, 0b111111],
        'J': [0b001111, 0b000110, 0b000110, 0b000110, 0b000110, 0b110110, 0b110110, 0b011100],
        'K': [0b110011, 0b110110, 0b111100, 0b111000, 0b111000, 0b111100, 0b110110, 0b110011],
        'L': [0b110000, 0b110000, 0b110000, 0b110000, 0b110000, 0b110000, 0b110000, 0b111111],
        'M': [0b110011, 0b111111, 0b111111, 0b110011, 0b110011, 0b110011, 0b110011, 0b110011],
        'N': [0b110011, 0b111011, 0b111011, 0b111111, 0b110111, 0b110111, 0b110011, 0b110011],
        'O': [0b011110, 0b110011, 0b110011, 0b110011, 0b110011, 0b110011, 0b110011, 0b011110],
        'P': [0b111110, 0b110011, 0b110011, 0b111110, 0b111110, 0b110000, 0b110000, 0b110000],
        'Q': [0b011110, 0b110011, 0b110011, 0b110011, 0b111011, 0b110111, 0b011110, 0b000111],
        'R': [0b111110, 0b110011, 0b110011, 0b111110, 0b111100, 0b110110, 0b110011, 0b110011],
        'S': [0b011110, 0b110011, 0b110000, 0b011110, 0b001111, 0b000011, 0b110011, 0b011110],
        'T': [0b111111, 0b001100, 0b001100, 0b001100, 0b001100, 0b001100, 0b001100, 0b001100],
        'U': [0b110011, 0b110011, 0b110011, 0b110011, 0b110011, 0b110011, 0b110011, 0b011110],
        'V': [0b110011, 0b110011, 0b110011, 0b110011, 0b110011, 0b110011, 0b011110, 0b001100],
        'W': [0b110011, 0b110011, 0b110011, 0b110011, 0b110011, 0b111111, 0b111111, 0b110011],
        'X': [0b110011, 0b110011, 0b011110, 0b001100, 0b001100, 0b011110, 0b110011, 0b110011],
        'Y': [0b110011, 0b110011, 0b110011, 0b011110, 0b001100, 0b001100, 0b001100, 0b001100],
        'Z': [0b111111, 0b000011, 0b000110, 0b001100, 0b011000, 0b110000, 0b110000, 0b111111],
    }

    @staticmethod
    def slugify(text: str) -> str:
        text = unicodedata.normalize('NFKD', str(text or ""))
        text = text.encode('ASCII', 'ignore').decode('ASCII')
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[-\s]+', '-', text).strip('-')
        return text or "app"

    @staticmethod
    def niche_theme(nicho: str) -> dict:
        if not nicho:
            return dict(PWAGenerator.FALLBACK_THEME)
        key = nicho.lower().strip()
        for palette_key in PWAGenerator.NICHE_PALETTES:
            if palette_key in key or key in palette_key:
                return dict(PWAGenerator.NICHE_PALETTES[palette_key])
        return dict(PWAGenerator.FALLBACK_THEME)

    @staticmethod
    def generate_icons(app_name: str, theme: dict = None, size: int = 512) -> bytes:
        if theme is None:
            theme = PWAGenerator.FALLBACK_THEME
        primary = theme.get("primary", "#3B82F6")
        accent = theme.get("accent", "#60A5FA")

        logo_text = PWAGenerator.slugify(app_name)[:6].upper() if app_name else "DZ"
        letter = logo_text[0] if logo_text else "D"

        def _hex_to_rgba(hx: str, a: int = 255) -> tuple:
            hx = hx.lstrip('#')
            if len(hx) == 6:
                return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16), a)
            if len(hx) == 3:
                return (int(hx[0]*2, 16), int(hx[1]*2, 16), int(hx[2]*2, 16), a)
            return (0, 0, 0, a)

        c1 = _hex_to_rgba(primary)
        c2 = _hex_to_rgba(accent)

        raw_data = bytearray()

        diag = size * 1.5
        cx, cy = size // 2, size // 2
        radius = size * 0.18

        for y in range(size):
            raw_data.append(0)  # filter byte None
            for x in range(size):
                d = (x + y) / diag
                r = int(c1[0] + (c2[0] - c1[0]) * d)
                g = int(c1[1] + (c2[1] - c1[1]) * d)
                b = int(c1[2] + (c2[2] - c1[2]) * d)
                a = 255

                dx = x - cx
                dy = y - cy
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < radius:
                    r, g, b, a_ = 255, 255, 255, 200
                    blend = dist / radius
                    r = int(r * (1 - blend) + c1[0] * blend)
                    g = int(g * (1 - blend) + c1[1] * blend)
                    b = int(b * (1 - blend) + c1[2] * blend)

                raw_data.extend([r, g, b, a])

        # draw initial letter if font available
        font_rows = PWAGenerator._FONT.get(letter)
        if font_rows:
            fw, fh = 6, 8
            scale = max(2, int(size * 0.06))
            f_px_w = fw * scale
            f_px_h = fh * scale
            fx0 = cx - f_px_w // 2
            fy0 = cy - f_px_h // 2

            for fy in range(fh):
                row_bits = font_rows[fy]
                for fx in range(fw):
                    if row_bits & (1 << (fw - 1 - fx)):
                        for sy in range(scale):
                            py = fy0 + fy * scale + sy
                            if 0 <= py < size:
                                row_start = 1 + py * (size * 4 + 1) + fx0 * 4
                                for sx in range(scale):
                                    px = fx0 + fx * scale + sx
                                    if 0 <= px < size:
                                        idx = 1 + py * (size * 4 + 1) + px * 4
                                        raw_data[idx + 0] = 255
                                        raw_data[idx + 1] = 255
                                        raw_data[idx + 2] = 255
                                        raw_data[idx + 3] = 255

        return PWAGenerator._build_png(raw_data, size)

    @staticmethod
    def _build_png(raw_data: bytes, size: int) -> bytes:
        def _chunk(chunk_type: bytes, data: bytes) -> bytes:
            c = chunk_type + data
            return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

        sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
        ihdr = _chunk(b'IHDR', ihdr_data)
        idat = _chunk(b'IDAT', zlib.compress(raw_data))
        iend = _chunk(b'IEND', b'')
        return sig + ihdr + idat + iend

    @staticmethod
    def _normalize_questions(questions) -> list:
        normalized = []
        for q in questions:
            if isinstance(q, str):
                normalized.append({
                    "question": q,
                    "options": [{"text": q, "points": 1}],
                    "result": {"title": "", "desc": ""}
                })
            elif isinstance(q, dict):
                entry = {
                    "question": q.get("question", q.get("questionText", q.get("text", ""))),
                    "options": [],
                    "result": {"title": "", "desc": ""}
                }
                raw_opts = q.get("options", [])
                for opt in raw_opts:
                    if isinstance(opt, str):
                        entry["options"].append({"text": opt, "points": 1})
                    elif isinstance(opt, dict):
                        entry["options"].append({
                            "text": opt.get("text", ""),
                            "points": opt.get("points", opt.get("value", 1))
                        })
                res = q.get("result", q.get("resultado", {}))
                if isinstance(res, dict):
                    entry["result"] = {
                        "title": res.get("title", res.get("titulo", "")),
                        "desc": res.get("desc", res.get("descricao", res.get("description", "")))
                    }
                elif isinstance(res, str):
                    entry["result"] = {"title": res, "desc": ""}
                normalized.append(entry)
        return normalized

    @staticmethod
    def build_manifest(app_id: str, slug: str, app_name: str, theme: dict, description: str = "") -> dict:
        start_url = f"/app/{slug}"
        scope = f"/app/{slug}/"
        bg = theme.get("bg", "#090D16")
        primary = theme.get("primary", "#3B82F6")
        return {
            "name": app_name,
            "short_name": app_name[:12] if len(app_name) > 12 else app_name,
            "description": description or f"{app_name} — {theme.get('tagline', 'App Inteligente')}",
            "start_url": start_url,
            "scope": scope,
            "display": "standalone",
            "background_color": bg,
            "theme_color": primary,
            "orientation": "portrait",
            "icons": [
                {
                    "src": f"/app/{slug}/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": f"/app/{slug}/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": f"/app/{slug}/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "maskable"
                }
            ],
            "shortcuts": [
                {
                    "name": "Iniciar Quiz",
                    "url": f"/app/{slug}?action=quiz",
                    "description": "Comece o quiz personalizado"
                },
                {
                    "name": "Meu Progresso",
                    "url": f"/app/{slug}?action=progress",
                    "description": "Veja seu progresso e streak"
                }
            ]
        }

    @staticmethod
    def build_service_worker(slug: str, app_id: str, precache_urls: list = None) -> str:
        base = f"/app/{slug}"
        urls = [base, f"{base}/", f"{base}/manifest.json"]
        if precache_urls:
            urls.extend(precache_urls)
        precache_json = json.dumps(urls)
        return f'''const CACHE_NAME = "dezafira-{slug}-v1";
const PRECACHE_URLS = {precache_json};

self.addEventListener("install", event => {{
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
}});

self.addEventListener("activate", event => {{
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
}});

self.addEventListener("fetch", event => {{
  const url = new URL(event.request.url);
  const isShell = url.pathname.startsWith("{base}/icon-") ||
                   url.pathname === "{base}" ||
                   url.pathname === "{base}/" ||
                   url.pathname === "{base}/manifest.json";

  if (isShell) {{
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
    return;
  }}

  event.respondWith(
    fetch(event.request)
      .then(resp => {{
        const clone = resp.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return resp;
      }})
      .catch(() => caches.match(event.request).then(cached => {{
        return cached || new Response(
          `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Offline — DEZAFIRA</title><style>body{{background:#090D16;color:#F3F4F6;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px;text-align:center}}h1{{font-size:1.5rem}}.emoji{{font-size:3rem}}</style></head><body><div><div class="emoji">📡</div><h1>Você está offline</h1><p>Conecte-se à internet para continuar usando o app.</p></div></body></html>`,
          {{ status: 200, headers: {{ "Content-Type": "text/html" }} }}
        );
      }}))
  );
}});
'''

    @staticmethod
    def generate_quiz_pwa(app_id: str, title: str, nicho: str,
                           questions: list, cta_text: str = "Obter Relatório",
                           checkout_url: str = "") -> dict:
        slug = PWAGenerator.slugify(title)
        theme = PWAGenerator.niche_theme(nicho)
        normalized_questions = PWAGenerator._normalize_questions(questions)
        drip_json = json.dumps([])

        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "static", "pwa_template.html")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template nao encontrado: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        theme_json = json.dumps({
            "primary": theme["primary"],
            "primary_dark": theme["accent"],
            "accent": theme["accent"],
            "gradient": theme["gradient"],
            "bg": theme["bg"],
            "surface": theme["surface"],
            "emoji": theme["emoji"],
            "tagline": theme["tagline"]
        })

        description = f"{title} — {theme.get('tagline', 'App Inteligente da DEZAFIRA')}"

        manifest = PWAGenerator.build_manifest(app_id, slug, title, theme, description)
        sw = PWAGenerator.build_service_worker(slug, app_id)

        replacements = {
            "{{APP_ID}}": app_id,
            "{{SLUG}}": slug,
            "{{APP_NAME}}": title,
            "{{NICHE}}": nicho or "Geral",
            "{{THEME}}": theme_json,
            "{{QUESTIONS_JSON}}": json.dumps(normalized_questions, ensure_ascii=False),
            "{{CTA_TEXT}}": cta_text,
            "{{CHECKOUT_URL}}": checkout_url,
            "{{MANIFEST_URL}}": f"/app/{slug}/manifest.json",
            "{{SW_URL}}": f"/app/{slug}/sw.js",
            "{{ICON_192}}": f"/app/{slug}/icon-192.png",
            "{{ICON_512}}": f"/app/{slug}/icon-512.png",
            "{{DRIP_JSON}}": drip_json,
            "{{LOGO_URL}}": "",
            "{{BANNER_URL}}": "",
            "{{DESCRIPTION}}": description,
        }

        html = template
        for placeholder, value in replacements.items():
            html = html.replace(placeholder, str(value))

        unresolved = re.findall(r'\{\{[\w_]+\}\}', html)
        if unresolved:
            for u in unresolved:
                if u in replacements:
                    html = html.replace(u, str(replacements[u]))

        return {
            "success": True,
            "app_id": app_id,
            "app_url": f"/app/{slug}",
            "slug": slug,
            "html": html,
            "manifest": manifest,
            "service_worker": sw,
            "icons": {
                "192": f"/app/{slug}/icon-192.png",
                "512": f"/app/{slug}/icon-512.png",
                "maskable": f"/app/{slug}/icon-512.png"
            }
        }

    @staticmethod
    def generate_from_app_record(record: dict) -> dict:
        app_name = record.get("app_name", "MiniApp")
        niche = record.get("niche", "Geral")
        app_id = record.get("id", "unknown")
        pwa_html = record.get("pwa_html", "")

        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "static", "pwa_template.html")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template nao encontrado: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        slug = PWAGenerator.slugify(app_name)
        theme = PWAGenerator.niche_theme(niche)
        theme_json = json.dumps({
            "primary": theme["primary"],
            "primary_dark": theme["accent"],
            "accent": theme["accent"],
            "gradient": theme["gradient"],
            "bg": theme["bg"],
            "surface": theme["surface"],
            "emoji": theme["emoji"],
            "tagline": theme["tagline"]
        })

        description = f"{app_name} — {theme.get('tagline', 'App Inteligente da DEZAFIRA')}"
        manifest = PWAGenerator.build_manifest(app_id, slug, app_name, theme, description)
        sw = PWAGenerator.build_service_worker(slug, app_id)
        drip_json = json.dumps(record.get("drip_contents", []))

        # If pwa_html is substantial (more than 500 chars), keep it as inner content
        # Otherwise, generate a default quiz with generic questions
        inner_content = ""
        if pwa_html and len(pwa_html.strip()) > 500:
            # Resolve any remaining {{PLACEHOLDERS}} in stored HTML
            inner_content = pwa_html
            for ph in re.findall(r'\{\{[\w_]+\}\}', inner_content):
                inner_content = inner_content.replace(ph, "")
        else:
            inner_content = ""

        replacements = {
            "{{APP_ID}}": app_id,
            "{{SLUG}}": slug,
            "{{APP_NAME}}": app_name,
            "{{NICHE}}": niche or "Geral",
            "{{THEME}}": theme_json,
            "{{QUESTIONS_JSON}}": json.dumps([], ensure_ascii=False),
            "{{CTA_TEXT}}": "Obter Relatório",
            "{{CHECKOUT_URL}}": "",
            "{{MANIFEST_URL}}": f"/app/{slug}/manifest.json",
            "{{SW_URL}}": f"/app/{slug}/sw.js",
            "{{ICON_192}}": f"/app/{slug}/icon-192.png",
            "{{ICON_512}}": f"/app/{slug}/icon-512.png",
            "{{DRIP_JSON}}": drip_json,
            "{{LOGO_URL}}": record.get("logo_url", ""),
            "{{BANNER_URL}}": record.get("banner_url", ""),
            "{{DESCRIPTION}}": description,
        }

        html = template
        for placeholder, value in replacements.items():
            html = html.replace(placeholder, str(value))

        # inject stored HTML content into a content area if substantial
        if inner_content:
            content_marker = '<section id="view-drip" class="view">'
            if content_marker in html:
                wrapped = f'{content_marker}\n<div class="stored-content">{inner_content}</div>\n'
                html = html.replace(content_marker, wrapped)

        return {
            "success": True,
            "app_id": app_id,
            "app_url": f"/app/{slug}",
            "slug": slug,
            "html": html,
            "manifest": manifest,
            "service_worker": sw,
            "icons": {
                "192": f"/app/{slug}/icon-192.png",
                "512": f"/app/{slug}/icon-512.png",
                "maskable": f"/app/{slug}/icon-512.png"
            }
        }

    @staticmethod
    def generate_checkout_page(app_name: str, checkout_url: str, theme: dict = None) -> dict:
        if theme is None:
            theme = PWAGenerator.FALLBACK_THEME
        slug = PWAGenerator.slugify(app_name)
        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkout — {app_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        body {{
            background-color: {theme.get("bg", "#090D16")};
            color: #F3F4F6;
            font-family: 'Plus Jakarta Sans', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .checkout-card {{
            background: {theme.get("surface", "#131A2C")};
            border: 1px solid #1E293B;
            border-radius: 24px;
            max-width: 480px;
            width: 100%;
            padding: 40px;
            text-align: center;
        }}
        h1 {{
            font-size: 1.6rem;
            font-weight: 800;
            margin-bottom: 12px;
        }}
        p {{
            color: #9CA3AF;
            font-size: 0.95rem;
            margin-bottom: 28px;
            line-height: 1.5;
        }}
        .cta {{
            display: block;
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, {theme.get("primary", "#3B82F6")}, {theme.get("accent", "#60A5FA")});
            color: white;
            text-decoration: none;
            font-weight: 700;
            font-size: 1.1rem;
            border-radius: 14px;
            border: none;
            cursor: pointer;
        }}
        .cta:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
        }}
    </style>
</head>
<body>
    <div class="checkout-card">
        <div style="font-size:3rem;margin-bottom:16px">{theme.get("emoji", "⚡")}</div>
        <h1>{app_name}</h1>
        <p>{theme.get("tagline", "Complete sua aquisição para acesso total.")}</p>
        <a href="{checkout_url}" class="cta">Comprar Agora</a>
    </div>
</body>
</html>'''
        return {
            "success": True,
            "slug": slug,
            "html": html
        }
