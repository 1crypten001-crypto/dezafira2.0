"""
MÓDULO: asaas_client.py
DESCRIÇÃO: Cliente da API Asaas v3 — pagamentos na venda dos produtos da
fábrica (1Convite, ebooks, cursos, PWAs).

Token: `ASAAS_API_KEY` no .env (formato `$aact_prod_...` = produção,
`$aact_sandbox_...` = sandbox). Base URL é escolhida pelo prefixo do token.

Fluxo típico (venda via checkout):
  1. `create_customer(nome, email, cpf_cnpj)` → id do cliente (upsert por email)
  2. `create_pix_charge(customer_id, value_cents, ...)` → cobrança PIX
     (retorna invoiceUrl + QR code payload/encodedImage)
  3. Cliente paga → Asaas chama o webhook registrado (`/api/v1/asaas/webhook`)
  4. `handle_webhook(payload)` confirma e libera o acesso na nossa base

Referência: https://docs.asaas.com/reference
"""

import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger("asaas_client")

ASAAS_PRODUCTION_URL = "https://api.asaas.com/v3"
ASAAS_SANDBOX_URL = "https://sandbox.asaas.com/api/v3"

# Eventos de webhook que consideramos "pago"
PAID_EVENTS = {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED", "PAYMENT_CREDIT_CARD_CAPTURED", "PAYMENT_OVERDUE"}


def _base_url() -> str:
    token = os.getenv("ASAAS_API_KEY", "")
    if token.startswith("$aact_sandbox_"):
        return ASAAS_SANDBOX_URL
    return ASAAS_PRODUCTION_URL


def _cents_to_asaas(value_cents: int) -> str:
    """Converte centavos (int) para o valor decimal string do Asaas ('19.90')."""
    return f"{value_cents / 100:.2f}"


def _due_date(days: int = 1) -> str:
    return (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")


class AsaasError(Exception):
    """Erro retornado pela API Asaas."""


class AsaasClient:
    """Client mínimo da API Asaas v3 (customer, cobrança PIX, webhook)."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 20.0):
        self.api_key = api_key or os.getenv("ASAAS_API_KEY", "")
        if not self.api_key:
            raise ValueError("ASAAS_API_KEY não configurado (defina no .env)")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=_base_url(),
            headers={"access_token": self.api_key, "Content-Type": "application/json"},
            timeout=self.timeout,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> Dict:
        try:
            resp = await self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise AsaasError(f"Falha de conexão com o Asaas: {exc}") from exc
        if resp.status_code >= 400:
            detail = resp.text[:400]
            raise AsaasError(f"Asaas {resp.status_code}: {detail}")
        data = resp.json()
        if isinstance(data, dict) and data.get("errors"):
            msgs = "; ".join(e.get("description", str(e)) for e in data["errors"])
            raise AsaasError(f"Asaas erros: {msgs}")
        return data

    # ── CUSTOMERS ────────────────────────────────────────────────────────────

    async def find_customer_by_email(self, email: str) -> Optional[Dict]:
        """Busca cliente pelo e-mail (Asaas filtra por `email`)."""
        data = await self._request("GET", "/customers", params={"email": email.strip().lower(), "limit": 1})
        rows = data.get("data") or []
        return rows[0] if rows else None

    async def create_customer(self, name: str, email: str, cpf_cnpj: Optional[str] = None,
                              phone: Optional[str] = None, external_reference: Optional[str] = None) -> Dict:
        """Cria cliente (ou devolve o existente pelo e-mail)."""
        existing = await self.find_customer_by_email(email)
        if existing:
            return existing
        payload: Dict = {"name": name, "email": email.strip().lower()}
        if cpf_cnpj:
            digits = re.sub(r"\D", "", cpf_cnpj)
            payload["cpfCnpj"] = digits
        if phone:
            payload["mobilePhone"] = re.sub(r"\D", "", phone)
        if external_reference:
            payload["externalReference"] = external_reference
        return await self._request("POST", "/customers", json=payload)

    # ── PAYMENTS (cobranças) ─────────────────────────────────────────────────

    async def create_pix_charge(self, customer_id: str, value_cents: int, description: str,
                                external_reference: Optional[str] = None,
                                due_days: int = 1) -> Dict:
        """Cria cobrança PIX e devolve os dados de pagamento (QR code incluso)."""
        payment = await self._request("POST", "/payments", json={
            "customer": customer_id,
            "billingType": "PIX",
            "value": _cents_to_asaas(value_cents),
            "dueDate": _due_date(due_days),
            "description": description[:200],
            "externalReference": external_reference,
        })
        pix = {}
        try:
            pix = await self._request("GET", f"/payments/{payment['id']}/pixQrCode")
        except AsaasError as exc:
            logger.warning("Falha ao buscar QR PIX: %s", exc)
        return {
            "payment_id": payment["id"],
            "status": payment["status"],
            "invoiceUrl": payment.get("invoiceUrl", ""),
            "billingType": "PIX",
            "value": payment.get("value", 0),
            "dueDate": payment.get("dueDate", ""),
            "pix": pix,
        }

    async def create_credit_card_charge(self, customer_id: str, value_cents: int, description: str,
                                        credit_card: Dict, credit_card_holder: Dict,
                                        external_reference: Optional[str] = None) -> Dict:
        """Cria cobrança no cartão de crédito (uma vez — sem assinatura)."""
        payment = await self._request("POST", "/payments", json={
            "customer": customer_id,
            "billingType": "CREDIT_CARD",
            "value": _cents_to_asaas(value_cents),
            "dueDate": _due_date(1),
            "description": description[:200],
            "externalReference": external_reference,
            "creditCard": credit_card,
            "creditCardHolderInfo": credit_card_holder,
        })
        return {
            "payment_id": payment["id"],
            "status": payment["status"],
            "invoiceUrl": payment.get("invoiceUrl", ""),
            "billingType": "CREDIT_CARD",
            "value": payment.get("value", 0),
        }

    async def get_payment(self, payment_id: str) -> Dict:
        return await self._request("GET", f"/payments/{payment_id}")

    # ── WEBHOOK ──────────────────────────────────────────────────────────────

    async def create_webhook(self, url: str, events: Optional[List[str]] = None,
                             email: Optional[str] = None) -> Dict:
        """Registra webhook no Asaas (idempotente por URL)."""
        existing = await self._request("GET", "/webhooks", params={"limit": 100})
        for w in existing.get("data") or []:
            if w.get("url") == url:
                return w
        events = events or ["PAYMENT_CREATED", "PAYMENT_RECEIVED", "PAYMENT_CONFIRMED",
                            "PAYMENT_OVERDUE", "PAYMENT_REFUNDED", "PAYMENT_RESTORED",
                            "PAYMENT_REJECTED", "PAYMENT_DELETED"]
        payload: Dict = {"url": url, "events": events, "apiVersion": 3, "enabled": True}
        if email:
            payload["email"] = email
        return await self._request("POST", "/webhooks", json=payload)

    async def handle_webhook(self, payload: Dict) -> Dict:
        """Processa evento do Asaas. Devolve o que foi liberado (ou nada)."""
        event = payload.get("event", "")
        payment = payload.get("payment") or {}
        payment_id = payment.get("id") or payload.get("paymentId")
        result: Dict = {"event": event, "payment_id": payment_id, "processed": False}
        if event in PAID_EVENTS and payment_id:
            full = await self.get_payment(payment_id)
            result["status"] = full.get("status")
            result["externalReference"] = full.get("externalReference")
            result["value"] = full.get("value")
            result["customer"] = full.get("customer")
            result["processed"] = True
        return result

    # ── ACCOUNT (validação do token) ─────────────────────────────────────────

    async def get_account(self) -> Dict:
        return await self._request("GET", "/myAccount")


# ── helpers assíncronos de curto circuito (uso direto em endpoints) ─────────

async def asaas_get_account() -> Dict:
    client = AsaasClient()
    try:
        return await client.get_account()
    finally:
        await client.aclose()


async def asaas_upsert_customer(name: str, email: str, cpf_cnpj: Optional[str] = None,
                                phone: Optional[str] = None, external_reference: Optional[str] = None) -> Dict:
    client = AsaasClient()
    try:
        return await client.create_customer(name, email, cpf_cnpj, phone, external_reference)
    finally:
        await client.aclose()


async def asaas_create_pix_charge(customer_id: str, value_cents: int, description: str,
                                  external_reference: Optional[str] = None, due_days: int = 1) -> Dict:
    client = AsaasClient()
    try:
        return await client.create_pix_charge(customer_id, value_cents, description,
                                              external_reference, due_days)
    finally:
        await client.aclose()
