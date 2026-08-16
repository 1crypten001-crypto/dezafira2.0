/**
 * Security Headers Middleware
 * 
 * Sets HTTP security headers to protect against common web vulnerabilities.
 * Implements defense-in-depth security strategy.
 * 
 * Requirements: 2.10
 */

import type { RequestEvent } from '@sveltejs/kit';

/**
 * Security headers configuration interface
 */
export interface SecurityHeadersConfig {
	/** Enable Content Security Policy */
	enableCSP?: boolean;
	/** Custom CSP directives */
	cspDirectives?: Record<string, string[]>;
	/** Enable HSTS (only for HTTPS) */
	enableHSTS?: boolean;
	/** HSTS max age in seconds */
	hstsMaxAge?: number;
	/** Include subdomains in HSTS */
	hstsIncludeSubDomains?: boolean;
	/** Enable HSTS preload */
	hstsPreload?: boolean;
	/** Custom additional headers */
	additionalHeaders?: Record<string, string>;
}

/**
 * Default Content Security Policy directives
 * Strict policy that can be relaxed based on application needs
 */
const DEFAULT_CSP_DIRECTIVES: Record<string, string[]> = {
	'default-src': ["'self'"],
	'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"], // TODO: Remove unsafe-* in production
	'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
	'img-src': ["'self'", 'data:', 'https:', 'blob:'],
	'font-src': ["'self'", 'data:', 'https://fonts.gstatic.com'],
	'connect-src': ["'self'"],
	'media-src': ["'self'"],
	'object-src': ["'none'"],
	'frame-src': ["'none'"],
	'frame-ancestors': ["'none'"],
	'base-uri': ["'self'"],
	'form-action': ["'self'"],
	'upgrade-insecure-requests': []
};

/**
 * Build Content Security Policy header value from directives
 * 
 * @param directives - CSP directives object
 * @returns CSP header value string
 */
function buildCSP(directives: Record<string, string[]>): string {
	return Object.entries(directives)
		.map(([directive, values]) => {
			if (values.length === 0) {
				return directive;
			}
			return `${directive} ${values.join(' ')}`;
		})
		.join('; ');
}

/**
 * Set security headers on the response
 * 
 * @param event - SvelteKit request event
 * @param config - Optional security headers configuration
 */
export function setSecurityHeaders(
	event: RequestEvent,
	config: SecurityHeadersConfig = {}
): void {
	const {
		enableCSP = true,
		cspDirectives = DEFAULT_CSP_DIRECTIVES,
		enableHSTS = true,
		hstsMaxAge = 31536000, // 1 year
		hstsIncludeSubDomains = true,
		hstsPreload = true,
		additionalHeaders = {}
	} = config;

	const headers: Record<string, string> = {};

	// Content Security Policy
	if (enableCSP) {
		headers['Content-Security-Policy'] = buildCSP(cspDirectives);
	}

	// Prevent clickjacking attacks
	headers['X-Frame-Options'] = 'DENY';

	// Prevent MIME type sniffing
	headers['X-Content-Type-Options'] = 'nosniff';

	// Enable browser XSS protection (legacy, but still useful)
	headers['X-XSS-Protection'] = '1; mode=block';

	// HTTP Strict Transport Security (only for HTTPS)
	if (enableHSTS && event.url.protocol === 'https:') {
		let hstsValue = `max-age=${hstsMaxAge}`;
		if (hstsIncludeSubDomains) {
			hstsValue += '; includeSubDomains';
		}
		if (hstsPreload) {
			hstsValue += '; preload';
		}
		headers['Strict-Transport-Security'] = hstsValue;
	}

	// Referrer Policy - balance privacy and functionality
	headers['Referrer-Policy'] = 'strict-origin-when-cross-origin';

	// Permissions Policy (formerly Feature Policy)
	// Disable potentially dangerous features
	headers['Permissions-Policy'] = [
		'geolocation=()',
		'microphone=()',
		'camera=()',
		'payment=()',
		'usb=()',
		'magnetometer=()',
		'gyroscope=()',
		'accelerometer=()'
	].join(', ');

	// Cross-Origin policies
	headers['Cross-Origin-Embedder-Policy'] = 'require-corp';
	headers['Cross-Origin-Opener-Policy'] = 'same-origin';
	headers['Cross-Origin-Resource-Policy'] = 'same-origin';

	// Merge with additional custom headers
	Object.assign(headers, additionalHeaders);

	// Set all headers
	event.setHeaders(headers);
}

/**
 * Relaxed CSP for development environment
 * Allows inline scripts and styles for hot module replacement
 */
export const DEV_CSP_DIRECTIVES: Record<string, string[]> = {
	'default-src': ["'self'"],
	'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
	'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
	'img-src': ["'self'", 'data:', 'https:', 'blob:'],
	'font-src': ["'self'", 'data:', 'https://fonts.gstatic.com'],
	'connect-src': ["'self'", 'ws:', 'wss:'], // WebSocket for HMR
	'frame-ancestors': ["'none'"],
	'base-uri': ["'self'"],
	'form-action': ["'self'"]
};

/**
 * Strict CSP for production environment
 * Removes unsafe-inline and unsafe-eval
 */
export const PROD_CSP_DIRECTIVES: Record<string, string[]> = {
	'default-src': ["'self'"],
	'script-src': ["'self'"],
	'style-src': ["'self'", 'https://fonts.googleapis.com'],
	'img-src': ["'self'", 'data:', 'https:'],
	'font-src': ["'self'", 'data:', 'https://fonts.gstatic.com'],
	'connect-src': ["'self'"],
	'media-src': ["'self'"],
	'object-src': ["'none'"],
	'frame-src': ["'none'"],
	'frame-ancestors': ["'none'"],
	'base-uri': ["'self'"],
	'form-action': ["'self'"],
	'upgrade-insecure-requests': []
};

/**
 * Get environment-appropriate CSP directives
 * 
 * @param isDevelopment - Whether running in development mode
 * @returns CSP directives for the environment
 */
export function getCSPDirectives(isDevelopment: boolean): Record<string, string[]> {
	return isDevelopment ? DEV_CSP_DIRECTIVES : PROD_CSP_DIRECTIVES;
}

/**
 * Security headers middleware factory
 * Creates a middleware function with specific configuration
 * 
 * @param config - Security headers configuration
 * @returns Middleware function
 */
export function createSecurityHeadersMiddleware(config: SecurityHeadersConfig = {}) {
	return (event: RequestEvent) => {
		setSecurityHeaders(event, config);
	};
}

/**
 * Set CORS headers for API endpoints
 * 
 * @param event - SvelteKit request event
 * @param options - CORS options
 */
export function setCORSHeaders(
	event: RequestEvent,
	options: {
		origin?: string | string[];
		methods?: string[];
		allowedHeaders?: string[];
		exposedHeaders?: string[];
		credentials?: boolean;
		maxAge?: number;
	} = {}
): void {
	const {
		origin = '*',
		methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
		allowedHeaders = ['Content-Type', 'Authorization', 'X-CSRF-Token'],
		exposedHeaders = ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset'],
		credentials = false,
		maxAge = 86400 // 24 hours
	} = options;

	const headers: Record<string, string> = {};

	// Handle origin
	if (Array.isArray(origin)) {
		const requestOrigin = event.request.headers.get('origin');
		if (requestOrigin && origin.includes(requestOrigin)) {
			headers['Access-Control-Allow-Origin'] = requestOrigin;
		}
	} else {
		headers['Access-Control-Allow-Origin'] = origin;
	}

	// Other CORS headers
	headers['Access-Control-Allow-Methods'] = methods.join(', ');
	headers['Access-Control-Allow-Headers'] = allowedHeaders.join(', ');
	headers['Access-Control-Expose-Headers'] = exposedHeaders.join(', ');
	headers['Access-Control-Max-Age'] = maxAge.toString();

	if (credentials) {
		headers['Access-Control-Allow-Credentials'] = 'true';
	}

	event.setHeaders(headers);
}

/**
 * Set cache control headers
 * 
 * @param event - SvelteKit request event
 * @param options - Cache control options
 */
export function setCacheHeaders(
	event: RequestEvent,
	options: {
		maxAge?: number;
		sMaxAge?: number;
		public?: boolean;
		private?: boolean;
		noCache?: boolean;
		noStore?: boolean;
		mustRevalidate?: boolean;
		immutable?: boolean;
	} = {}
): void {
	const directives: string[] = [];

	if (options.public) directives.push('public');
	if (options.private) directives.push('private');
	if (options.noCache) directives.push('no-cache');
	if (options.noStore) directives.push('no-store');
	if (options.mustRevalidate) directives.push('must-revalidate');
	if (options.immutable) directives.push('immutable');

	if (options.maxAge !== undefined) {
		directives.push(`max-age=${options.maxAge}`);
	}

	if (options.sMaxAge !== undefined) {
		directives.push(`s-maxage=${options.sMaxAge}`);
	}

	if (directives.length > 0) {
		event.setHeaders({
			'Cache-Control': directives.join(', ')
		});
	}
}

/**
 * Preset cache headers for common scenarios
 */
export const CACHE_PRESETS = {
	/** No caching - always fetch fresh */
	noCache: {
		noCache: true,
		noStore: true,
		mustRevalidate: true
	},

	/** Cache for 5 minutes */
	short: {
		public: true,
		maxAge: 300, // 5 minutes
		sMaxAge: 300
	},

	/** Cache for 1 hour */
	medium: {
		public: true,
		maxAge: 3600, // 1 hour
		sMaxAge: 3600
	},

	/** Cache for 1 day */
	long: {
		public: true,
		maxAge: 86400, // 1 day
		sMaxAge: 86400
	},

	/** Cache for 1 year (immutable assets) */
	immutable: {
		public: true,
		maxAge: 31536000, // 1 year
		immutable: true
	}
};
