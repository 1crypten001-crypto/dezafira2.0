/**
 * Input Sanitization Module
 * 
 * Provides HTML sanitization using DOMPurify and input validation using Zod schemas.
 * Protects against XSS attacks and ensures data integrity.
 * 
 * Requirements: 2.8, 2.9, 2.14
 */

import DOMPurify from 'isomorphic-dompurify';
import { z } from 'zod';

/**
 * Allowed HTML tags for rich text content
 * Carefully curated to prevent XSS while allowing formatting
 */
const ALLOWED_TAGS = [
	// Text formatting
	'p',
	'br',
	'strong',
	'em',
	'u',
	's',
	'mark',
	'small',
	'sub',
	'sup',

	// Links
	'a',

	// Lists
	'ul',
	'ol',
	'li',

	// Headings
	'h1',
	'h2',
	'h3',
	'h4',
	'h5',
	'h6',

	// Quotes and code
	'blockquote',
	'code',
	'pre',

	// Media
	'img',
	'figure',
	'figcaption',

	// Tables
	'table',
	'thead',
	'tbody',
	'tfoot',
	'tr',
	'th',
	'td',
	'caption',

	// Semantic
	'article',
	'section',
	'aside',
	'div',
	'span'
];

/**
 * Allowed HTML attributes
 * Restricted to prevent JavaScript execution
 */
const ALLOWED_ATTR = [
	'href',
	'src',
	'alt',
	'title',
	'class',
	'id',
	'target',
	'rel',
	'width',
	'height',
	'loading',
	'decoding',
	'style' // Limited to safe CSS properties
];

/**
 * Allowed URL protocols
 * Prevents javascript: and data: URLs
 */
const ALLOWED_URI_REGEXP = /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i;

/**
 * Sanitize HTML content to prevent XSS attacks
 * 
 * @param html - Raw HTML string
 * @param options - Optional sanitization options
 * @returns Sanitized HTML string
 */
export function sanitizeHTML(
	html: string,
	options: {
		allowedTags?: string[];
		allowedAttributes?: string[];
		allowDataAttributes?: boolean;
	} = {}
): string {
	const config = {
		ALLOWED_TAGS: options.allowedTags || ALLOWED_TAGS,
		ALLOWED_ATTR: options.allowedAttributes || ALLOWED_ATTR,
		ALLOW_DATA_ATTR: options.allowDataAttributes || false,
		ALLOW_UNKNOWN_PROTOCOLS: false,
		ALLOWED_URI_REGEXP,
		// Remove scripts and event handlers
		FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed'],
		FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
		// Keep safe HTML entities
		KEEP_CONTENT: true,
		// Return clean HTML
		RETURN_DOM: false,
		RETURN_DOM_FRAGMENT: false,
		RETURN_DOM_IMPORT: false
	};

	return DOMPurify.sanitize(html, config);
}

/**
 * Sanitize plain text by escaping HTML entities
 * 
 * @param text - Plain text string
 * @returns Escaped text safe for HTML display
 */
export function sanitizeText(text: string): string {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#x27;')
		.replace(/\//g, '&#x2F;');
}

/**
 * Validation schemas for different entity types
 */
export const schemas = {
	/**
	 * Post validation schema
	 */
	post: z.object({
		title: z.string().min(1, 'Title is required').max(500, 'Title too long'),
		slug: z
			.string()
			.min(1, 'Slug is required')
			.max(200, 'Slug too long')
			.regex(/^[a-z0-9-]+$/, 'Slug must contain only lowercase letters, numbers, and hyphens'),
		content: z.string().min(1, 'Content is required'),
		excerpt: z.string().max(500, 'Excerpt too long').optional(),
		cover_image: z.string().url('Invalid image URL').optional().or(z.literal('')),
		status: z.enum(['draft', 'pending', 'approved', 'published', 'archived']),
		is_premium: z.boolean().optional().default(false),
		pinterest_enabled: z.boolean().optional().default(false),
		pinterest_image: z.string().url('Invalid Pinterest image URL').optional().or(z.literal('')),
		seo_title: z.string().max(70, 'SEO title too long (max 70 characters)').optional(),
		seo_description: z
			.string()
			.max(160, 'SEO description too long (max 160 characters)')
			.optional(),
		seo_keywords: z.string().optional(),
		category_ids: z.array(z.number().int().positive()).optional(),
		scheduled_at: z.string().datetime().optional().or(z.literal(''))
	}),

	/**
	 * User validation schema
	 */
	user: z.object({
		username: z
			.string()
			.min(3, 'Username must be at least 3 characters')
			.max(100, 'Username too long')
			.regex(
				/^[a-zA-Z0-9_-]+$/,
				'Username must contain only letters, numbers, underscores, and hyphens'
			),
		email: z.string().email('Invalid email address').max(255, 'Email too long'),
		password: z
			.string()
			.min(12, 'Password must be at least 12 characters')
			.max(128, 'Password too long')
			.regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
			.regex(/[a-z]/, 'Password must contain at least one lowercase letter')
			.regex(/[0-9]/, 'Password must contain at least one number')
			.regex(
				/[^A-Za-z0-9]/,
				'Password must contain at least one special character'
			),
		role: z.enum(['super_admin', 'admin', 'editor', 'author']).optional()
	}),

	/**
	 * User update schema (password optional)
	 */
	userUpdate: z.object({
		username: z
			.string()
			.min(3, 'Username must be at least 3 characters')
			.max(100, 'Username too long')
			.regex(
				/^[a-zA-Z0-9_-]+$/,
				'Username must contain only letters, numbers, underscores, and hyphens'
			)
			.optional(),
		email: z.string().email('Invalid email address').max(255, 'Email too long').optional(),
		password: z
			.string()
			.min(12, 'Password must be at least 12 characters')
			.max(128, 'Password too long')
			.regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
			.regex(/[a-z]/, 'Password must contain at least one lowercase letter')
			.regex(/[0-9]/, 'Password must contain at least one number')
			.regex(
				/[^A-Za-z0-9]/,
				'Password must contain at least one special character'
			)
			.optional(),
		role: z.enum(['super_admin', 'admin', 'editor', 'author']).optional()
	}),

	/**
	 * Category validation schema
	 */
	category: z.object({
		name: z.string().min(1, 'Category name is required').max(100, 'Category name too long'),
		slug: z
			.string()
			.min(1, 'Slug is required')
			.max(100, 'Slug too long')
			.regex(/^[a-z0-9-]+$/, 'Slug must contain only lowercase letters, numbers, and hyphens'),
		description: z.string().max(500, 'Description too long').optional(),
		parent_id: z.number().int().positive().optional().or(z.null())
	}),

	/**
	 * API key validation schema
	 */
	apiKey: z.object({
		name: z.string().min(1, 'API key name is required').max(100, 'Name too long'),
		permissions: z.array(z.string()).optional().default([]),
		rate_limit: z
			.number()
			.int()
			.min(1, 'Rate limit must be at least 1')
			.max(10000, 'Rate limit too high')
			.optional()
			.default(1000),
		expires_at: z.string().datetime().optional().or(z.null())
	}),

	/**
	 * Settings validation schema
	 */
	settings: z.object({
		key: z
			.string()
			.min(1, 'Setting key is required')
			.max(100, 'Key too long')
			.regex(/^[a-z0-9_]+$/, 'Key must contain only lowercase letters, numbers, and underscores'),
		value: z.string(),
		type: z.enum(['string', 'number', 'boolean', 'json']).optional().default('string')
	}),

	/**
	 * Ad validation schema
	 */
	ad: z.object({
		name: z.string().min(1, 'Ad name is required').max(255, 'Name too long'),
		placement: z.enum(['sidebar', 'home_middle', 'post_inline', 'in_article']),
		type: z.enum(['html', 'image', 'text', 'native']),
		content: z.string().optional(),
		image_url: z.string().url('Invalid image URL').optional().or(z.literal('')),
		link_url: z.string().url('Invalid link URL').optional().or(z.literal('')),
		is_active: z.boolean().optional().default(true),
		weight: z.number().int().min(1).max(100).optional().default(1)
	}),

	/**
	 * Login validation schema
	 */
	login: z.object({
		email: z.string().email('Invalid email address'),
		password: z.string().min(1, 'Password is required')
	}),

	/**
	 * Newsletter subscription schema
	 */
	newsletter: z.object({
		email: z.string().email('Invalid email address').max(255, 'Email too long')
	})
};

/**
 * Validate input data against a schema
 * 
 * @param schema - Zod validation schema
 * @param data - Data to validate
 * @returns Validated and typed data
 * @throws ZodError if validation fails
 */
export function validateInput<T>(schema: z.ZodSchema<T>, data: unknown): T {
	return schema.parse(data);
}

/**
 * Validate input data and return result with errors
 * 
 * @param schema - Zod validation schema
 * @param data - Data to validate
 * @returns Validation result with success flag and data or errors
 */
export function safeValidateInput<T>(
	schema: z.ZodSchema<T>,
	data: unknown
): { success: true; data: T } | { success: false; errors: z.ZodError } {
	const result = schema.safeParse(data);

	if (result.success) {
		return { success: true, data: result.data };
	} else {
		return { success: false, errors: result.error };
	}
}

/**
 * File upload validation options
 */
export interface FileValidationOptions {
	/** Maximum file size in bytes (default: 10MB) */
	maxSize?: number;
	/** Allowed MIME types */
	allowedTypes?: string[];
	/** Allowed file extensions */
	allowedExtensions?: string[];
}

/**
 * File validation result
 */
export interface FileValidationResult {
	/** Whether the file is valid */
	valid: boolean;
	/** Error message if invalid */
	error?: string;
}

/**
 * Validate file upload
 * 
 * @param file - File object to validate
 * @param options - Validation options
 * @returns Validation result
 */
export function validateFileUpload(
	file: File,
	options: FileValidationOptions = {}
): FileValidationResult {
	const maxSize = options.maxSize || 10 * 1024 * 1024; // 10MB default
	const allowedTypes = options.allowedTypes || [
		'image/jpeg',
		'image/png',
		'image/gif',
		'image/webp',
		'image/svg+xml'
	];

	// Check file size
	if (file.size > maxSize) {
		return {
			valid: false,
			error: `File size exceeds ${maxSize / 1024 / 1024}MB limit`
		};
	}

	// Check MIME type
	if (!allowedTypes.includes(file.type)) {
		return {
			valid: false,
			error: `File type ${file.type} is not allowed. Allowed types: ${allowedTypes.join(', ')}`
		};
	}

	// Check file extension if specified
	if (options.allowedExtensions) {
		const extension = file.name.split('.').pop()?.toLowerCase();
		if (!extension || !options.allowedExtensions.includes(extension)) {
			return {
				valid: false,
				error: `File extension .${extension} is not allowed. Allowed extensions: ${options.allowedExtensions.join(', ')}`
			};
		}
	}

	return { valid: true };
}

/**
 * Sanitize filename to prevent directory traversal attacks
 * 
 * @param filename - Original filename
 * @returns Safe filename
 */
export function sanitizeFilename(filename: string): string {
	// Remove path separators and null bytes
	return filename
		.replace(/[\/\\]/g, '')
		.replace(/\0/g, '')
		.replace(/\.\./g, '')
		.trim();
}

/**
 * Generate a safe random filename
 * 
 * @param originalFilename - Original filename to extract extension
 * @returns Random filename with original extension
 */
export function generateSafeFilename(originalFilename: string): string {
	const extension = originalFilename.split('.').pop()?.toLowerCase() || '';
	const randomName = crypto.randomUUID();
	return extension ? `${randomName}.${extension}` : randomName;
}
