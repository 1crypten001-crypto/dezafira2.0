import crypto from 'crypto';
import { env } from '$env/dynamic/private';

/**
 * courseAccess.ts — tokens de acesso ao player de curso do DezafiraAdm.
 *
 * O Adm protege GET /curso/{course_id} exigindo `?token=`. Este helper
 * gera o token no momento da entrega (mesmo HMAC, mesma chave que o Adm
 * valida: IMPORT_API_KEY aqui == CLUBE_IMPORT_KEY lá).
 */

const TTL_SECONDS = 30 * 24 * 3600; // 30 dias

function secret(): string {
  return env.IMPORT_API_KEY || '';
}

/** Gera o token de acesso assinado para um curso do Adm. */
export function generateCourseAccessToken(courseId: string, userRef: string): string {
  const exp = Math.floor(Date.now() / 1000) + TTL_SECONDS;
  const payload = `${courseId}:${exp}:${userRef}`;
  const sig = crypto.createHmac('sha256', secret()).update(payload).digest('hex');
  return `${exp}.${userRef}.${sig}`;
}

/**
 * Anexa `?token=` ao external_link quando ele aponta para o player de curso
 * do Adm (/curso/...). Retorna o link original caso contrário (ou se a chave
 * não estiver configurada — nesse caso mantém o link sem token e o Adm, em
 * fail-closed, negará o acesso; configura IMPORT_API_KEY para liberar).
 */
export function decorateCourseLink(externalLink: string | null | undefined, userRef: string): string | null {
  if (!externalLink || !externalLink.includes('/curso/')) {
    return externalLink || null;
  }
  const match = externalLink.match(/\/curso\/([^/?]+)/);
  const courseId = match ? decodeURIComponent(match[1]) : '';
  if (!courseId || !secret()) {
    return externalLink || null;
  }
  const token = generateCourseAccessToken(courseId, userRef);
  const sep = externalLink.includes('?') ? '&' : '?';
  return `${externalLink}${sep}token=${encodeURIComponent(token)}`;
}
