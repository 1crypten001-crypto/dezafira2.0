#!/usr/bin/env python3
"""
Extrai quadros de um vídeo e converte para WebP otimizado para animação por scroll.

Escolhe quadros igualmente espaçados de um MP4, converte para WebP em duas
resoluções (desktop + mobile) e gera um manifest.json com os metadados.

Uso básico:
    python3 extrair_quadros.py \
        --entrada /caminho/video.mp4 \
        --saida area_de_trabalho/2026-03-04/sites-animados/meu-projeto/quadros

Quantidade de quadros customizada:
    python3 extrair_quadros.py \
        --entrada /caminho/video.mp4 \
        --saida area_de_trabalho/.../quadros \
        --quadros 120

Qualidade e resolução customizadas:
    python3 extrair_quadros.py \
        --entrada /caminho/video.mp4 \
        --saida area_de_trabalho/.../quadros \
        --qualidade 75 \
        --res-desktop 1920x1080 \
        --res-mobile 960x540

Só desktop (pular mobile):
    python3 extrair_quadros.py \
        --entrada /caminho/video.mp4 \
        --saida area_de_trabalho/.../quadros \
        --so-desktop

Requisitos:
    Precisa de ffmpeg e ffprobe instalados (brew install ffmpeg).
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def ler_argumentos():
    """Monta e interpreta a linha de comando."""
    cli = argparse.ArgumentParser(
        description="Extrai quadros de um vídeo para animação por scroll"
    )
    cli.add_argument(
        "--entrada", required=True,
        help="Caminho do arquivo MP4 de origem"
    )
    cli.add_argument(
        "--saida", required=True,
        help="Pasta destino para os quadros extraídos"
    )
    cli.add_argument(
        "--quadros", type=int, default=0,
        help="Quantidade alvo de quadros (padrão: calculado pela duração)"
    )
    cli.add_argument(
        "--qualidade", type=int, default=80,
        help="Qualidade WebP 1-100 (padrão: 80)"
    )
    cli.add_argument(
        "--res-desktop", default="1920x1080",
        help="Resolução desktop (padrão: 1920x1080)"
    )
    cli.add_argument(
        "--res-mobile", default="960x540",
        help="Resolução mobile (padrão: 960x540)"
    )
    cli.add_argument(
        "--so-desktop", action="store_true",
        help="Pula a geração dos quadros mobile"
    )
    cli.add_argument(
        "--so-mobile", action="store_true",
        help="Pula a geração dos quadros desktop"
    )
    return cli.parse_args()


def interpretar_resolucao(texto):
    """Converte 'WIDTHxHEIGHT' em uma tupla (w, h)."""
    try:
        largura, altura = texto.lower().split("x")
        return int(largura), int(altura)
    except (ValueError, AttributeError):
        print(f"Erro: formato de resolução inválido: {texto}. Use LARGURAxALTURA.", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def checar_dependencias():
    """Confirma que ffmpeg e ffprobe estão instalados."""
    for programa in ("ffmpeg", "ffprobe"):
        if not shutil.which(programa):
            print(
                f"Erro: '{programa}' não encontrado. Instale com: brew install ffmpeg",
                file=sys.stderr,
            )
            sys.exit(1)


def checar_entrada(caminho):
    """Valida que o arquivo existe e parece mesmo um vídeo."""
    arquivo = Path(caminho)
    if not arquivo.exists():
        print(f"Erro: arquivo não encontrado: {caminho}", file=sys.stderr)
        sys.exit(1)
    if arquivo.stat().st_size < 1024:
        print(f"Erro: arquivo pequeno demais para ser um vídeo: {caminho}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Análise do vídeo
# ---------------------------------------------------------------------------

def inspecionar_video(caminho):
    """Roda o ffprobe e devolve os metadados do vídeo."""
    comando = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(caminho),
    ]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        dados = json.loads(resultado.stdout)
    except subprocess.CalledProcessError as erro:
        print(f"Erro: ffprobe falhou: {erro.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Erro: não foi possível ler a saída do ffprobe", file=sys.stderr)
        sys.exit(1)

    # Procura o stream de vídeo
    stream_video = None
    for stream in dados.get("streams", []):
        if stream.get("codec_type") == "video":
            stream_video = stream
            break

    if not stream_video:
        print("Erro: nenhum stream de vídeo encontrado no arquivo", file=sys.stderr)
        sys.exit(1)

    # Interpreta o frame rate (pode vir como "30/1" ou "29.97")
    fps_texto = stream_video.get("r_frame_rate", "30/1")
    if "/" in fps_texto:
        numerador, denominador = fps_texto.split("/")
        fps = float(numerador) / float(denominador) if float(denominador) != 0 else 30.0
    else:
        fps = float(fps_texto)

    duracao = float(dados.get("format", {}).get("duration", 0))
    if duracao == 0:
        # Plano B: duração do próprio stream
        duracao = float(stream_video.get("duration", 0))

    largura = int(stream_video.get("width", 1920))
    altura = int(stream_video.get("height", 1080))
    codec = stream_video.get("codec_name", "desconhecido")
    total_quadros = int(round(duracao * fps))

    return {
        "duracao": round(duracao, 2),
        "largura": largura,
        "altura": altura,
        "fps": round(fps, 2),
        "codec": codec,
        "total_quadros": total_quadros,
        "arquivo": Path(caminho).name,
    }


# ---------------------------------------------------------------------------
# Cálculo de quadros / altura
# ---------------------------------------------------------------------------

def calcular_quadros_ideais(duracao, override_usuario=0):
    """Calcula quantidade de quadros e altura do scroll a partir da duração.

    Fórmula: min(200, max(60, duracao * 10))
    - 0-5s:   60-90 quadros  (revelações simples)
    - 5-15s:  120-150 quadros (padrão, sweet spot)
    - 15-30s: 150-200 quadros (sequências complexas)
    - 30s+:   teto de 200    (aumenta a altura do scroll no lugar)
    """
    if override_usuario > 0:
        quantidade = override_usuario
    else:
        quantidade = min(200, max(60, int(duracao * 10)))

    # Altura do scroll: ~3.3vh por quadro, mínimo de 300vh
    altura_scroll = max(300, int(quantidade * 3.3))
    # Arredonda para o múltiplo de 50vh mais próximo
    altura_scroll = round(altura_scroll / 50) * 50

    return quantidade, altura_scroll


# ---------------------------------------------------------------------------
# Extração
# ---------------------------------------------------------------------------

def tem_libwebp():
    """Verifica se o FFmpeg foi compilado com o encoder libwebp."""
    saida = subprocess.run(
        ["ffmpeg", "-encoders"], capture_output=True, text=True,
    )
    return "libwebp" in saida.stdout


def extrair_quadros(entrada, pasta_saida, quantidade, resolucao, qualidade, rotulo=""):
    """Extrai quadros igualmente espaçados do vídeo como WebP.

    Estratégia:
    1. Se o FFmpeg tem libwebp: extração em um único passe (mais rápido)
    2. Caso contrário: extrai como PNG e converte para WebP via Pillow (universal)
    """
    largura, altura = resolucao
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    # Pega a duração para calcular o fps alvo
    sonda = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(entrada),
    ]
    resposta = subprocess.run(sonda, capture_output=True, text=True)
    duracao = float(resposta.stdout.strip()) if resposta.stdout.strip() else 10.0

    fps_alvo = quantidade / duracao
    fps_alvo = max(1, min(60, fps_alvo))

    marcador = f"  [{rotulo}] " if rotulo else "  "
    com_libwebp = tem_libwebp()

    if com_libwebp:
        # Caminho rápido: FFmpeg → WebP num só passe
        print(f"{marcador}Extraindo {quantidade} quadros a {largura}x{altura} (FFmpeg libwebp)...", file=sys.stderr)
        comando = [
            "ffmpeg", "-y",
            "-i", str(entrada),
            "-vf", f"fps={fps_alvo:.4f},scale={largura}:{altura}:flags=lanczos",
            "-c:v", "libwebp",
            "-quality", str(qualidade),
            "-compression_level", "6",
            "-an",
            "-frames:v", str(quantidade),
            str(pasta_saida / "frame-%04d.webp"),
        ]
    else:
        # Caminho universal: FFmpeg → PNG, depois Pillow → WebP
        print(f"{marcador}Extraindo {quantidade} quadros a {largura}x{altura} (FFmpeg + Pillow)...", file=sys.stderr)
        comando = [
            "ffmpeg", "-y",
            "-i", str(entrada),
            "-vf", f"fps={fps_alvo:.4f},scale={largura}:{altura}:flags=lanczos",
            "-an",
            "-frames:v", str(quantidade),
            str(pasta_saida / "frame-%04d.png"),
        ]

    try:
        resultado = subprocess.run(
            comando, capture_output=True, text=True,
            timeout=300,
        )
        if resultado.returncode != 0:
            print(f"Erro: FFmpeg falhou:\n{resultado.stderr[-500:]}", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Erro: FFmpeg estourou o tempo (limite de 5 min)", file=sys.stderr)
        sys.exit(1)

    # Se veio PNG, converte para WebP usando o Pillow
    if not com_libwebp:
        try:
            from PIL import Image as ImagemPIL
        except ImportError:
            print(
                "Erro: nem libwebp (FFmpeg) nem Pillow estão disponíveis.\n"
                "Solução: pip install Pillow  OU  brew reinstall ffmpeg",
                file=sys.stderr,
            )
            sys.exit(1)

        pngs = sorted(pasta_saida.glob("frame-*.png"))
        print(f"{marcador}Convertendo {len(pngs)} PNGs para WebP via Pillow...", file=sys.stderr)

        for png in pngs:
            webp = png.with_suffix(".webp")
            img = ImagemPIL.open(png)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(str(webp), "WEBP", quality=qualidade, method=6)
            png.unlink()  # Remove o PNG para economizar disco

    # Conta os quadros realmente extraídos
    quadros = sorted(pasta_saida.glob("frame-*.webp"))
    total = len(quadros)

    if total == 0:
        print(f"Erro: nenhum quadro extraído em {pasta_saida}", file=sys.stderr)
        sys.exit(1)

    # Calcula tamanho total
    bytes_totais = sum(f.stat().st_size for f in quadros)
    bytes_medios = bytes_totais // total if total > 0 else 0

    print(
        f"{marcador}{total} quadros extraídos "
        f"({bytes_totais / 1024 / 1024:.1f}MB no total, "
        f"{bytes_medios / 1024:.0f}KB em média por quadro)",
        file=sys.stderr,
    )

    return {
        "quantidade": total,
        "bytes_totais": bytes_totais,
        "bytes_medios": bytes_medios,
        "resolucao": f"{largura}x{altura}",
    }


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def gerar_manifest(pasta_saida, info_video, quadros_alvo, altura_scroll,
                   qualidade, info_desktop=None, info_mobile=None):
    """Escreve o manifest.json com todos os metadados."""
    manifest = {
        "origem": {
            "arquivo": info_video["arquivo"],
            "duracao": info_video["duracao"],
            "resolucao": f"{info_video['largura']}x{info_video['altura']}",
            "fps": info_video["fps"],
            "codec": info_video["codec"],
            "total_quadros_origem": info_video["total_quadros"],
        },
        "quadros": {
            "quantidade_alvo": quadros_alvo,
            "formato": "webp",
            "qualidade": qualidade,
            "padrao_nomes": "frame-{NNNN}.webp",
        },
        "altura_scroll_recomendada": f"{altura_scroll}vh",
        "criado_em": datetime.now().isoformat(timespec="seconds"),
    }

    if info_desktop:
        manifest["desktop"] = {
            "resolucao": info_desktop["resolucao"],
            "quantidade_real": info_desktop["quantidade"],
            "bytes_totais": info_desktop["bytes_totais"],
            "bytes_medios": info_desktop["bytes_medios"],
            "total_mb": round(info_desktop["bytes_totais"] / 1024 / 1024, 2),
        }

    if info_mobile:
        manifest["mobile"] = {
            "resolucao": info_mobile["resolucao"],
            "quantidade_real": info_mobile["quantidade"],
            "bytes_totais": info_mobile["bytes_totais"],
            "bytes_medios": info_mobile["bytes_medios"],
            "total_mb": round(info_mobile["bytes_totais"] / 1024 / 1024, 2),
        }

    caminho_manifest = Path(pasta_saida) / "manifest.json"
    with open(caminho_manifest, "w") as arq:
        json.dump(manifest, arq, indent=2)

    print(f"\n  Manifest salvo em: {caminho_manifest}", file=sys.stderr)
    return manifest


# ---------------------------------------------------------------------------
# Resumo / warnings
# ---------------------------------------------------------------------------

def imprimir_resumo(info_video, quadros_alvo, altura_scroll, manifest):
    """Mostra um resumo legível para humanos."""
    print("\n" + "=" * 56, file=sys.stderr)
    print("  ANÁLISE DO VÍDEO", file=sys.stderr)
    print("=" * 56, file=sys.stderr)
    print(f"  Origem:      {info_video['arquivo']}", file=sys.stderr)
    print(f"  Duração:     {info_video['duracao']}s", file=sys.stderr)
    print(f"  Resolução:   {info_video['largura']}x{info_video['altura']}", file=sys.stderr)
    print(f"  FPS:         {info_video['fps']}fps", file=sys.stderr)
    print(f"  Codec:       {info_video['codec']}", file=sys.stderr)
    print(f"  Quadros origem: {info_video['total_quadros']}", file=sys.stderr)
    print("-" * 56, file=sys.stderr)
    print("  RESULTADO DA EXTRAÇÃO", file=sys.stderr)
    print("-" * 56, file=sys.stderr)
    print(f"  Alvo:        {quadros_alvo} quadros", file=sys.stderr)
    print(f"  Scroll:      {altura_scroll}vh recomendado", file=sys.stderr)

    if "desktop" in manifest:
        d = manifest["desktop"]
        print(f"  Desktop:     {d['quantidade_real']} quadros @ {d['resolucao']} ({d['total_mb']}MB)", file=sys.stderr)

    if "mobile" in manifest:
        m = manifest["mobile"]
        print(f"  Mobile:      {m['quantidade_real']} quadros @ {m['resolucao']} ({m['total_mb']}MB)", file=sys.stderr)

    print("=" * 56, file=sys.stderr)

    # Avisos
    mb_desktop = manifest.get("desktop", {}).get("total_mb", 0)
    mb_mobile = manifest.get("mobile", {}).get("total_mb", 0)
    if mb_desktop > 15:
        print(f"\n  AVISO: o pacote desktop ({mb_desktop}MB) passou do alvo de 15MB.", file=sys.stderr)
        print("  Considere: --qualidade 60 ou --quadros (reduzir)", file=sys.stderr)
    if mb_mobile > 5:
        print(f"\n  AVISO: o pacote mobile ({mb_mobile}MB) passou do alvo de 5MB.", file=sys.stderr)
        print("  Considere: --qualidade 60 ou --quadros (reduzir)", file=sys.stderr)


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def principal():
    args = ler_argumentos()

    # Validações
    checar_dependencias()
    checar_entrada(args.entrada)

    # Analisa o vídeo
    print("\nInspecionando o vídeo...", file=sys.stderr)
    info_video = inspecionar_video(args.entrada)

    # Define a quantidade de quadros
    quadros_alvo, altura_scroll = calcular_quadros_ideais(
        info_video["duracao"], args.quadros
    )

    pasta_saida = Path(args.saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    res_desktop = interpretar_resolucao(args.res_desktop)
    res_mobile = interpretar_resolucao(args.res_mobile)

    info_desktop = None
    info_mobile = None

    # Quadros desktop
    if not args.so_mobile:
        dir_desktop = pasta_saida / "desktop"
        info_desktop = extrair_quadros(
            args.entrada, dir_desktop, quadros_alvo,
            res_desktop, args.qualidade, rotulo="desktop"
        )

    # Quadros mobile
    if not args.so_desktop:
        dir_mobile = pasta_saida / "mobile"
        info_mobile = extrair_quadros(
            args.entrada, dir_mobile, quadros_alvo,
            res_mobile, args.qualidade, rotulo="mobile"
        )

    # Gera o manifest
    manifest = gerar_manifest(
        pasta_saida, info_video, quadros_alvo, altura_scroll,
        args.qualidade, info_desktop, info_mobile,
    )

    # Mostra o resumo
    imprimir_resumo(info_video, quadros_alvo, altura_scroll, manifest)

    # Saída legível por máquina no stdout, para o agente interpretar
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    principal()