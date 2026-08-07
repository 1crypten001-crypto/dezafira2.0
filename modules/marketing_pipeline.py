"""
MarketingPipeline — Esteira de 6 fases de Marketing Digital baseada no Sabri Suby Framework.
Agentes brasileiros: Seu Tião, Dona Benta, Tonho da Propaganda, Zé do Traço, Chica dos Correios e Seu Valdir.
100% integrado com Obscura Engine e a cascata de LLMs gratuitas.
"""
import os
import re
import json
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from modules.blog_writer import _call_llm


def parse_stage5_emails(content: str) -> list:
    """Extrai a sequência de até 4 e-mails da Fase 5 (Chica dos Correios).

    O LLM retorna um texto livre com marcadores "E-mail N:" seguidos de
    "Assunto: ..." e "Corpo: ...". Este parser tolera variações (título na
    mesma linha do marcador, "Email N", "## E-mail N") e devolve
    [{subject, body}, ...] normalizados com índice 1..4 para o nurturing
    (Resend via Clube).
    """
    if not content:
        return []
    text = content.replace("\r\n", "\n")

    # Divide por marcadores de e-mail. O marcador é OBRIGATÓRIO — evita
    # corromper o corpo quando contém "1\n" solto (ex: "passo 1\n").
    parts = re.split(
        r"(?i)(?:^|\n)\s*(?:#{1,3}\s*)?e-?mail\s*(\d+)\s*[.:\-]?\s*[^\n]*\n",
        text,
    )
    emails = []
    # parts[0] = preâmbulo (ignorado); depois alterna número, bloco, número, bloco...
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        block = parts[i + 1] if i + 1 < len(parts) else ""
        subject = ""
        body = ""

        m_subject = re.search(r"(?i)assunto\s*[::\-]\s*(.+?)(?:\n|$)", block)
        if m_subject:
            subject = m_subject.group(1).strip()
        m_body = re.search(r"(?i)corpo\s*[::\-]\s*(.+)$", block, re.DOTALL)
        if m_body:
            body = m_body.group(1).strip()
        elif m_subject:
            body = block[m_subject.end():].strip()
        else:
            # Sem rótulos: usa a linha do marcador (título) como assunto e o resto como corpo
            first_line = block.strip().split("\n")[0].strip()
            subject = first_line[:200]
            body = block.strip()[len(first_line):].strip()

        # Limpeza: remove prefixo "Corpo:"/"Assunto:" residual e qualquer
        # cabeçalho de e-mail seguinte que tenha sobrado no bloco.
        body = re.sub(r"(?i)^(?:corpo|assunto)\s*[::\-]?\s*", "", body).strip()
        body = re.split(r"(?i)\n\s*(?:#{1,3}\s*)?e-?mail\s*\d+\s*[.:\-]?", body)[0].strip()
        body = re.sub(r"\n{3,}", "\n\n", body).strip()

        if subject or body:
            emails.append({"index": num, "subject": subject[:200], "body": body})

    if not emails:
        # Fallback 1: blocos por linha "Assunto:" (sem marcador E-mail)
        blocks = re.split(r"(?i)\n\s*(?:assunto|subject)\s*[::\-]\s*", text)
        # Se o texto começa direto com "Assunto:", blocks[0] já é o 1º e-mail
        start = 0 if text.strip().lower().startswith(("assunto", "subject")) else 1
        for j, blk in enumerate(blocks[start:], start=1):
            if not blk.strip():
                continue
            lines = blk.strip().split("\n")
            subject = re.sub(r"(?i)^(?:assunto|subject)\s*[::\-]?\s*", "", lines[0].strip())[:200] if lines else ""
            body = "\n".join(lines[1:]).strip()
            body = re.sub(r"(?i)^(?:corpo|assunto)\s*[::\-]?\s*", "", body).strip()
            emails.append({"index": j, "subject": subject, "body": body})

    if not emails:
        # Fallback 2: sem estrutura nenhuma — um único e-mail com o texto todo
        emails.append({"index": 1, "subject": "", "body": text.strip()[:2000]})

    # Normaliza índices para 1..4 sequencial (evita 400 no Clube por índice inválido)
    for k, em in enumerate(emails[:4], start=1):
        em["index"] = k
    return emails[:4]


async def send_nurturing_to_clube(campaign_id: str, clube_url: str, import_key: str) -> dict:
    """Dispara a sequência de nurturing (fase 5) para o Clube via ponte.

    Lê a campanha persistida no banco, extrai os e-mails da fase 5 e chama
    POST /api/import/nurture no Clube para cada um (Resend → assinantes ativos).
    """
    try:
        from modules.database import get_marketing_campaign
        camp = get_marketing_campaign(campaign_id)
    except Exception as e:
        return {"success": False, "error": f"Erro ao ler campanha: {str(e)}"}
    if not camp:
        return {"success": False, "error": "Campanha não encontrada"}

    stage5 = (camp.get("stages") or {}).get("5") or ""
    emails = parse_stage5_emails(stage5)
    if not emails:
        return {"success": False, "error": "Nenhum e-mail encontrado na Fase 5 — rode a fase 5 primeiro."}

    if not import_key:
        return {"success": False, "error": "CLUBE_IMPORT_KEY não configurado no Adm."}

    import httpx
    results = []
    sent_total = 0
    base = (clube_url or "https://www.dezafira.com.br").rstrip("/")
    for em in emails:
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                r = await client.post(
                    f"{base}/api/import/nurture",
                    json={"subject": em["subject"], "content": em["body"], "email_index": em["index"]},
                    headers={"Content-Type": "application/json", "x-import-key": import_key},
                )
                try:
                    data = r.json() if r.status_code < 500 else {"error": r.text[:200]}
                except Exception:
                    data = {"error": f"HTTP {r.status_code}: {r.text[:200]}", "success": False}
            ok = r.status_code in (200, 201) and bool(data.get("success"))
            sent_total += data.get("sent") or 0
            results.append({"email_index": em["index"], "subject": em["subject"], "ok": ok, "response": data})
        except Exception as e:
            results.append({"email_index": em["index"], "subject": em["subject"], "ok": False, "error": str(e)})

    return {"success": True, "campaign_id": campaign_id, "emails": len(emails), "sent": sent_total, "results": results}

class MarketingPipeline:
    def __init__(self):
        self.state = {
            "niche": "",
            "avatar": "",
            "lead_magnet": "",
            "ads": "",
            "landing_page": "",
            "emails": "",
            "offer": "",
            "google_suggests": [],
            "reddit_questions": []
        }

    async def run_stage(self, stage: int, niche: str) -> dict:
        self.state["niche"] = niche
        
        if stage == 1:
            return await self._run_stage_1(niche)
        elif stage == 2:
            return await self._run_stage_2()
        elif stage == 3:
            return await self._run_stage_3()
        elif stage == 4:
            return await self._run_stage_4()
        elif stage == 5:
            return await self._run_stage_5()
        elif stage == 6:
            return await self._run_stage_6()
        else:
            return {"error": "Fase inválida"}

    async def _run_stage_1(self, niche: str) -> dict:
        # FASE 1: Seu Tião (O Caçador de Avatares) - Usa Obscura + LLM
        print(f"[Seu Tião] Buscando buscas ativas no Google para o nicho '{niche}'...")
        suggests = []
        try:
            from services.obscura_bridge import get_google_suggestions
            suggests = await get_google_suggestions(niche, "PT")
        except Exception as e:
            print(f"[Seu Tião] Aviso ao minerar com Obscura: {e}")

        if not suggests:
            suggests = [f"{niche} dicas", f"{niche} guia", f"{niche} como fazer", f"{niche} preço", f"{niche} funciona"]
        
        self.state["google_suggests"] = suggests
        self.state["reddit_questions"] = []

        system_prompt = (
            "Você é o Seu Tião, um Caçador de Avatares de marketing muito perspicaz, observador e com linguagem simples brasileira.\n"
            "Seu trabalho é criar o perfil completo do Dream Buyer (Comprador Ideal) baseado nas buscas reais fornecidas."
        )
        user_prompt = f"""
        Nicho: {niche}
        Dúvidas e buscas do público: {', '.join(suggests)}

        Crie um perfil estruturado do nosso Dream Buyer (Avatar de Cliente) contendo:
        1. As 3 maiores dores dele.
        2. Os 3 maiores medos ocultos.
        3. Os 3 maiores sonhos e objetivos dele.
        4. Três objeções comuns de compra que ele faria.
        
        Escreva tudo de forma clara em português brasileiro.
        """
        response = await _call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=1500)
        self.state["avatar"] = response
        return {
            "success": True, 
            "content": response, 
            "google_suggests": suggests,
            "reddit_questions": []
        }

    async def _run_stage_2(self) -> dict:
        # FASE 2: Dona Benta (Iscas / Lead Magnets)
        avatar = self.state.get("avatar", "Avatar geral")
        niche = self.state.get("niche", "Geral")
        system_prompt = (
            "Você é a Dona Benta, uma especialista em criar iscas digitais irresistíveis e acolhedoras para capturar leads.\n"
            "Você sabe exatamente qual 'doce' (conteúdo gratuito) vai atrair as pessoas."
        )
        user_prompt = f"""
        Com base no perfil do Dream Buyer do nicho '{niche}':
        {avatar}

        Proponha 3 ideias de Iscas Digitais de Alto Valor (HVCO - High Value Content Offer), como e-books, checklists ou mini-cursos gratuitos.
        Para cada ideia forneça:
        1. Um título altamente chamativo.
        2. O que será entregue (estrutura/tópicos).
        3. Por que esse material vai resolver a maior dor do nosso avatar.
        """
        response = await _call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=1500)
        self.state["lead_magnet"] = response
        return {"success": True, "content": response}

    async def _run_stage_3(self) -> dict:
        # FASE 3: Tonho da Propaganda (Copywriter de Anúncios AIDA)
        lead_magnet = self.state.get("lead_magnet", "")
        niche = self.state.get("niche", "")
        system_prompt = (
            "Você é o Tonho da Propaganda, redator publicitário de interior com excelente lábia e escrita afiada brasileira.\n"
            "Seu trabalho é criar chamadas de anúncios no modelo AIDA (Atenção, Interesse, Desejo, Ação) para redes sociais."
        )
        user_prompt = f"""
        Escreva 3 variações de anúncios persuasivos para redes sociais focados em divulgar nossa isca digital ou produto de '{niche}':
        Isca/Produto de referência:
        {lead_magnet}

        Use a estrutura AIDA:
        - [Atenção]: Headline que para o feed.
        - [Interesse]: Foca na dor ou desejo do avatar.
        - [Desejo]: Benefício do material.
        - [Ação]: Chamada de Ação (CTA) clara.
        """
        response = await _call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=1500)
        self.state["ads"] = response
        return {"success": True, "content": response}

    async def _run_stage_4(self) -> dict:
        # FASE 4: Zé do Traço (Landing Page)
        avatar = self.state.get("avatar", "")
        niche = self.state.get("niche", "")
        system_prompt = (
            "Você é o Zé do Traço, arquiteto de Landing Pages de alta conversão. Você foca em estrutura limpa, direta e persuasiva."
        )
        user_prompt = f"""
        Escreva a cópia e estrutura da Landing Page de captura para o produto/isca de '{niche}':
        Contexto do Comprador:
        {avatar}

        Forneça a estrutura de blocos da página:
        - [Destaque/Hero]: Título de Alto Impacto (Promissor) e Subtítulo explicativo.
        - [Bloco do Problema]: Focado em empatia e conexão com a dor do cliente.
        - [Bloco da Solução]: O que é o material/produto e por que ele funciona.
        - [Bloco de Prova Social]: Ideia de depoimentos e dados que trazem credibilidade.
        - [Bloco de Garantia/Segurança]: Apresentação do risco zero.
        - [CTA Final]: Chamada para o formulário de cadastro.
        """
        response = await _call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=1500)
        self.state["landing_page"] = response
        return {"success": True, "content": response}

    async def _run_stage_5(self) -> dict:
        # FASE 5: Chica dos Correios (Automação de E-mails / Nurturing)
        avatar = self.state.get("avatar", "")
        niche = self.state.get("niche", "")
        system_prompt = (
            "Você é a Chica dos Correios, carteira popular da vila, muito atenciosa e próxima de todo mundo.\n"
            "Você escreve sequências de e-mails diários que geram relacionamento, intimidade e confiança."
        )
        user_prompt = f"""
        Escreva uma sequência de 4 e-mails de relacionamento e vendas para a nossa lista de leads interessados em '{niche}':
        Perfil do cliente:
        {avatar}

        Estrutura sugerida para cada e-mail:
        - E-mail 1: Entrega de valor e apresentação (Boas-vindas).
        - E-mail 2: Aprofundamento do problema e quebra da maior objeção.
        - E-mail 3: O segredo/solução definitiva (Apresentando nossa oferta).
        - E-mail 4: Última chamada (Urgência + Garantia de Risco Zero).
        
        Forneça um Assunto e o Corpo do e-mail para cada um deles.
        """
        response = await _call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=2000)
        self.state["emails"] = response
        return {"success": True, "content": response}

    async def _run_stage_6(self) -> dict:
        # FASE 6: Seu Valdir (O Fechador da Oferta Irrecusável)
        avatar = self.state.get("avatar", "")
        niche = self.state.get("niche", "")
        system_prompt = (
            "Você é o Seu Valdir, comerciante experiente, prestativo e ótimo de negócio.\n"
            "Seu objetivo é desenhar a 'Oferta Irrecusável' (Godfather Offer) que elimina riscos e cria urgência."
        )
        user_prompt = f"""
        Crie a Oferta Irrecusável para o produto/serviço de '{niche}':
        Dores do Comprador:
        {avatar}

        Descreva a oferta detalhando:
        1. A Garantia de Risco Zero Forte (ex: 7 dias incondicional ou devolução em dobro caso não tenha resultados).
        2. Bônus Exclusivos que agregam mais valor que o próprio produto.
        3. Ancoragem de Preço (de R$ X por apenas R$ Y).
        4. O Gatilho de Escassez e Urgência para forçar a ação imediata.
        """
        response = await _call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=1500)
        self.state["offer"] = response
        return {"success": True, "content": response}

    @staticmethod
    def send_smtp_email(to_email: str, subject: str, html_body: str) -> bool:
        """Dispara e-mail via SMTP gratuito usando configurações do ambiente."""
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")
        sender_email = os.getenv("SMTP_SENDER", smtp_user)

        if not smtp_user or not smtp_pass:
            print("[SMTP] Variáveis SMTP_USER ou SMTP_PASS ausentes no .env. Envio abortado.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = to_email

            part = MIMEText(html_body, "html")
            msg.attach(part)

            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(sender_email, to_email, msg.as_string())
            server.quit()
            print(f"[SMTP] E-mail enviado com sucesso para {to_email}!")
            return True
        except Exception as e:
            print(f"[SMTP] Erro ao enviar e-mail: {e}")
            return False
