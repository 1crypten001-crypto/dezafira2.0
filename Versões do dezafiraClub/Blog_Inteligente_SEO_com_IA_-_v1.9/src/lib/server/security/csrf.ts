/**
 * CSRF Protection Middleware
 * 
 * Implements Cross-Site Request Forgery protection using token-based validation.
 * Tokens are generated with 32 bytes of cryptographic entropy and validated using
 * timing-safe comparison to prevent timing attacks.
 * 
 * Requirements: 2.1, 2.5
 */

import crypto from 'crypto';
import { error } from '@sveltejs/kit';
import type { RequestEvent } from '@sveltejs/kit';

const CSRF_TOKEN_LENGTH = 32;
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_HEADER_NAME = 'x-csrf-token';

/**
 * Generate a cryptographically secure CSRF token
 * @returns Hex-encoded token string (64 characters)
 */
export function generateCSRFToken(): string {
	return crypto.randomBytes(CSRF_TOKEN_LENGTH).toString('hex');
}

/**
 * Validate CSRF token using timing-safe comparison
 * @param token - Token from request header or form
 * @param cookieToken - Token from cookie
 * @returns True if tokens match, false otherwise
 */
export function validateCSRFToken(
	token: string | null,
	cookieToken: string | null
): boolean {
	if (!token || !cookieToken) {
		return false;
	}

	// Ensure both tokens are the same length to prevent timing attacks
	if (token.length !== cookieToken.length) {
		return false;
	}

	try {
		return crypto.timingSafeEqual(
			Buffer.from(token, 'hex'),
			Buffer.from(cookieToken, 'hex')
		);
	} catch (error) {
		// timingSafeEqual throws if buffers have different lengths
		return false;
	}
}

/**
 * CSRF middleware for SvelteKit hooks
 * Validates CSRF tokens for state-changing requests (POST, PUT, PATCH, DELETE)
 * Generates new tokens for GET requests
 * 
 * @param event - SvelteKit request event
 * @throws 403 error if CSRF validation fails
 */
export function csrfMiddleware(event: RequestEvent): void {
	const method = event.request.method;
	const url = event.url as unknown as { pathname?: unknown; protocol?: unknown; searchParams?: unknown } | undefined;
	const path = typeof url?.pathname === 'string' ? url.pathname : '/';
	const protocol = typeof url?.protocol === 'string' ? url.protocol : 'http:';
	const searchParams = url?.searchParams instanceof URLSearchParams ? url.searchParams : new URLSearchParams();
	const eventOrigin =
		typeof (event.url as unknown as { origin?: unknown } | undefined)?.origin === 'string'
			? (event.url as unknown as { origin: string }).origin
			: null;

	if (path.startsWith('/api/webhook/')) {
		return;
	}

	// Only validate for state-changing methods
	if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
		// Get token from header or query parameter
		const token =
			event.request.headers.get(CSRF_HEADER_NAME) ||
			searchParams.get('csrf_token');

		const cookieToken = event.cookies.get(CSRF_COOKIE_NAME) ?? null;

		if (!token) {
			const secFetchSite = event.request.headers.get('sec-fetch-site');
			if (secFetchSite === 'same-origin' || secFetchSite === 'same-site') {
				return;
			}

			const origin = event.request.headers.get('origin');
			if (eventOrigin && origin === eventOrigin) {
				return;
			}

			const referer = event.request.headers.get('referer');
			if (eventOrigin && typeof referer === 'string' && referer.startsWith(`${eventOrigin}/`)) {
				return;
			}
		}

		if (!validateCSRFToken(token, cookieToken)) {
			throw error(403, {
				message: 'Invalid CSRF token',
				code: 'CSRF_VALIDATION_FAILED'
			});
		}
	}

	// Generate new token for GET requests
	if (method === 'GET') {
		const token = generateCSRFToken();

		// Set CSRF cookie with security flags
		event.cookies.set(CSRF_COOKIE_NAME, token, {
			httpOnly: true, // Prevent JavaScript access
			secure: protocol === 'https:', // Only send over HTTPS in production
			sameSite: 'strict', // Prevent CSRF attacks
			path: '/',
			maxAge: 60 * 60 * 24 // 24 hours
		});

		// Make token available to the application
		event.locals.csrfToken = token;
	}
}

/**
 * Get CSRF token from event locals
 * @param event - SvelteKit request event
 * @returns CSRF token string or undefined
 */
export function getCSRFToken(event: RequestEvent): string | undefined {
	return event.locals.csrfToken;
}

/**
 * Verify CSRF token from request
 * Utility function for manual CSRF validation in specific routes
 * 
 * @param event - SvelteKit request event
 * @returns True if token is valid
 */
export function verifyCSRFToken(event: RequestEvent): boolean {
	const token =
		event.request.headers.get(CSRF_HEADER_NAME) ||
		event.url.searchParams.get('csrf_token');

	const cookieToken = event.cookies.get(CSRF_COOKIE_NAME) ?? null;

	return validateCSRFToken(token, cookieToken);
}
