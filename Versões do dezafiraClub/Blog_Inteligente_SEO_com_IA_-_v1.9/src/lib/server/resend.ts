import { env } from '$env/dynamic/private';
import { getSettings } from './database';

async function getResendSettings() {
  const settings = await getSettings();
  return {
    apiKey: env.RESEND_API_KEY || settings.resend_api_key || '',
    fromEmail: env.RESEND_FROM_EMAIL || settings.resend_from_email || 'onboarding@resend.dev'
  };
}

export async function isResendConfigured(): Promise<boolean> {
  const settings = await getResendSettings();
  return !!settings.apiKey;
}

export async function sendOtpEmail(toEmail: string, code: string): Promise<boolean> {
  try {
    const settings = await getResendSettings();

    if (!settings.apiKey) {
      console.error('[RESEND] API key is not configured');
      return false;
    }

    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${settings.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: settings.fromEmail,
        to: [toEmail],
        subject: `Código de Acesso: ${code}`,
        html: `
          <div style="font-family: sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e8e8e8; border-radius: 8px;">
            <h2 style="color: #1a1a1a; text-align: center; margin-bottom: 24px;">Seu Código de Acesso</h2>
            <p style="color: #4a4a4a; font-size: 16px; line-height: 1.5;">Olá,</p>
            <p style="color: #4a4a4a; font-size: 16px; line-height: 1.5;">Você solicitou um código de acesso para entrar na Área de Membros. Use o código abaixo para concluir seu login:</p>
            <div style="background: #f5f5f5; border-radius: 6px; padding: 16px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 4px; margin: 24px 0; color: #1a1a1a;">
              ${code}
            </div>
            <p style="color: #888888; font-size: 14px; line-height: 1.5;">Este código expira em 10 minutos. Se você não solicitou este e-mail, por favor ignore-o.</p>
          </div>
        `
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[RESEND] API error response:', errorText);
      return false;
    }

    const result = await response.json();
    console.log('[RESEND] Email sent successfully:', result);
    return true;
  } catch (e) {
    console.error('[RESEND] Error sending OTP email:', e);
    return false;
  }
}

/**
 * Envia um e-mail de notificação de atualização de produto para todos os compradores.
 * Utiliza o campo 'bcc' em lotes de 100 para proteger a privacidade dos usuários.
 */
function escapeHtml(value: string): string {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export type ProductUpdateEmailResult = {
  ok: boolean;
  sent: number;
  failed: number;
  error?: string;
};

/**
 * Envia e-mail de atualização de produto aos compradores (BCC em lotes).
 * Retorna contagem de sucesso/falha — não mascara erro de API como sucesso.
 */
export async function sendProductUpdateEmail(
  toEmails: string[],
  productName: string,
  productSlug: string,
  siteName: string,
  siteUrl: string,
  changelog?: string
): Promise<ProductUpdateEmailResult> {
  try {
    const settings = await getResendSettings();

    if (!settings.apiKey) {
      console.warn('[RESEND] API key is not configured for product update email. Skipping notification.');
      return { ok: false, sent: 0, failed: toEmails.length, error: 'RESEND_NOT_CONFIGURED' };
    }

    if (toEmails.length === 0) {
      console.log('[RESEND] No buyers to notify for product:', productName);
      return { ok: true, sent: 0, failed: 0 };
    }

    const batchSize = 100;
    const base = (siteUrl || '').replace(/\/$/, '');
    const dashboardUrl = `${base}/members/dashboard`;
    const productUrl = productSlug ? `${base}/product/${productSlug}` : dashboardUrl;
    const safeName = escapeHtml(productName);
    const safeSite = escapeHtml(siteName);
    const safeChangelog = changelog ? escapeHtml(changelog) : '';

    let sent = 0;
    let failed = 0;
    let lastError = '';

    for (let i = 0; i < toEmails.length; i += batchSize) {
      const batch = toEmails.slice(i, i + batchSize);

      // Resend free/test: only your own email works with onboarding@resend.dev
      // Production: from must be a verified domain
      const response = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${settings.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          from: settings.fromEmail,
          // Primary recipient required; use from address, buyers in BCC
          to: [settings.fromEmail],
          bcc: batch,
          subject: `Atualização disponível: ${productName}`,
          html: `
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; background-color: #fafafa;">
              <div style="background-color: #ffffff; border: 1px solid #e8e8e8; border-radius: 12px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                <div style="text-align: center; margin-bottom: 32px;">
                  <span style="font-size: 40px;">🚀</span>
                </div>
                <h1 style="color: #1a1a1a; font-size: 22px; font-weight: 700; text-align: center; margin: 0 0 16px 0; line-height: 1.3;">
                  Atualização disponível!
                </h1>
                <p style="color: #4a4a4a; font-size: 16px; line-height: 1.6; text-align: center; margin: 0 0 24px 0;">
                  O recurso <strong>${safeName}</strong> que você adquiriu em <strong>${safeSite}</strong> foi atualizado.
                </p>
                
                <div style="background-color: #f9f9f9; border-radius: 8px; padding: 20px; margin-bottom: 32px; border-left: 4px solid #1a1a1a;">
                  <h3 style="margin: 0 0 8px 0; color: #1a1a1a; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700;">Recurso atualizado</h3>
                  <p style="margin: 0; color: #1a1a1a; font-size: 15px; font-weight: 600;">
                    ${safeName}
                  </p>
                  <p style="margin: 8px 0 0 0; color: #626262; font-size: 13px; line-height: 1.5;">
                    Acesse sua área de membros para baixar a versão atualizada, sem custo adicional.
                  </p>
                </div>

                ${safeChangelog ? `
                <div style="background-color: #f0f7ff; border-radius: 8px; padding: 20px; margin-bottom: 32px; border-left: 4px solid #0070f3;">
                  <h3 style="margin: 0 0 8px 0; color: #0070f3; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700;">O que mudou nesta versão</h3>
                  <p style="margin: 0; color: #1a1a1a; font-size: 14px; line-height: 1.5; white-space: pre-wrap;">
                    ${safeChangelog}
                  </p>
                </div>
                ` : ''}

                <div style="text-align: center; margin-bottom: 32px;">
                  <a href="${escapeHtml(dashboardUrl)}" style="display: inline-block; background-color: #1a1a1a; color: #ffffff; text-decoration: none; padding: 14px 28px; font-size: 14px; font-weight: 600; border-radius: 8px;">
                    Acessar meus downloads
                  </a>
                  ${productSlug ? `
                  <div style="margin-top: 12px;">
                    <a href="${escapeHtml(productUrl)}" style="color: #626262; font-size: 13px;">Ver página do produto</a>
                  </div>` : ''}
                </div>

                <hr style="border: 0; border-top: 1px solid #e8e8e8; margin: 32px 0;" />

                <div style="text-align: center;">
                  <p style="color: #888888; font-size: 13px; margin: 0 0 8px 0; line-height: 1.5;">
                    Atualização gratuita para clientes existentes.
                  </p>
                  <p style="color: #b0b0b0; font-size: 11px; margin: 0;">
                    Enviado por ${safeSite}
                  </p>
                </div>
              </div>
            </div>
          `
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        lastError = errorText;
        failed += batch.length;
        console.error('[RESEND] Product update batch failed:', errorText);
      } else {
        sent += batch.length;
        const result = await response.json().catch(() => ({}));
        console.log(`[RESEND] Product update batch of ${batch.length} sent:`, result?.id || 'ok');
      }
    }

    return {
      ok: failed === 0,
      sent,
      failed,
      error: failed > 0 ? lastError || 'BATCH_FAILED' : undefined
    };
  } catch (e: any) {
    console.error('[RESEND] Error sending product update emails:', e);
    return {
      ok: false,
      sent: 0,
      failed: toEmails.length,
      error: e?.message || 'SEND_ERROR'
    };
  }
}

/**
 * Helper para extrair o ID de vídeo do YouTube de várias URLs
 */
function getYouTubeId(url: string | null): string | null {
  if (!url) return null;
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : null;
}

/**
 * Envia uma campanha de Newsletter para os assinantes.
 * Envia em lotes de 100 via bcc para privacidade.
 */
export async function sendNewsletterCampaignEmail(
  toEmails: string[],
  subject: string,
  content: string,
  youtubeVideoUrl: string | null,
  siteName: string,
  siteUrl: string
): Promise<boolean> {
  try {
    const settings = await getResendSettings();

    if (!settings.apiKey) {
      console.warn('[RESEND] API key is not configured for newsletter campaign. Skipping.');
      return false;
    }

    if (toEmails.length === 0) {
      console.log('[RESEND] No subscribers to send newsletter campaign to.');
      return true;
    }

    // Processar o conteúdo para substituir quebras de linha em parágrafos HTML simples
    const formattedContent = content
      .split('\n\n')
      .map(p => p.trim() ? `<p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">${p.replace(/\n/g, '<br/>')}</p>` : '')
      .join('');

    // Se tiver vídeo do YouTube, criar o card visual
    const youtubeId = youtubeVideoUrl ? getYouTubeId(youtubeVideoUrl) : null;
    let youtubeBlock = '';
    
    if (youtubeId) {
      youtubeBlock = `
        <div style="margin: 24px 0; border: 1px solid #e8e8e8; border-radius: 12px; overflow: hidden; background-color: #000000; text-align: center;">
          <a href="${youtubeVideoUrl}" target="_blank" style="display: block; position: relative; text-decoration: none;">
            <!-- Usamos a imagem da capa do vídeo do Youtube como background -->
            <img src="https://img.youtube.com/vi/${youtubeId}/maxresdefault.jpg" alt="Assistir Vídeo no YouTube" style="width: 100%; max-width: 100%; display: block; border: 0;" />
            <!-- Botão de Play centralizado e estilizado para e-mails -->
            <div style="background-color: rgba(239, 68, 68, 0.95); border-radius: 8px; color: #ffffff; padding: 12px 24px; font-weight: 700; font-family: sans-serif; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; margin: 16px auto; width: fit-content; max-width: 250px; text-align: center; border: 1px solid #dc2626;">
              ▶ Assistir no YouTube
            </div>
          </a>
        </div>
      `;
    }

    const batchSize = 100;
    
    for (let i = 0; i < toEmails.length; i += batchSize) {
      const batch = toEmails.slice(i, i + batchSize);
      
      const response = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${settings.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          from: settings.fromEmail,
          to: [settings.fromEmail], // Envia para si mesmo
          bcc: batch,                // Lista de contatos em cópia oculta
          subject: subject,
          html: `
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 30px 15px; background-color: #f9f9f9;">
              <div style="background-color: #ffffff; border: 1px solid #e8e8e8; border-radius: 12px; padding: 35px; box-shadow: 0 4px 10px rgba(0,0,0,0.01);">
                <!-- Cabeçalho com o nome do Blog -->
                <div style="border-bottom: 1px solid #f0f0f0; padding-bottom: 20px; margin-bottom: 25px; text-align: center;">
                  <a href="${siteUrl}" style="font-size: 20px; font-weight: 800; color: #1a1a1a; text-decoration: none; font-family: sans-serif; letter-spacing: -0.5px;">
                    ${siteName}
                  </a>
                </div>
                
                <!-- Título da Campanha -->
                <h2 style="color: #1a1a1a; font-size: 22px; font-weight: 700; margin: 0 0 20px 0; line-height: 1.35; font-family: sans-serif;">
                  ${subject}
                </h2>
                
                <!-- Conteúdo Principal -->
                <div style="color: #4a4a4a; font-size: 16px; line-height: 1.6; font-family: sans-serif;">
                  ${formattedContent}
                </div>
                
                <!-- Bloco do Vídeo (se aplicável) -->
                ${youtubeBlock}
                
                <!-- Rodapé / Descadastro -->
                <hr style="border: 0; border-top: 1px solid #f0f0f0; margin: 30px 0;" />
                <div style="text-align: center; color: #a0a0a0; font-size: 12px; font-family: sans-serif; line-height: 1.6;">
                  <p style="margin: 0 0 8px 0;">
                    Você recebeu este e-mail porque está inscrito na nossa newsletter.
                  </p>
                  <p style="margin: 0;">
                    Deseja parar de receber estes e-mails? 
                    <a href="${siteUrl}/api/newsletter/unsubscribe?email=\${BCC_RECIPIENT_EMAIL}" style="color: #666666; text-decoration: underline;">
                      Clique aqui para cancelar inscrição
                    </a>.
                  </p>
                  <p style="margin: 12px 0 0 0; color: #cccccc; font-size: 10px;">
                    Enviado por ${siteName} — ${siteUrl}
                  </p>
                </div>
              </div>
            </div>
          `
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[RESEND] API error response for newsletter campaign batch:', errorText);
      } else {
        console.log(`[RESEND] Newsletter campaign batch of ${batch.length} sent successfully`);
      }
    }

    return true;
  } catch (e) {
    console.error('[RESEND] Error sending newsletter campaign:', e);
    return false;
  }
}

/**
 * Envia um e-mail ao comprador quando o acesso ao recurso manual (Google Drive, GitHub, etc.) é liberado pelo administrador.
 */
export async function sendManualAccessDeliveredEmail(
  toEmail: string,
  buyerName: string,
  productName: string,
  accessId: string,
  instructions: string
): Promise<boolean> {
  try {
    const settings = await getResendSettings();

    if (!settings.apiKey) {
      console.warn('[RESEND] API key is not configured for manual access email notification.');
      return false;
    }

    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${settings.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: settings.fromEmail,
        to: [toEmail],
        subject: `🎉 Seu acesso ao "${productName}" foi liberado!`,
        html: `
          <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 32px 24px; background: #ffffff; border: 1px solid #e8e8e8; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
            <div style="text-align: center; margin-bottom: 24px;">
              <span style="font-size: 40px;">🎉</span>
            </div>
            <h2 style="color: #22c55e; text-align: center; font-size: 22px; font-weight: 700; margin: 0 0 8px 0;">Acesso Liberado!</h2>
            <p style="color: #374151; font-size: 15px; line-height: 1.5; margin: 0 0 16px 0;">Olá, <strong>${buyerName}</strong>!</p>
            <p style="color: #374151; font-size: 15px; line-height: 1.5; margin: 0 0 16px 0;">
              Seu acesso ao produto <strong>"${productName}"</strong> foi compartilhado com:
            </p>
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px 18px; margin: 16px 0; font-size: 15px; color: #15803d; font-weight: 600; text-align: center; word-break: break-all;">
              ${accessId}
            </div>
            <div style="background-color: #f9f9f9; border-radius: 8px; padding: 16px; margin: 20px 0; border-left: 4px solid #22c55e; font-size: 14px; color: #4a4a4a; line-height: 1.6; white-space: pre-wrap;">${instructions}</div>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
            <p style="color: #9ca3af; font-size: 12px; text-align: center; margin: 0;">Dúvidas? Responda este e-mail ou entre em contato pelo site.</p>
          </div>
        `
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[RESEND] API error response for manual access notification:', errorText);
      return false;
    }

    const result = await response.json();
    console.log('[RESEND] Manual access notification email sent successfully:', result);
    return true;
  } catch (e) {
    console.error('[RESEND] Error sending manual access notification email:', e);
    return false;
  }
}



