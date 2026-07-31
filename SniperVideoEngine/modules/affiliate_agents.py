import hashlib
import hmac
import time
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class SeuSilvaAgent:
    """
    Agente Seu Silva (Amazon Affiliate Specialist).
    Responsável por gerenciar chaves e formatar links de afiliado da Amazon.
    """
    @staticmethod
    def get_status(channel_dict: Dict[str, Any]) -> Dict[str, str]:
        tag = channel_dict.get("amazon_tag")
        key = channel_dict.get("amazon_key")
        
        if not tag:
            return {"status": "inactive", "message": "Seu Silva diz: Configuração da Amazon ausente (necessita de Tag de Associado)."}
        
        if not key:
            return {
                "status": "warning",
                "message": f"Seu Silva diz: Rodando em modo de curadoria manual (Tag: {tag}). PA-API não configurada."
            }
        
        return {"status": "active", "message": f"Seu Silva diz: Integração com Amazon PA-API ativa! (Tag: {tag})"}

    @staticmethod
    def generate_link(product_url_or_id: str, tag: str) -> str:
        """Gera link de afiliado da Amazon usando a tag do associado."""
        # Se for um ID de produto (ASIN)
        if len(product_url_or_id) == 10 and product_url_or_id.isalnum():
            asin = product_url_or_id
        else:
            # Tentar extrair ASIN da URL da Amazon
            asin_match = __import__('re').search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', product_url_or_id)
            asin = asin_match.group(1) if asin_match else None
        
        if asin:
            return f"https://www.amazon.com.br/dp/{asin}?tag={tag}"
        
        # Fallback se não conseguir extrair o ASIN
        if "tag=" not in product_url_or_id:
            separator = "&" if "?" in product_url_or_id else "?"
            return f"{product_url_or_id}{separator}tag={tag}"
        return product_url_or_id


class DonaBentaAgent:
    """
    Agente Dona Benta (Shopee Affiliate Specialist).
    Gerencia chaves de API, assinaturas HMAC e validação.
    """
    @staticmethod
    def get_status(channel_dict: Dict[str, Any]) -> Dict[str, str]:
        app_id = channel_dict.get("shopee_app_id")
        secret = channel_dict.get("shopee_app_secret")
        
        if not app_id or not secret:
            return {"status": "inactive", "message": "Dona Benta diz: Configuração da Shopee ausente (AppID/Secret)."}
        
        return {"status": "active", "message": "Dona Benta diz: Conexão com Shopee API ativa! Pronta para assinar chamadas."}

    @staticmethod
    def sign_request(secret: str, api_path: str, body: str, timestamp: int) -> str:
        """Gera a assinatura digital HMAC-SHA256 exigida pela API da Shopee."""
        base_string = f"{api_path}{timestamp}{body}"
        signature = hmac.new(
            secret.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature


class SeuNogueiraAgent:
    """
    Agente Seu Nogueira (Mercado Livre Affiliate Specialist).
    Cuida do fluxo OAuth2 e renovação automática de access_tokens expirados.
    """
    @staticmethod
    def get_status(channel_dict: Dict[str, Any]) -> Dict[str, str]:
        client_id = channel_dict.get("mercadolivre_client_id")
        access_token = channel_dict.get("mercadolivre_access_token")
        expires = channel_dict.get("mercadolivre_token_expires")
        
        if not client_id:
            return {"status": "inactive", "message": "Seu Nogueira diz: Conexão com Mercado Livre ausente (Client ID)."}
        
        if not access_token:
            return {"status": "warning", "message": "Seu Nogueira diz: Autenticação pendente com o Mercado Livre (necessita autorizar OAuth)."}
        
        # Verificar expiração
        if expires:
            if isinstance(expires, str):
                try:
                    expires = datetime.fromisoformat(expires)
                except ValueError:
                    expires = datetime.utcnow()
            
            if datetime.utcnow() >= expires:
                return {"status": "warning", "message": "Seu Nogueira diz: Token expirado. Tentando renovação automática..."}
        
        return {"status": "active", "message": "Seu Nogueira diz: Token do Mercado Livre válido e pronto para uso!"}

    @classmethod
    async def check_and_refresh_token(cls, channel_id: str, channel_dict: Dict[str, Any]) -> Optional[str]:
        """
        Verifica se o token do Mercado Livre expirou e, em caso afirmativo,
        realiza o refresh_token de forma automática no banco.
        """
        access_token = channel_dict.get("mercadolivre_access_token")
        refresh_token = channel_dict.get("mercadolivre_refresh_token")
        client_id = channel_dict.get("mercadolivre_client_id")
        client_secret = channel_dict.get("mercadolivre_client_secret")
        expires_at = channel_dict.get("mercadolivre_token_expires")
        
        if not client_id or not client_secret or not refresh_token:
            return access_token
            
        # Converter expires_at se for string
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at)
            except ValueError:
                expires_at = None
                
        # Se expira nos próximos 15 minutos ou já expirou, renovamos
        should_refresh = not expires_at or (datetime.utcnow() + timedelta(minutes=15)) >= expires_at
        
        if should_refresh:
            print(f"[Seu Nogueira] Token expirado ou próximo da expiração para o canal {channel_id}. Renovando...")
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.mercadolibre.com/oauth/token",
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        data={
                            "grant_type": "refresh_token",
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "refresh_token": refresh_token
                        },
                        timeout=10.0
                    )
                    
                if resp.status_code == 200:
                    data = resp.json()
                    new_access = data.get("access_token")
                    new_refresh = data.get("refresh_token")
                    expires_in = data.get("expires_in", 21600) # padrão ML 6h (21600s)
                    
                    new_expires = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    # Atualizar banco
                    from modules.database import update_db_blog_channel
                    update_db_blog_channel(
                        channel_id,
                        mercadolivre_access_token=new_access,
                        mercadolivre_refresh_token=new_refresh,
                        mercadolivre_token_expires=new_expires
                    )
                    print(f"[Seu Nogueira] Token renovado com sucesso para {channel_id}!")
                    return new_access
                else:
                    print(f"[Seu Nogueira] Erro ao renovar token. Status: {resp.status_code}. Resp: {resp.text}")
            except Exception as e:
                print(f"[Seu Nogueira] Falha de comunicação na renovação: {e}")
                
        return access_token
