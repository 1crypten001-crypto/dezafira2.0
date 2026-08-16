import { error } from '@sveltejs/kit';
import type { RequestEvent } from '@sveltejs/kit';

export interface RateLimitConfig {
	windowMs: number;
	maxRequests: number;
	keyPrefix: string;
	message?: string;
}

export interface RateLimitResult {
	allowed: boolean;
	remaining: number;
	resetAt: number;
	limit: number;
}

type Bucket = { timestamps: number[] };

const buckets = new Map<string, Bucket>();

function getBucket(key: string): Bucket {
	let bucket = buckets.get(key);
	if (!bucket) {
		bucket = { timestamps: [] };
		buckets.set(key, bucket);
	}
	return bucket;
}

export async function checkRateLimit(identifier: string, config: RateLimitConfig): Promise<RateLimitResult> {
	const key = `${config.keyPrefix}:${identifier}`;
	const now = Date.now();
	const windowStart = now - config.windowMs;
	const bucket = getBucket(key);

	bucket.timestamps = bucket.timestamps.filter((t) => t > windowStart);
	const count = bucket.timestamps.length;

	if (count >= config.maxRequests) {
		const oldest = bucket.timestamps[0];
		const resetAt = oldest ? oldest + config.windowMs : now + config.windowMs;
		return { allowed: false, remaining: 0, resetAt, limit: config.maxRequests };
	}

	bucket.timestamps.push(now);
	const remaining = config.maxRequests - bucket.timestamps.length;
	const oldest = bucket.timestamps[0];
	const resetAt = oldest ? oldest + config.windowMs : now + config.windowMs;

	return { allowed: true, remaining, resetAt, limit: config.maxRequests };
}

export const RATE_LIMITS = {
	api: {
		windowMs: 60 * 60 * 1000,
		maxRequests: 1000,
		keyPrefix: 'rl:api',
		message: 'API rate limit exceeded. Please try again later.'
	},
	login: {
		windowMs: 15 * 60 * 1000,
		maxRequests: 5,
		keyPrefix: 'rl:login',
		message: 'Too many login attempts. Please try again in 15 minutes.'
	},
	general: {
		windowMs: 60 * 1000,
		maxRequests: 100,
		keyPrefix: 'rl:general',
		message: 'Too many requests. Please slow down.'
	},
	passwordReset: {
		windowMs: 60 * 60 * 1000,
		maxRequests: 3,
		keyPrefix: 'rl:password-reset',
		message: 'Too many password reset attempts. Please try again later.'
	},
	registration: {
		windowMs: 60 * 60 * 1000,
		maxRequests: 5,
		keyPrefix: 'rl:registration',
		message: 'Too many registration attempts. Please try again later.'
	}
} as const;

export async function rateLimitMiddleware(event: RequestEvent, config: RateLimitConfig): Promise<void> {
	const identifier = event.getClientAddress();
	const result = await checkRateLimit(identifier, config);

	event.setHeaders({
		'X-RateLimit-Limit': result.limit.toString(),
		'X-RateLimit-Remaining': result.remaining.toString(),
		'X-RateLimit-Reset': new Date(result.resetAt).toISOString(),
		'X-RateLimit-Policy': `${config.maxRequests};w=${config.windowMs / 1000}`
	});

	if (!result.allowed) {
		throw error(429, config.message || 'Too many requests');
	}
}

export function createRateLimiter(config: RateLimitConfig) {
	return async (event: RequestEvent) => {
		await rateLimitMiddleware(event, config);
	};
}

export async function rateLimitByUser(
	event: RequestEvent,
	config: RateLimitConfig,
	userId: number
): Promise<void> {
	const identifier = `user:${userId}`;
	const result = await checkRateLimit(identifier, config);

	event.setHeaders({
		'X-RateLimit-Limit': result.limit.toString(),
		'X-RateLimit-Remaining': result.remaining.toString(),
		'X-RateLimit-Reset': new Date(result.resetAt).toISOString()
	});

	if (!result.allowed) {
		throw error(429, config.message || 'Too many requests');
	}
}

export async function resetRateLimit(identifier: string, keyPrefix: string): Promise<void> {
	buckets.delete(`${keyPrefix}:${identifier}`);
}

export async function getRateLimitStatus(identifier: string, config: RateLimitConfig): Promise<RateLimitResult> {
	const key = `${config.keyPrefix}:${identifier}`;
	const now = Date.now();
	const windowStart = now - config.windowMs;
	const bucket = getBucket(key);

	bucket.timestamps = bucket.timestamps.filter((t) => t > windowStart);
	const count = bucket.timestamps.length;

	if (count >= config.maxRequests) {
		const oldest = bucket.timestamps[0];
		const resetAt = oldest ? oldest + config.windowMs : now + config.windowMs;
		return { allowed: false, remaining: 0, resetAt, limit: config.maxRequests };
	}

	const oldest = bucket.timestamps[0];
	const resetAt = oldest ? oldest + config.windowMs : now + config.windowMs;
	return { allowed: true, remaining: config.maxRequests - count, resetAt, limit: config.maxRequests };
}

export async function closeRedisConnection(): Promise<void> {
	return;
}

type RedisValue = { value: string; expiresAt?: number };

class MemoryRedis {
	private store = new Map<string, RedisValue>();

	private isExpired(entry?: RedisValue) {
		return !!entry?.expiresAt && Date.now() >= entry.expiresAt;
	}

	private getEntry(key: string): RedisValue | undefined {
		const entry = this.store.get(key);
		if (!entry) return undefined;
		if (this.isExpired(entry)) {
			this.store.delete(key);
			return undefined;
		}
		return entry;
	}

	async get(key: string): Promise<string | null> {
		return this.getEntry(key)?.value ?? null;
	}

	async setex(key: string, seconds: number, value: string): Promise<'OK'> {
		this.store.set(key, { value, expiresAt: Date.now() + seconds * 1000 });
		return 'OK';
	}

	async incr(key: string): Promise<number> {
		const current = parseInt(this.getEntry(key)?.value ?? '0');
		const next = current + 1;
		const expiresAt = this.getEntry(key)?.expiresAt;
		this.store.set(key, { value: String(next), expiresAt });
		return next;
	}

	async pexpire(key: string, ms: number): Promise<number> {
		const entry = this.getEntry(key);
		const value = entry?.value ?? '0';
		this.store.set(key, { value, expiresAt: Date.now() + ms });
		return 1;
	}

	async pttl(key: string): Promise<number> {
		const entry = this.getEntry(key);
		if (!entry?.expiresAt) return -1;
		return Math.max(0, entry.expiresAt - Date.now());
	}

	async del(...keys: string[]): Promise<number> {
		let deleted = 0;
		for (const key of keys) {
			if (this.store.delete(key)) deleted++;
		}
		return deleted;
	}

	async keys(pattern: string): Promise<string[]> {
		if (!pattern.includes('*')) {
			return this.store.has(pattern) ? [pattern] : [];
		}
		const prefix = pattern.split('*')[0];
		return Array.from(this.store.keys()).filter((k) => k.startsWith(prefix));
	}
}

export const redis = new MemoryRedis();
