import { env } from '$env/dynamic/private';
import { getUserByUsername, createUser, updateUserPassword, createDBSession, getDBSession, deleteDBSession, clearExpiredDBSessions } from './database';
import bcrypt from 'bcryptjs';
import crypto from 'crypto';

// ============================================
// ADMIN CREDENTIALS COM VALIDAÇÃO DE SEGURANÇA
// ============================================

const ADMIN_USERNAME = env.ADMIN_USERNAME || 'admin';
const ADMIN_PASSWORD = env.ADMIN_PASSWORD;

// Lista de senhas fracas comuns para bloquear
const WEAK_PASSWORDS = [
  'admin123', 'admin', 'password', 'password123', '12345678',
  '123456789', 'qwerty123', 'abc123456', 'senha123', 'adminadmin',
  'root', 'test', 'demo', 'welcome', 'letmein', 'iloveyou',
];

/**
 * Verifica se a senha do admin está configurada e é forte o suficiente
 * Lança erro em produção se a senha não estiver configurada ou for fraca
 */
function validateAdminPasswordConfig(): { valid: boolean; error?: string; warning?: string } {
  // Verificar se ADMIN_PASSWORD está definido
  if (!ADMIN_PASSWORD) {
    return {
      valid: false,
      error: 'ADMIN_PASSWORD não está configurado no .env! Defina uma senha forte antes de rodar a aplicação.'
    };
  }

  // Verificar se é uma senha fraca comum
  if (WEAK_PASSWORDS.includes(ADMIN_PASSWORD.toLowerCase())) {
    return {
      valid: false,
      error: `ADMIN_PASSWORD está usando uma senha fraca e comum ("${ADMIN_PASSWORD}"). Use uma senha forte e única!`
    };
  }

  // Verificar força da senha
  const strength = validatePasswordStrength(ADMIN_PASSWORD);
  if (!strength.valid) {
    return {
      valid: false,
      error: `ADMIN_PASSWORD não atende os requisitos mínimos: ${strength.message}`
    };
  }

  // Verificar se é muito curta (menos de 12 chars para produção)
  if (ADMIN_PASSWORD.length < 12) {
    return {
      valid: false,
      error: 'ADMIN_PASSWORD deve ter pelo menos 12 caracteres para produção.'
    };
  }

  return { valid: true };
}

// Validar na inicialização do módulo
const passwordValidation = validateAdminPasswordConfig();
if (!passwordValidation.valid) {
  const isProd = process.env.NODE_ENV === 'production';
  if (isProd) {
    console.error('❌ ERRO DE CONFIGURAÇÃO DE SEGURANÇA:');
    console.error(passwordValidation.error);
    console.error('A aplicação continuará executando, mas configure uma senha forte o quanto antes.');
  } else {
    console.warn('⚠️ AVISO DE CONFIGURAÇÃO DE SEGURANÇA (desenvolvimento):');
    console.warn(passwordValidation.error);
  }
}

const SALT_ROUNDS = 10;

// ============================================
// SESSION MANAGEMENT (Database-backed)
// ============================================

const SESSION_DURATION_MS = 30 * 24 * 60 * 60 * 1000; // 30 dias

/**
 * Gera um token de sessão criptograficamente seguro
 */
export function generateSessionToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

/**
 * Cria uma nova sessão e retorna o token
 */
export async function createSession(username: string): Promise<string> {
  const token = generateSessionToken();
  const now = Date.now();
  const expiresAt = now + SESSION_DURATION_MS;

  await createDBSession(token, username, expiresAt);

  return token;
}

/**
 * Valida um token de sessão. Retorna o username se válido, null se inválido/expirado.
 */
export async function validateSession(token: string): Promise<string | null> {
  if (!token) return null;

  const session = await getDBSession(token);
  if (!session) return null;

  // Verificar expiração
  if (Date.now() > session.expires_at) {
    await deleteDBSession(token);
    return null;
  }

  return session.username;
}

/**
 * Invalida (destrói) uma sessão
 */
export async function destroySession(token: string): Promise<void> {
  await deleteDBSession(token);
}

/**
 * Limpa sessões expiradas (housekeeping)
 */
export function cleanExpiredSessions(): void {
  clearExpiredDBSessions();
}

// Limpar sessões expiradas a cada 30 minutos
if (typeof setInterval !== 'undefined') {
  setInterval(cleanExpiredSessions, 30 * 60 * 1000);
}

// ============================================
// RATE LIMITING
// ============================================
interface RateLimitEntry {
  count: number;
  firstAttempt: number;
}

const loginAttempts = new Map<string, RateLimitEntry>();
const MAX_ATTEMPTS = 5;
const WINDOW_MS = 15 * 60 * 1000;

export function checkRateLimit(ip: string): { allowed: boolean; remaining: number; waitSeconds: number } {
  const now = Date.now();
  const entry = loginAttempts.get(ip);

  if (!entry) {
    loginAttempts.set(ip, { count: 1, firstAttempt: now });
    return { allowed: true, remaining: MAX_ATTEMPTS - 1, waitSeconds: 0 };
  }

  if (now - entry.firstAttempt > WINDOW_MS) {
    loginAttempts.set(ip, { count: 1, firstAttempt: now });
    return { allowed: true, remaining: MAX_ATTEMPTS - 1, waitSeconds: 0 };
  }

  if (entry.count >= MAX_ATTEMPTS) {
    const waitSeconds = Math.ceil((WINDOW_MS - (now - entry.firstAttempt)) / 1000);
    return { allowed: false, remaining: 0, waitSeconds };
  }

  entry.count++;
  return { allowed: true, remaining: MAX_ATTEMPTS - entry.count, waitSeconds: 0 };
}

export function resetRateLimit(ip: string): void {
  loginAttempts.delete(ip);
}

// ============================================
// PASSWORD UTILITIES
// ============================================
export function validatePasswordStrength(password: string): { valid: boolean; message: string } {
  if (password.length < 8) {
    return { valid: false, message: 'A senha deve ter pelo menos 8 caracteres' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: 'A senha deve conter pelo menos uma letra maiúscula' };
  }
  if (!/[a-z]/.test(password)) {
    return { valid: false, message: 'A senha deve conter pelo menos uma letra minúscula' };
  }
  if (!/[0-9]/.test(password)) {
    return { valid: false, message: 'A senha deve conter pelo menos um número' };
  }
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    return { valid: false, message: 'A senha deve conter pelo menos um caractere especial (!@#$%^&*...)' };
  }
  
  // Verificar caracteres repetitivos (ex: aaa, 111)
  if (/(.)\1{2,}/.test(password)) {
    return { valid: false, message: 'A senha não deve conter 3 ou mais caracteres repetidos' };
  }
  
  // Verificar senhas muito comuns com padrão sequencial (apenas纯粹的-sequências isoladas)
  const sequentialPatterns = ['123', '234', '345', '456', '567', '678', '789', 'abc', 'bcd', 'cde', 'def'];
  const lowerPassword = password.toLowerCase();
  for (const pattern of sequentialPatterns) {
    const regex = new RegExp(`(^${pattern}|${pattern}$|${pattern}(?=[^a-z0-9])|(?<=[^a-z0-9])${pattern})`, 'i');
    if (regex.test(lowerPassword) && lowerPassword !== pattern) {
      return { valid: false, message: 'A senha não deve conter sequências óbvias de caracteres' };
    }
  }
  
  return { valid: true, message: 'Senha válida' };
}

export async function verifyLogin(username: string, password: string): Promise<boolean> {
  try {
    const user = await getUserByUsername(username);
    
    if (!user) {
      console.log(`[Auth] User not found: ${username}`);
      return false;
    }

    if (!user.password) {
      console.error(`[Auth] User ${username} found but has no password property! User object keys:`, Object.keys(user));
      return false;
    }

    if (typeof user.password !== 'string') {
      console.error(`[Auth] User ${username} password is not a string! Type:`, typeof user.password);
      return false;
    }

    return await bcrypt.compare(password, user.password);
  } catch (error) {
    console.error(`[Auth] Error in verifyLogin for user ${username}:`, error);
    throw error;
  }
}

export async function getUser(username: string) {
  return getUserByUsername(username);
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export function getAdminCredentials() {
  return {
    username: ADMIN_USERNAME,
    password: ADMIN_PASSWORD
  };
}

export async function initAdminUser() {
  // Verificar validação de senha primeiro
  const validation = validateAdminPasswordConfig();
  if (!validation.valid) {
    // Se já passou pela validação do módulo, só log warning em dev
    if (process.env.NODE_ENV !== 'production') {
      console.warn('⚠️  Admin user inicializado com senha fraca (apenas para desenvolvimento)');
    }
    return;
  }

  const admin = await getUserByUsername(ADMIN_USERNAME);
  const hashedPassword = await hashPassword(ADMIN_PASSWORD);

  if (!admin) {
    await createUser(ADMIN_USERNAME, hashedPassword, 'admin');
    console.log(`Usuário admin "${ADMIN_USERNAME}" criado com sucesso`);
  } else {
    // ADMIN_PASSWORD é a fonte da verdade: sincroniza a senha mesmo se o usuário já existe
    await updateUserPassword(ADMIN_USERNAME, hashedPassword);
    console.log(`Senha do admin "${ADMIN_USERNAME}" sincronizada a partir de ADMIN_PASSWORD`);
  }
}
