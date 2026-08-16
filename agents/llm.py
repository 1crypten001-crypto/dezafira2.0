"""LLM Client compartilhado — todos os agentes usam esta interface.
Cascata completa de provedores com fallback automatico."""

import os
import httpx
from typing import List, Dict, Any, Optional

# Prefixo retornado quando TODOS os provedores falham.
# Delegate wrappers (ex: modules.blog_writer._call_llm) checam este
# prefixo para converter a falha em excecao — nao hardcode o literal.
ERROR_PREFIX = "[[ERRO]]"


async def query_llm(
    messages: List[Dict[str, str]],
    max_tokens: int = 4096,
    temperature: float = 0.7,
    model: str = "meta/llama-3.3-70b-instruct",
) -> str:
    """Chama LLM com fallback em cascata:
    1. Agnes AI (agnes-2.5-flash) — IA OFICIAL Dezafira (OpenAI-compatible)
    2. OpenRouter (primario histórico)
    3. Google Gemini
    4. NVIDIA NIM
    5. HuggingFace Inference API
    6. DeepSeek API
    """
    last_error = None

    # Helper para extrair system e user dos messages
    system_prompt = ""
    user_prompt = ""
    for m in messages:
        if m.get("role") == "system":
            system_prompt = m["content"]
        elif m.get("role") == "user":
            user_prompt = m["content"]
    if not user_prompt:
        user_prompt = messages[-1]["content"] if messages else ""

    # ─── TENTATIVA 1: Agnes AI (agnes-2.5-flash) — IA OFICIAL Dezafira ─────
    agnes_key = os.getenv("AGNES_API_KEY", "").strip()
    agnes_model = os.getenv("AGNES_LLM_MODEL", "agnes-2.5-flash")
    if agnes_key:
        try:
            r = await _call_agnes(agnes_key, agnes_model, messages, temperature, max_tokens)
            if r:
                print(f"[LLM] Agnes {agnes_model}: OK")
                return r
            print(f"[LLM] Agnes {agnes_model}: resposta vazia, tentando próximo...")
        except Exception as e:
            last_error = f"Agnes: {e}"
            print(f"[LLM] Agnes falhou: {e}")

    # ─── TENTATIVA 2: OpenRouter ────────────────────────────────────────────
    or_key = os.getenv("OPENROUTER_API_KEY", "")
    if or_key:
        # Modelos gratuitos do OpenRouter em ordem de qualidade
        or_models = [
            "meta-llama/llama-3.3-70b-instruct",
            "mistralai/mistral-small-24b-instruct-2501",
            "deepseek/deepseek-chat",
            "qwen/qwen-2.5-72b-instruct",
            "google/gemini-2.0-flash-lite-preview-02-05",
        ]
        for mdl in or_models:
            try:
                r = await _call_openrouter(or_key, mdl, messages, temperature, max_tokens)
                if r:
                    print(f"[LLM] OpenRouter {mdl}: OK")
                    return r
                elif r is not None:
                    # 402 (sem creditos) ou erro — tenta o proximo modelo
                    print(f"[LLM] OpenRouter {mdl}: resposta sem conteudo, tentando proximo...")
            except Exception as e:
                last_error = f"OpenRouter {mdl}: {e}"
                print(f"[LLM] OpenRouter {mdl} falhou: {e}")
                continue

    # ─── TENTATIVA 2: Google Gemini ─────────────────────────────────────────
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        gemini_models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
        for mdl in gemini_models:
            try:
                r = await _call_gemini(gemini_key, mdl, system_prompt, user_prompt, temperature, max_tokens)
                if r:
                    print(f"[LLM] Gemini {mdl}: OK")
                    return r
            except Exception as e:
                last_error = f"Gemini {mdl}: {e}"
                print(f"[LLM] Gemini {mdl} falhou: {e}")
                continue

    # ─── TENTATIVA 3: NVIDIA NIM ────────────────────────────────────────────
    nvidia_key = os.getenv("NVIDIA_API_KEY", "") or os.getenv("NVAPI_KEY", "")
    if nvidia_key and nvidia_key != "mock_key_for_testing":
        try:
            r = await _call_nvidia(nvidia_key, model, messages, temperature, max_tokens)
            if r:
                print("[LLM] NVIDIA NIM: OK")
                return r
        except Exception as e:
            last_error = f"NVIDIA: {e}"
            print(f"[LLM] NVIDIA falhou: {e}")

    # ─── TENTATIVA 4: HuggingFace ───────────────────────────────────────────
    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
    if hf_token:
        try:
            r = await _call_huggingface(hf_token, system_prompt, user_prompt, temperature, max_tokens)
            if r:
                print("[LLM] HuggingFace: OK")
                return r
        except Exception as e:
            last_error = f"HF: {e}"
            print(f"[LLM] HF falhou: {e}")

    # ─── TENTATIVA 5: DeepSeek ──────────────────────────────────────────────
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    if deepseek_key:
        try:
            r = await _call_deepseek(deepseek_key, messages, temperature, max_tokens)
            if r:
                print("[LLM] DeepSeek: OK")
                return r
        except Exception as e:
            last_error = f"DeepSeek: {e}"
            print(f"[LLM] DeepSeek falhou: {e}")

    error_msg = f"Todos os LLMs falharam. Ultimo erro: {last_error}"
    print(f"[LLM] {error_msg}")
    return f"{ERROR_PREFIX} {error_msg}"


async def _call_agnes(key: str, model: str, messages: list, temp: float, max_tok: int) -> Optional[str]:
    """Agnes AI (agnes-2.5-flash) — OpenAI-compatible: POST /v1/chat/completions."""
    base = os.getenv("AGNES_LLM_BASE", "https://apihub.agnes-ai.com").rstrip("/")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temp,
        "max_tokens": max_tok,
        "frequency_penalty": 0.4,
        "presence_penalty": 0.2,
    }
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{base}/v1/chat/completions", json=payload, headers=headers)
        if r.status_code == 200:
            data = r.json()
            try:
                return data["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError, TypeError):
                print(f"[LLM] Agnes resposta inesperada: {str(data)[:200]}")
                return None
        print(f"[LLM] Agnes HTTP {r.status_code}: {r.text[:200]}")
        return None


async def _call_openrouter(key: str, model: str, messages: list, temp: float, max_tok: int) -> Optional[str]:
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://dezafira.com.br",
        "X-Title": "Dezafira",
    }
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json={"model": model, "messages": messages, "temperature": temp, "max_tokens": max_tok, "frequency_penalty": 0.4, "presence_penalty": 0.2},
            headers=headers,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        return None


async def _call_gemini(key: str, model: str, system_prompt: str, user_prompt: str, temp: float, max_tok: int) -> Optional[str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": temp, "maxOutputTokens": max_tok},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload)
        if r.status_code == 200:
            data = r.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        return None


async def _call_nvidia(key: str, model: str, messages: list, temp: float, max_tok: int) -> Optional[str]:
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            json={"model": model, "messages": messages, "temperature": temp, "max_tokens": max_tok, "frequency_penalty": 0.4, "presence_penalty": 0.2},
            headers=headers,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        return None


async def _call_huggingface(key: str, system_prompt: str, user_prompt: str, temp: float, max_tok: int) -> Optional[str]:
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "inputs": f"{system_prompt}\n\n{user_prompt}",
        "parameters": {"temperature": temp, "max_new_tokens": min(max_tok, 4096), "return_full_text": False, "repetition_penalty": 1.15},
    }
    hf_models = [
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "HuggingFaceH4/zephyr-7b-beta",
        "microsoft/Phi-3-mini-4k-instruct",
    ]
    for model in hf_models:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(f"https://api-inference.huggingface.co/models/{model}", json=payload, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list) and len(data) > 0:
                        text = data[0].get("generated_text", "")
                        if text:
                            return text.strip()
        except Exception:
            continue
    return None


async def _call_deepseek(key: str, messages: list, temp: float, max_tok: int) -> Optional[str]:
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            json={"model": "deepseek-chat", "messages": messages, "temperature": temp, "max_tokens": max_tok, "frequency_penalty": 0.4, "presence_penalty": 0.2},
            headers=headers,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        return None
