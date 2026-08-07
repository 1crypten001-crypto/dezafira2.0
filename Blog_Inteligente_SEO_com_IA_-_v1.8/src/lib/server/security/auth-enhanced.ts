/**
 * Enhanced Authentication System
 * 
 * Provides advanced authentication features including:
 * - Password strength validation (min 12 chars, uppercase, lowercase, number, special)
 * - Account lockout after 5 failed attempts in 15 minutes
 * - Session invalidation on password change
 * - Authentication failure logging with IP and timestamp
 * - Redis-based session storage for scalability
 * 
 * Requirements: 2.2, 2.3, 2.4, 2.7, 2.13
 */

import bcrypt from 'bcryptjs';
import crypto from 'crypto';
import { redis } from './rateLimit';
import { query, queryOne } from '../db';

// ============================================
// CONSTANTS
// ============================================

const BCRYPT_WORK_FACTOR = 12; // Requirement 2.4
const SESSION_TOKEN_BYTES = 32; // Requirement 2.5
const SESSION_DURATION_MS = 24 * 60 * 60 * 1000; // 24 hours (Requirement 2.6)
const MAX_LOGIN_ATTEMPTS = 5; // Requirement 2.3
const LOCKOUT_WINDOW_MS = 15 * 60 * 1000; // 15 minutes (Requirement 2.3)

// ============================================
// PASSWORD VALIDATION
// ============================================

/**
 * Password strength requirements (Requirement 2.2)
 */
export interface PasswordRequirements {
	minLength: number;
	requireUppercase: boolean;
	requireLowercase: boolean;
	requireNumber: boolean;
	requireSpecial: boolean;
}

export const DEFAULT_PASSWORD_REQUIREMENTS: PasswordRequirements = {
	minLength: 12,
	requireUppercase: true,
	requireLowercase: true,
	requireNumber: true,
	requireSpecial: true
};

/**
 * Password validation result
 */
export interface PasswordValidationResult {
	valid: boolean;
	errors: string[];
}

/**
 * Validate password strength according to requirements
 * 
 * @param password - Password to validate
 * @param requirements - Password requirements (optional, uses defaults)
 * @returns Validation result with errors if invalid
 */
export function validatePasswordStrength(
	password: string,
	requirements: PasswordRequirements = DEFAULT_PASSWORD_REQUIREMENTS
): PasswordValidationResult {
	const errors: string[] = [];

	// Check minimum length
	if (password.length < requirements.minLength) {
		errors.push(`Password must be at least ${requirements.minLength} characters long`);
	}

	// Check maximum length (prevent DoS)
	if (password.length > 128) {
		errors.push('Password must not exceed 128 characters');
	}

	// Check uppercase requirement
	if (requirements.requireUppercase && !/[A-Z]/.test(password)) {
		errors.push('Password must contain at least one uppercase letter');
	}

	// Check lowercase requirement
	if (requirements.requireLowercase && !/[a-z]/.test(password)) {
		errors.push('Password must contain at least one lowercase letter');
	}

	// Check number requirement
	if (requirements.requireNumber && !/[0-9]/.test(password)) {
		errors.push('Password must contain at least one number');
	}

	// Check special character requirement
	if (requirements.requireSpecial && !/[^A-Za-z0-9]/.test(password)) {
		errors.push('Password must contain at least one special character');
	}

	// Check for common weak patterns
	if (/(.)\1{2,}/.test(password)) {
		errors.push('Password must not contain 3 or more repeated characters');
	}

	// Check for sequential patterns
	const sequentialPatterns = [
		'123',
		'234',
		'345',
		'456',
		'567',
		'678',
		'789',
		'abc',
		'bcd',
		'cde',
		'def'
	];
	const lowerPassword = password.toLowerCase();
	for (const pattern of sequentialPatterns) {
		if (lowerPassword.includes(pattern)) {
			errors.push('Password must not contain obvious sequential patterns');
			break;
		}
	}

	// Check against common weak passwords
	const weakPasswords = [
		'password',
		'admin',
		'welcome',
		'letmein',
		'qwerty',
		'iloveyou'
	];
	if (weakPasswords.some((weak) => lowerPassword.includes(weak))) {
		errors.push('Password must not contain common weak words');
	}

	return {
		valid: errors.length === 0,
		errors
	};
}

/**
 * Hash password using bcrypt with configured work factor
 * 
 * @param password - Plain text password
 * @returns Hashed password
 */
export async function hashPassword(password: string): Promise<string> {
	return bcrypt.hash(password, BCRYPT_WORK_FACTOR);
}

/**
 * Verify password against hash
 * 
 * @param password - Plain text password
 * @param hash - Hashed password
 * @returns True if password matches
 */
export async function verifyPassword(password: string, hash: string): Promise<boolean> {
	return bcrypt.compare(password, hash);
}

// ============================================
// ACCOUNT LOCKOUT
// ============================================

/**
 * Account lockout information
 */
export interface LockoutInfo {
	locked: boolean;
	attempts: number;
	unlockAt?: Date;
}

/**
 * Get lockout key for Redis
 */
function getLockoutKey(identifier: string): string {
	return `lockout:${identifier}`;
}

/**
 * Record failed login attempt
 * 
 * @param identifier - User identifier (email or IP address)
 * @returns Lockout information
 */
export async function recordFailedLogin(identifier: string): Promise<LockoutInfo> {
	const key = getLockoutKey(identifier);
	const now = Date.now();

	// Increment attempt counter
	const attempts = await redis.incr(key);

	// Set expiration on first attempt
	if (attempts === 1) {
		await redis.pexpire(key, LOCKOUT_WINDOW_MS);
	}

	// Check if account should be locked
	if (attempts >= MAX_LOGIN_ATTEMPTS) {
		const ttl = await redis.pttl(key);
		const unlockAt = new Date(now + ttl);

		return {
			locked: true,
			attempts,
			unlockAt
		};
	}

	return {
		locked: false,
		attempts
	};
}

/**
 * Check if account is locked
 * 
 * @param identifier - User identifier (email or IP address)
 * @returns Lockout information
 */
export async function checkAccountLockout(identifier: string): Promise<LockoutInfo> {
	const key = getLockoutKey(identifier);
	const attempts = parseInt((await redis.get(key)) || '0');

	if (attempts >= MAX_LOGIN_ATTEMPTS) {
		const ttl = await redis.pttl(key);
		const unlockAt = new Date(Date.now() + ttl);

		return {
			locked: true,
			attempts,
			unlockAt
		};
	}

	return {
		locked: false,
		attempts
	};
}

/**
 * Reset failed login attempts (on successful login)
 * 
 * @param identifier - User identifier (email or IP address)
 */
export async function resetFailedLogins(identifier: string): Promise<void> {
	const key = getLockoutKey(identifier);
	await redis.del(key);
}

// ============================================
// AUTHENTICATION LOGGING
// ============================================

/**
 * Authentication event types
 */
export enum AuthEventType {
	LOGIN_SUCCESS = 'login_success',
	LOGIN_FAILURE = 'login_failure',
	LOGOUT = 'logout',
	PASSWORD_CHANGE = 'password_change',
	ACCOUNT_LOCKED = 'account_locked',
	SESSION_EXPIRED = 'session_expired'
}

/**
 * Log authentication event
 * 
 * @param event - Event type
 * @param userId - User ID (if applicable)
 * @param email - User email
 * @param ipAddress - Client IP address
 * @param userAgent - Client user agent
 * @param metadata - Additional metadata
 */
export async function logAuthEvent(
	event: AuthEventType,
	userId: number | null,
	email: string,
	ipAddress: string,
	userAgent: string,
	metadata: Record<string, any> = {}
): Promise<void> {
	try {
		await query(
			`INSERT INTO audit_logs (tenant_id, user_id, action, entity_type, entity_id, changes, ip_address, user_agent, created_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)`,
			[
				metadata.tenantId || null,
				userId,
				event,
				'authentication',
				userId,
				JSON.stringify({ email, ...metadata }),
				ipAddress,
				userAgent
			]
		);
	} catch (error) {
		console.error('Failed to log auth event:', error);
		// Don't throw - logging failure shouldn't break authentication
	}
}

// ============================================
// SESSION MANAGEMENT
// ============================================

/**
 * Session data interface
 */
export interface SessionData {
	sessionId: string;
	userId: number;
	email: string;
	tenantId: string;
	createdAt: Date;
	expiresAt: Date;
}

/**
 * Generate cryptographically secure session token
 * 
 * @returns Session token (hex string)
 */
export function generateSessionToken(): string {
	return crypto.randomBytes(SESSION_TOKEN_BYTES).toString('hex');
}

/**
 * Get session key for Redis
 */
function getSessionKey(sessionId: string): string {
	return `session:${sessionId}`;
}

/**
 * Create new session
 * 
 * @param userId - User ID
 * @param email - User email
 * @param tenantId - Tenant ID
 * @returns Session token
 */
export async function createSession(
	userId: number,
	email: string,
	tenantId: string
): Promise<string> {
	const sessionId = generateSessionToken();
	const now = Date.now();
	const expiresAt = now + SESSION_DURATION_MS;

	const sessionData: SessionData = {
		sessionId,
		userId,
		email,
		tenantId,
		createdAt: new Date(now),
		expiresAt: new Date(expiresAt)
	};

	// Store in Redis
	const key = getSessionKey(sessionId);
	await redis.setex(
		key,
		Math.ceil(SESSION_DURATION_MS / 1000),
		JSON.stringify(sessionData)
	);

	// Also store in database for persistence
	await query(
		`INSERT INTO sessions (id, tenant_id, user_id, expires_at, created_at)
     VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
     ON CONFLICT (id) DO UPDATE SET expires_at = $4`,
		[sessionId, tenantId, userId, expiresAt]
	);

	return sessionId;
}

/**
 * Validate session token
 * 
 * @param sessionId - Session token
 * @returns Session data if valid, null if invalid/expired
 */
export async function validateSession(sessionId: string): Promise<SessionData | null> {
	if (!sessionId) return null;

	// Try Redis first (fast path)
	const key = getSessionKey(sessionId);
	const cached = await redis.get(key);

	if (cached) {
		const session: SessionData = JSON.parse(cached);

		// Check expiration
		if (new Date(session.expiresAt) < new Date()) {
			await destroySession(sessionId);
			return null;
		}

		return session;
	}

	// Fallback to database
	const session = await queryOne<{
		id: string;
		tenant_id: string;
		user_id: number;
		expires_at: number;
		created_at: string;
	}>(
		`SELECT s.id, s.tenant_id, s.user_id, s.expires_at, s.created_at, u.email
     FROM sessions s
     JOIN users u ON s.user_id = u.id
     WHERE s.id = $1`,
		[sessionId]
	);

	if (!session) return null;

	// Check expiration
	if (session.expires_at < Date.now()) {
		await destroySession(sessionId);
		return null;
	}

	// Reconstruct session data
	const sessionData: SessionData = {
		sessionId: session.id,
		userId: session.user_id,
		email: (session as any).email,
		tenantId: session.tenant_id,
		createdAt: new Date(session.created_at),
		expiresAt: new Date(session.expires_at)
	};

	// Restore to Redis
	await redis.setex(
		key,
		Math.ceil((session.expires_at - Date.now()) / 1000),
		JSON.stringify(sessionData)
	);

	return sessionData;
}

/**
 * Destroy session
 * 
 * @param sessionId - Session token
 */
export async function destroySession(sessionId: string): Promise<void> {
	// Remove from Redis
	const key = getSessionKey(sessionId);
	await redis.del(key);

	// Remove from database
	await query('DELETE FROM sessions WHERE id = $1', [sessionId]);
}

/**
 * Invalidate all sessions for a user (e.g., on password change)
 * Requirement 2.7
 * 
 * @param userId - User ID
 */
export async function invalidateAllUserSessions(userId: number): Promise<void> {
	// Get all session IDs for user
	const sessions = await query<{ id: string }>(
		'SELECT id FROM sessions WHERE user_id = $1',
		[userId]
	);

	// Delete from Redis
	const keys = sessions.map((s) => getSessionKey(s.id));
	if (keys.length > 0) {
		await redis.del(...keys);
	}

	// Delete from database
	await query('DELETE FROM sessions WHERE user_id = $1', [userId]);
}

/**
 * Clean expired sessions (housekeeping)
 */
export async function cleanExpiredSessions(): Promise<void> {
	const now = Date.now();
	await query('DELETE FROM sessions WHERE expires_at < $1', [now]);
}

// Run cleanup every 30 minutes
if (typeof setInterval !== 'undefined') {
	setInterval(cleanExpiredSessions, 30 * 60 * 1000);
}

// ============================================
// AUTHENTICATION FLOW
// ============================================

/**
 * Login result interface
 */
export interface LoginResult {
	success: boolean;
	sessionToken?: string;
	user?: {
		id: number;
		email: string;
		username: string;
		role: string;
		tenantId: string;
	};
	error?: string;
	lockoutInfo?: LockoutInfo;
}

/**
 * Authenticate user and create session
 * 
 * @param email - User email
 * @param password - Plain text password
 * @param ipAddress - Client IP address
 * @param userAgent - Client user agent
 * @param tenantId - Tenant ID
 * @returns Login result
 */
export async function login(
	email: string,
	password: string,
	ipAddress: string,
	userAgent: string,
	tenantId: string
): Promise<LoginResult> {
	// Check account lockout
	const lockout = await checkAccountLockout(email);
	if (lockout.locked) {
		await logAuthEvent(
			AuthEventType.ACCOUNT_LOCKED,
			null,
			email,
			ipAddress,
			userAgent,
			{ tenantId, unlockAt: lockout.unlockAt }
		);

		return {
			success: false,
			error: `Account locked due to too many failed attempts. Try again after ${lockout.unlockAt?.toLocaleTimeString()}`,
			lockoutInfo: lockout
		};
	}

	// Get user from database
	const user = await queryOne<{
		id: number;
		email: string;
		username: string;
		password: string;
		role: string;
		tenant_id: string;
		is_active: boolean;
	}>('SELECT * FROM users WHERE email = $1 AND tenant_id = $2', [email, tenantId]);

	if (!user) {
		// Record failed attempt
		await recordFailedLogin(email);
		await logAuthEvent(AuthEventType.LOGIN_FAILURE, null, email, ipAddress, userAgent, {
			tenantId,
			reason: 'user_not_found'
		});

		return {
			success: false,
			error: 'Invalid email or password'
		};
	}

	// Check if user is active
	if (!user.is_active) {
		await logAuthEvent(AuthEventType.LOGIN_FAILURE, user.id, email, ipAddress, userAgent, {
			tenantId,
			reason: 'account_inactive'
		});

		return {
			success: false,
			error: 'Account is inactive'
		};
	}

	// Verify password
	const passwordValid = await verifyPassword(password, user.password);

	if (!passwordValid) {
		// Record failed attempt
		const lockoutInfo = await recordFailedLogin(email);
		await logAuthEvent(AuthEventType.LOGIN_FAILURE, user.id, email, ipAddress, userAgent, {
			tenantId,
			reason: 'invalid_password',
			attempts: lockoutInfo.attempts
		});

		return {
			success: false,
			error: 'Invalid email or password',
			lockoutInfo
		};
	}

	// Reset failed attempts on successful login
	await resetFailedLogins(email);

	// Create session
	const sessionToken = await createSession(user.id, user.email, user.tenant_id);

	// Log successful login
	await logAuthEvent(AuthEventType.LOGIN_SUCCESS, user.id, email, ipAddress, userAgent, {
		tenantId
	});

	return {
		success: true,
		sessionToken,
		user: {
			id: user.id,
			email: user.email,
			username: user.username,
			role: user.role,
			tenantId: user.tenant_id
		}
	};
}

/**
 * Logout user and destroy session
 * 
 * @param sessionId - Session token
 * @param ipAddress - Client IP address
 * @param userAgent - Client user agent
 */
export async function logout(
	sessionId: string,
	ipAddress: string,
	userAgent: string
): Promise<void> {
	// Get session data before destroying
	const session = await validateSession(sessionId);

	if (session) {
		await logAuthEvent(
			AuthEventType.LOGOUT,
			session.userId,
			session.email,
			ipAddress,
			userAgent,
			{ tenantId: session.tenantId }
		);
	}

	await destroySession(sessionId);
}

/**
 * Change user password
 * Invalidates all existing sessions (Requirement 2.7)
 * 
 * @param userId - User ID
 * @param currentPassword - Current password
 * @param newPassword - New password
 * @param ipAddress - Client IP address
 * @param userAgent - Client user agent
 * @returns Success status and error message if failed
 */
export async function changePassword(
	userId: number,
	currentPassword: string,
	newPassword: string,
	ipAddress: string,
	userAgent: string
): Promise<{ success: boolean; error?: string }> {
	// Get user
	const user = await queryOne<{
		id: number;
		email: string;
		password: string;
		tenant_id: string;
	}>('SELECT id, email, password, tenant_id FROM users WHERE id = $1', [userId]);

	if (!user) {
		return { success: false, error: 'User not found' };
	}

	// Verify current password
	const passwordValid = await verifyPassword(currentPassword, user.password);
	if (!passwordValid) {
		return { success: false, error: 'Current password is incorrect' };
	}

	// Validate new password strength
	const validation = validatePasswordStrength(newPassword);
	if (!validation.valid) {
		return { success: false, error: validation.errors.join(', ') };
	}

	// Hash new password
	const hashedPassword = await hashPassword(newPassword);

	// Update password
	await query('UPDATE users SET password = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2', [
		hashedPassword,
		userId
	]);

	// Invalidate all sessions (Requirement 2.7)
	await invalidateAllUserSessions(userId);

	// Log password change
	await logAuthEvent(
		AuthEventType.PASSWORD_CHANGE,
		userId,
		user.email,
		ipAddress,
		userAgent,
		{ tenantId: user.tenant_id }
	);

	return { success: true };
}
