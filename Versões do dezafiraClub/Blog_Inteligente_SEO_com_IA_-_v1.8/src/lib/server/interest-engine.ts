import {
	getPostById,
	incrementUserInterest,
	getCategoriesByPostId,
	incrementCollaborativeRelation,
	getPublishedFeedCandidates,
	getAllPosts,
	upsertUserSeenPost,
	getUserSeenPosts
} from './database';
import type { Post } from './database';

export type UserInterests = {
	categories?: Record<string, number>;
	tags?: Record<string, number>;
};

export type FeedBucket = 'fresh' | 'relevant' | 'discover';

export type FeedPost = Post & {
	feedBucket?: FeedBucket;
	isCollaborative?: boolean;
	recentlySeen?: boolean;
};

/** How long a viewed post stays out of the primary home mix (then it can return). */
export const SEEN_COOLDOWN_MS = 48 * 60 * 60 * 1000; // 48 hours
const SEEN_COOKIE = 'recently_seen_posts';
const SEEN_COOKIE_MAX_ENTRIES = 80;
const SEEN_COOKIE_MAX_AGE = 60 * 60 * 24 * 14; // 14 days cookie life

// ─── Recently-seen (cookie + DB) ────────────────────────────────────────────

/** Compact cookie: "id:unixSec,id:unixSec" */
export function parseSeenCookie(raw: string | undefined): Map<number, number> {
	const map = new Map<number, number>();
	if (!raw) return map;
	for (const part of raw.split(',')) {
		const [idStr, tsStr] = part.split(':');
		const id = Number(idStr);
		const sec = Number(tsStr);
		if (!id || !sec) continue;
		map.set(id, sec * 1000);
	}
	return map;
}

export function serializeSeenCookie(map: Map<number, number>): string {
	const now = Date.now();
	// Drop expired beyond 2× cooldown; keep freshest N
	const alive = Array.from(map.entries())
		.filter(([, ts]) => now - ts < SEEN_COOLDOWN_MS * 2)
		.sort((a, b) => b[1] - a[1])
		.slice(0, SEEN_COOKIE_MAX_ENTRIES);

	return alive.map(([id, ts]) => `${id}:${Math.floor(ts / 1000)}`).join(',');
}

export async function recordPostSeen(
	postId: number,
	locals: any,
	cookies: any,
	url: URL
): Promise<void> {
	if (!postId) return;
	const now = Date.now();

	if (locals?.user?.id) {
		await upsertUserSeenPost(locals.user.id, postId, now);
		return;
	}

	// Anonymous: cookie history
	const map = parseSeenCookie(cookies.get(SEEN_COOKIE));
	map.set(postId, now);
	const value = serializeSeenCookie(map);
	if (!value) return;

	cookies.set(SEEN_COOKIE, value, {
		path: '/',
		httpOnly: true,
		sameSite: 'strict',
		maxAge: SEEN_COOKIE_MAX_AGE,
		secure: url.protocol === 'https:'
	});
}

export async function loadRecentlySeen(
	locals: any,
	cookies: any,
	cooldownMs: number = SEEN_COOLDOWN_MS
): Promise<Map<number, number>> {
	if (locals?.user?.id) {
		return getUserSeenPosts(locals.user.id, cooldownMs);
	}
	const map = parseSeenCookie(cookies.get(SEEN_COOKIE));
	const now = Date.now();
	// Only active cooldown entries for ranking
	const active = new Map<number, number>();
	for (const [id, ts] of map) {
		if (now - ts < cooldownMs) active.set(id, ts);
	}
	return active;
}

/** Points awarded per engagement signal */
export async function trackRecommendationEvent(
	event: string,
	postId: number,
	locals: any,
	cookies: any,
	url: URL
): Promise<void> {
	let points = 0;
	if (event === 'view') points = 1;
	else if (event === 'scroll_50') points = 3;
	else if (event === 'scroll_100') points = 5;
	else if (event === 'time_3m') points = 3;
	else if (event === 'share') points = 10;

	if (points === 0) return;

	const post = await getPostById(postId);
	if (!post) return;

	const postCategories = await getCategoriesByPostId(postId);
	const categories = postCategories.map((c) => c.name);
	const tags = post.tags ? post.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : [];

	// Collaborative session transitions + recently-seen history
	if (event === 'view') {
		const lastViewedId = cookies.get('last_viewed_post_id');
		if (lastViewedId) {
			const fromId = Number(lastViewedId);
			if (!isNaN(fromId) && fromId !== postId) {
				await incrementCollaborativeRelation(fromId, postId);
			}
		}
		cookies.set('last_viewed_post_id', String(postId), {
			path: '/',
			httpOnly: true,
			sameSite: 'strict',
			maxAge: 30 * 60,
			secure: url.protocol === 'https:'
		});

		// Temporary feed suppression (returns after SEEN_COOLDOWN_MS)
		await recordPostSeen(postId, locals, cookies, url);
	}

	if (locals?.user) {
		const userId = locals.user.id;
		for (const cat of categories) {
			await incrementUserInterest(userId, 'category', cat, points);
		}
		for (const tag of tags) {
			await incrementUserInterest(userId, 'tag', tag, points);
		}
	} else {
		let interests: UserInterests = { categories: {}, tags: {} };
		const cookieVal = cookies.get('user_interests');
		if (cookieVal) {
			try {
				interests = JSON.parse(cookieVal);
			} catch {
				// ignore malformed cookie
			}
		}

		if (!interests.categories) interests.categories = {};
		if (!interests.tags) interests.tags = {};

		for (const cat of categories) {
			interests.categories[cat] = (interests.categories[cat] || 0) + points;
		}
		for (const tag of tags) {
			interests.tags[tag] = (interests.tags[tag] || 0) + points;
		}

		cookies.set('user_interests', JSON.stringify(interests), {
			path: '/',
			httpOnly: true,
			sameSite: 'strict',
			maxAge: 60 * 60 * 24 * 30,
			secure: url.protocol === 'https:'
		});
	}
}

// ─── Feed ranking helpers ───────────────────────────────────────────────────

function hashSeed(str: string): number {
	let h = 2166136261;
	for (let i = 0; i < str.length; i++) {
		h ^= str.charCodeAt(i);
		h = Math.imul(h, 16777619);
	}
	return h >>> 0;
}

/** Deterministic shuffle — same seed ⇒ same order (stable pagination, no duplicates). */
function seededShuffle<T>(items: T[], seed: number): T[] {
	const arr = items.slice();
	let s = seed || 1;
	for (let i = arr.length - 1; i > 0; i--) {
		s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
		const j = s % (i + 1);
		const tmp = arr[i];
		arr[i] = arr[j];
		arr[j] = tmp;
	}
	return arr;
}

function daysSince(dateStr: string | null | undefined): number {
	if (!dateStr) return 999;
	const t = new Date(dateStr).getTime();
	if (Number.isNaN(t)) return 999;
	return Math.max(0, (Date.now() - t) / (1000 * 60 * 60 * 24));
}

function parseList(value: string | null | undefined): string[] {
	if (!value) return [];
	return value
		.split(',')
		.map((s) => s.trim())
		.filter(Boolean);
}

/** Log-scale interest so long-term affinity cannot bury everything new. */
function cappedInterest(raw: number): number {
	if (raw <= 0) return 0;
	return Math.min(12, Math.log2(1 + raw));
}

function interestMatchScore(post: Post, interests?: UserInterests): number {
	if (!interests) return 0;
	const cats = interests.categories || {};
	const tags = interests.tags || {};
	let score = 0;

	for (const cat of parseList(post.categories)) {
		score += cappedInterest(cats[cat] || 0) * 2;
	}
	for (const tag of parseList(post.tags)) {
		score += cappedInterest(tags[tag] || 0) * 1.5;
	}
	return score;
}

function freshnessScore(post: Post): number {
	const d = daysSince(post.created_at);
	if (d <= 1) return 20;
	if (d <= 3) return 14;
	if (d <= 7) return 9;
	if (d <= 14) return 5;
	if (d <= 30) return 2;
	return 0;
}

function topInterestNames(map: Record<string, number> | undefined, limit = 3): string[] {
	if (!map) return [];
	return Object.entries(map)
		.filter(([, s]) => s > 0)
		.sort((a, b) => b[1] - a[1])
		.slice(0, limit)
		.map(([name]) => name);
}

function primaryCategory(post: Post): string {
	return parseList(post.categories)[0] || `__none_${post.id}`;
}

/**
 * Push recently-viewed posts out of the primary mix for the cooldown window.
 * They sit at the end (oldest-seen first) so deep scroll can still fill the feed,
 * and after SEEN_COOLDOWN_MS they rejoin the ranked mix normally.
 */
export function applySeenCooldown(
	mixed: FeedPost[],
	recentlySeen: Map<number, number> | undefined,
	cooldownMs: number = SEEN_COOLDOWN_MS
): FeedPost[] {
	if (!recentlySeen?.size || !mixed.length) return mixed;

	const now = Date.now();
	const active: FeedPost[] = [];
	const suppressed: { post: FeedPost; seenAt: number }[] = [];

	for (const post of mixed) {
		const seenAt = recentlySeen.get(post.id);
		if (seenAt != null && now - seenAt < cooldownMs) {
			suppressed.push({ post: { ...post, recentlySeen: true }, seenAt });
		} else {
			active.push(post);
		}
	}

	// Oldest view first among suppressed → closer to “coming back”
	suppressed.sort((a, b) => a.seenAt - b.seenAt);

	// If user saw almost everything, still show something (suppressed tail only)
	if (active.length === 0) {
		return suppressed.map((s) => s.post);
	}

	return [...active, ...suppressed.map((s) => s.post)];
}

/**
 * YouTube-like mixed home feed:
 * - fresh / relevant / discover buckets
 * - stable day seed + hard dedupe + light category diversity
 */
export function buildMixedFeed(
	candidates: Post[],
	userInterests: UserInterests | undefined,
	seedKey: string
): FeedPost[] {
	if (!candidates.length) return [];

	const seed = hashSeed(seedKey);
	const hasInterests =
		!!userInterests &&
		(Object.keys(userInterests.categories || {}).length > 0 ||
			Object.keys(userInterests.tags || {}).length > 0);

	if (!hasInterests) {
		const sorted = candidates.slice().sort((a, b) => {
			const ta = new Date(a.created_at).getTime();
			const tb = new Date(b.created_at).getTime();
			return tb - ta;
		});
		const head = sorted.slice(0, Math.min(12, sorted.length));
		const tail = seededShuffle(sorted.slice(head.length), seed);
		return [...head, ...tail].map((p) => ({
			...p,
			feedBucket: (daysSince(p.created_at) <= 7 ? 'fresh' : 'discover') as FeedBucket
		}));
	}

	const topCats = new Set(topInterestNames(userInterests!.categories, 3));
	const topTags = new Set(topInterestNames(userInterests!.tags, 5));

	const scored = candidates.map((post) => {
		const relevance = interestMatchScore(post, userInterests);
		const fresh = freshnessScore(post);
		const postCats = parseList(post.categories);
		const postTags = parseList(post.tags);
		const inBubble =
			postCats.some((c) => topCats.has(c)) || postTags.some((t) => topTags.has(t));

		return { post, relevance, fresh, inBubble };
	});

	const freshPool = scored
		.slice()
		.sort((a, b) => {
			if (b.fresh !== a.fresh) return b.fresh - a.fresh;
			return (
				new Date(b.post.created_at).getTime() - new Date(a.post.created_at).getTime()
			);
		})
		.map((s) => s.post);

	const relevantPool = scored
		.filter((s) => s.relevance > 0)
		.sort((a, b) => {
			const sa = a.relevance * 3 + a.fresh;
			const sb = b.relevance * 3 + b.fresh;
			if (sb !== sa) return sb - sa;
			return (
				new Date(b.post.created_at).getTime() - new Date(a.post.created_at).getTime()
			);
		})
		.map((s) => s.post);

	const discoverPool = seededShuffle(
		scored
			.filter((s) => !s.inBubble || s.relevance < 2)
			.sort(
				(a, b) =>
					new Date(b.post.created_at).getTime() - new Date(a.post.created_at).getTime()
			)
			.map((s) => s.post),
		seed ^ 0x9e3779b9
	);

	const allChrono = scored
		.slice()
		.sort(
			(a, b) =>
				new Date(b.post.created_at).getTime() - new Date(a.post.created_at).getTime()
		)
		.map((s) => s.post);

	const pattern: FeedBucket[] = [
		'fresh',
		'relevant',
		'fresh',
		'discover',
		'relevant',
		'fresh',
		'relevant',
		'discover',
		'fresh',
		'relevant'
	];

	const pointers: Record<FeedBucket, number> = {
		fresh: 0,
		relevant: 0,
		discover: 0
	};
	const pools: Record<FeedBucket, Post[]> = {
		fresh: freshPool,
		relevant: relevantPool.length ? relevantPool : allChrono,
		discover: discoverPool.length ? discoverPool : allChrono
	};

	const used = new Set<number>();
	const result: FeedPost[] = [];
	let lastCategory: string | null = null;
	let patternIdx = 0;
	let safety = 0;
	const maxSafety = candidates.length * 4;

	const takeNext = (bucket: FeedBucket, respectDiversity: boolean): FeedPost | null => {
		const pool = pools[bucket];
		while (pointers[bucket] < pool.length) {
			const post = pool[pointers[bucket]++];
			if (used.has(post.id)) continue;
			const cat = primaryCategory(post);
			if (respectDiversity && lastCategory && cat === lastCategory) {
				for (let k = pointers[bucket]; k < Math.min(pool.length, pointers[bucket] + 6); k++) {
					const alt = pool[k];
					if (!used.has(alt.id) && primaryCategory(alt) !== lastCategory) {
						pool[k] = post;
						pool[pointers[bucket] - 1] = alt;
						used.add(alt.id);
						return { ...alt, feedBucket: bucket };
					}
				}
			}
			used.add(post.id);
			return { ...post, feedBucket: bucket };
		}
		return null;
	};

	while (result.length < candidates.length && safety < maxSafety) {
		safety++;
		const preferred = pattern[patternIdx % pattern.length];
		patternIdx++;

		let picked =
			takeNext(preferred, true) ||
			takeNext('fresh', true) ||
			takeNext('relevant', true) ||
			takeNext('discover', false);

		if (!picked) {
			for (const p of allChrono) {
				if (!used.has(p.id)) {
					picked = { ...p, feedBucket: 'fresh' };
					used.add(p.id);
					break;
				}
			}
		}

		if (!picked) break;
		lastCategory = primaryCategory(picked);
		result.push(picked);
	}

	return result;
}

/**
 * Home / API feed entry point.
 * Search & category keep pure chronological order.
 * Personalized mix only when recommendations are on and no search filter.
 */
export async function getHomeFeed(options: {
	page?: number;
	limit?: number;
	search?: string;
	categorySlug?: string;
	userInterests?: UserInterests;
	recommendationsEnabled?: boolean;
	/** postId → seenAt(ms); posts viewed within cooldown are demoted */
	recentlySeen?: Map<number, number>;
}): Promise<FeedPost[]> {
	const page = options.page || 1;
	const limit = options.limit || 7;
	const search = options.search?.trim() || '';
	const categorySlug = options.categorySlug;

	if (search || categorySlug) {
		const posts = await getAllPosts({
			page,
			limit,
			search: search || undefined,
			categorySlug
		});
		return posts as FeedPost[];
	}

	if (!options.recommendationsEnabled) {
		const posts = await getAllPosts({ page, limit });
		return posts as FeedPost[];
	}

	const candidates = await getPublishedFeedCandidates(2000);
	const dayKey = new Date().toISOString().slice(0, 10);
	const interestKey = options.userInterests
		? Object.entries({
				...(options.userInterests.categories || {}),
				...(options.userInterests.tags || {})
			})
				.sort(([a], [b]) => a.localeCompare(b))
				.map(([k, v]) => `${k}:${Math.floor(Number(v))}`)
				.join('|')
		: 'anon';

	let mixed = buildMixedFeed(candidates, options.userInterests, `${dayKey}|${interestKey}`);
	mixed = applySeenCooldown(mixed, options.recentlySeen, SEEN_COOLDOWN_MS);

	const offset = (page - 1) * limit;
	return mixed.slice(offset, offset + limit);
}

export function getRecommendationReason(
	post: any,
	userInterests: UserInterests | undefined
): string | null {
	if (post.isCollaborative) {
		return '👥 Outros leitores também leram';
	}

	// Don't badge "already seen" items that only appear deep in the tail
	if (post.recentlySeen) {
		return null;
	}

	if (post.feedBucket === 'discover') {
		return '✨ Descoberta para você';
	}
	if (post.feedBucket === 'fresh') {
		const d = daysSince(post.created_at);
		if (d <= 3) return '🔥 Novidade';
		if (d <= 14) return '🆕 Recente';
	}

	if (!userInterests) {
		if (post.created_at && daysSince(post.created_at) <= 3) {
			return '🔥 Novidade';
		}
		return null;
	}

	const categories = userInterests.categories || {};
	const tags = userInterests.tags || {};

	if (post.feedBucket === 'relevant' || !post.feedBucket) {
		if (post.tags) {
			const postTags = parseList(post.tags);
			let maxTag = '';
			let maxScore = 0;
			for (const tag of postTags) {
				const score = tags[tag] || 0;
				if (score > maxScore) {
					maxScore = score;
					maxTag = tag;
				}
			}
			if (maxScore >= 5) {
				return `🏷️ Tema que você acompanha: ${maxTag}`;
			}
		}

		if (post.categories) {
			const postCats = parseList(post.categories);
			let maxCat = '';
			let maxScore = 0;
			for (const cat of postCats) {
				const score = categories[cat] || 0;
				if (score > maxScore) {
					maxScore = score;
					maxCat = cat;
				}
			}
			if (maxScore >= 5) {
				return `💡 Relevante em ${maxCat}`;
			}
		}
	}

	if (post.created_at && daysSince(post.created_at) <= 3) {
		return '🔥 Novidade';
	}

	if (post.feedBucket === 'relevant') {
		return '💡 Recomendado para você';
	}

	return null;
}
