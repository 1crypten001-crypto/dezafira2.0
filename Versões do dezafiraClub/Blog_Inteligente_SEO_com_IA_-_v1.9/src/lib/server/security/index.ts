/**
 * Security Module Index
 * 
 * Central export point for all security components.
 * Provides a unified interface for security features.
 */

// CSRF Protection
export {
	generateCSRFToken,
	validateCSRFToken,
	csrfMiddleware,
	getCSRFToken,
	verifyCSRFToken
} from './csrf';

// Rate Limiting
export {
	checkRateLimit,
	rateLimitMiddleware,
	createRateLimiter,
	rateLimitByUser,
	resetRateLimit,
	getRateLimitStatus,
	closeRedisConnection,
	RATE_LIMITS,
	redis,
	type RateLimitConfig,
	type RateLimitResult
} from './rateLimit';

// Input Sanitization
export {
	sanitizeHTML,
	sanitizeText,
	validateInput,
	safeValidateInput,
	validateFileUpload,
	sanitizeFilename,
	generateSafeFilename,
	schemas,
	type FileValidationOptions,
	type FileValidationResult
} from './sanitize';

// Security Headers
export {
	setSecurityHeaders,
	createSecurityHeadersMiddleware,
	setCORSHeaders,
	setCacheHeaders,
	getCSPDirectives,
	DEV_CSP_DIRECTIVES,
	PROD_CSP_DIRECTIVES,
	CACHE_PRESETS,
	type SecurityHeadersConfig
} from './headers';

// Enhanced Authentication
export {
	validatePasswordStrength,
	hashPassword,
	verifyPassword,
	recordFailedLogin,
	checkAccountLockout,
	resetFailedLogins,
	logAuthEvent,
	generateSessionToken,
	createSession,
	validateSession,
	destroySession,
	invalidateAllUserSessions,
	cleanExpiredSessions,
	login,
	logout,
	changePassword,
	DEFAULT_PASSWORD_REQUIREMENTS,
	AuthEventType,
	type PasswordRequirements,
	type PasswordValidationResult,
	type LockoutInfo,
	type SessionData,
	type LoginResult
} from './auth-enhanced';
