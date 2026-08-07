import { fail, redirect, isRedirect } from '@sveltejs/kit';
import { getSettings, updateSetting } from '$lib/server/database';
import { getTenantId } from '$lib/server/tenant';
import { env } from '$env/dynamic/private';
import { uploadImage } from '$lib/server/cloudinary';

export async function load() {
	const tenantId = getTenantId();
	const settings = await getSettings(tenantId);
	return { 
		settings,
		hasEnvApiKey: !!env.GEMINI_API_KEY,
		envApiModel: env.GEMINI_API_MODEL || 'gemini-2.5-flash'
	};
}

export const actions = {
	general: async ({ request }) => {
		try {
			const tenantId = getTenantId();
			const data = await request.formData();
			const site_title = data.get('site_title') as string;
			const site_description = data.get('site_description') as string;
			const site_keywords = data.get('site_keywords') as string;
			const feed_loading_mode = data.get('feed_loading_mode') as string;
			const enable_recommendations = data.get('enable_recommendations') as string;
			let site_logo = (data.get('site_logo') as string) || '';
			let site_favicon = (data.get('site_favicon') as string) || '';
			let seo_image = (data.get('seo_image') as string) || '';

			const site_logo_file = data.get('site_logo_file');
			const site_favicon_file = data.get('site_favicon_file');
			const seo_image_file = data.get('seo_image_file');

			const isCloudinaryConfigured = !!(env.CLOUDINARY_CLOUD_NAME && env.CLOUDINARY_API_KEY && env.CLOUDINARY_API_SECRET);

			if (site_logo_file && site_logo_file instanceof File && site_logo_file.size > 0) {
				try {
					if (isCloudinaryConfigured) {
						site_logo = await uploadImage(site_logo_file, 'blog/settings');
					} else {
						const buffer = Buffer.from(await site_logo_file.arrayBuffer());
						const extension = site_logo_file.name.split('.').pop() || 'png';
						const filename = `logo-${Date.now()}.${extension}`;

						const fs = await import('fs');
						const path = await import('path');
						const uploadDir = path.join(process.cwd(), 'static', 'uploads');

						if (!fs.existsSync(uploadDir)) {
							fs.mkdirSync(uploadDir, { recursive: true });
						}

						fs.writeFileSync(path.join(uploadDir, filename), buffer);
						site_logo = `/uploads/${filename}`;
					}
				} catch (e) {
					console.error('Error uploading site logo:', e);
					return fail(500, { message: 'Erro ao fazer upload do logo' });
				}
			}

			if (site_favicon_file && site_favicon_file instanceof File && site_favicon_file.size > 0) {
				try {
					if (isCloudinaryConfigured) {
						site_favicon = await uploadImage(site_favicon_file, 'blog/settings');
					} else {
						const buffer = Buffer.from(await site_favicon_file.arrayBuffer());
						const extension = site_favicon_file.name.split('.').pop() || 'png';
						const filename = `favicon-${Date.now()}.${extension}`;

						const fs = await import('fs');
						const path = await import('path');
						const uploadDir = path.join(process.cwd(), 'static', 'uploads');

						if (!fs.existsSync(uploadDir)) {
							fs.mkdirSync(uploadDir, { recursive: true });
						}

						fs.writeFileSync(path.join(uploadDir, filename), buffer);
						site_favicon = `/uploads/${filename}`;
					}
				} catch (e) {
					console.error('Error uploading site favicon:', e);
					return fail(500, { message: 'Erro ao fazer upload do favicon' });
				}
			}

			if (seo_image_file && seo_image_file instanceof File && seo_image_file.size > 0) {
				try {
					if (isCloudinaryConfigured) {
						seo_image = await uploadImage(seo_image_file, 'blog/settings');
					} else {
						const buffer = Buffer.from(await seo_image_file.arrayBuffer());
						const extension = seo_image_file.name.split('.').pop() || 'png';
						const filename = `og-image-${Date.now()}.${extension}`;

						const fs = await import('fs');
						const path = await import('path');
						const uploadDir = path.join(process.cwd(), 'static', 'uploads');

						if (!fs.existsSync(uploadDir)) {
							fs.mkdirSync(uploadDir, { recursive: true });
						}

						fs.writeFileSync(path.join(uploadDir, filename), buffer);
						seo_image = `/uploads/${filename}`;
					}
				} catch (e) {
					console.error('Error uploading SEO image:', e);
					return fail(500, { message: 'Erro ao fazer upload da imagem' });
				}
			}

			const og_app_id = data.get('og_app_id') as string;
			const twitter_handle = data.get('twitter_handle') as string;
			const footer_text = data.get('footer_text') as string;
			const admin_email = data.get('admin_email') as string;
			const default_theme = data.get('default_theme') as string;
			const custom_head_script = data.get('custom_head_script') as string;
			const custom_body_script = data.get('custom_body_script') as string;
			const whatsapp_enable = data.get('whatsapp_enable') === '1' || data.get('whatsapp_enable') === 'on' ? '1' : '0';
			const whatsapp_number = data.get('whatsapp_number') as string;
			const whatsapp_message = data.get('whatsapp_message') as string;
			const site_language = data.get('site_language') as string;

			await updateSetting('site_title', site_title || '', tenantId);
			await updateSetting('site_description', site_description || '', tenantId);
			await updateSetting('site_keywords', site_keywords || '', tenantId);
			await updateSetting(
				'feed_loading_mode',
				feed_loading_mode === 'infinite' ? 'infinite' : 'pagination',
				tenantId
			);
			await updateSetting('enable_recommendations', enable_recommendations === '0' ? '0' : '1', tenantId);
			await updateSetting('site_logo', site_logo || '', tenantId);
			await updateSetting('site_favicon', site_favicon || '', tenantId);
			await updateSetting('seo_image', seo_image || '', tenantId);
			await updateSetting('og_app_id', og_app_id || '', tenantId);
			await updateSetting('twitter_handle', twitter_handle || '', tenantId);
			await updateSetting('footer_text', footer_text || '', tenantId);
			await updateSetting('admin_email', admin_email || '', tenantId);
			await updateSetting('default_theme', default_theme === 'dark' ? 'dark' : 'light', tenantId);
			await updateSetting('custom_head_script', custom_head_script || '', tenantId);
			await updateSetting('custom_body_script', custom_body_script || '', tenantId);
			await updateSetting('whatsapp_enable', whatsapp_enable, tenantId);
			await updateSetting('whatsapp_number', whatsapp_number || '', tenantId);
			await updateSetting('whatsapp_message', whatsapp_message || '', tenantId);
			await updateSetting('site_language', site_language === 'en' || site_language === 'es' ? site_language : 'pt', tenantId);

			throw redirect(303, '/admin/settings?tab=general&success=true');
		} catch (e) {
			if (isRedirect(e)) throw e;
			console.error('Error saving settings:', e);
			return fail(500, { message: 'Erro ao salvar configurações' });
		}
	},

	api: async ({ request }) => {
		const tenantId = getTenantId();
		const data = await request.formData();

		const gemini_api_key = data.get('gemini_api_key') as string;
		const gemini_api_model = data.get('gemini_api_model') as string;
		const site_url = data.get('site_url') as string;

		const payment_gateway_raw = (data.get('payment_gateway') as string) || 'asaas';
		// Hard default: only allow asaas|stripe; anything else falls back to asaas (production safe)
		const payment_gateway = payment_gateway_raw === 'stripe' ? 'stripe' : 'asaas';
		const asaas_api_key = data.get('asaas_api_key') as string;
		const asaas_api_url = data.get('asaas_api_url') as string;
		const asaas_webhook_secret = data.get('asaas_webhook_secret') as string;
		const stripe_secret_key = data.get('stripe_secret_key') as string;
		const stripe_publishable_key = data.get('stripe_publishable_key') as string;
		const stripe_webhook_secret = data.get('stripe_webhook_secret') as string;
		const stripe_currency_raw = ((data.get('stripe_currency') as string) || 'brl').toLowerCase().trim();
		const stripe_currency = /^[a-z]{3}$/.test(stripe_currency_raw) ? stripe_currency_raw : 'brl';
		const enable_member_login = data.get('enable_member_login') === '1' || data.get('enable_member_login') === 'on' ? '1' : '0';

		const resend_api_key = data.get('resend_api_key') as string;
		const resend_from_email = data.get('resend_from_email') as string;
		const enable_otp_login = data.get('enable_otp_login') === '1' || data.get('enable_otp_login') === 'on' ? '1' : '0';
		const sidebar_products_display_mode = data.get('sidebar_products_display_mode') as string;
		const microsoft_clarity_project_id = data.get('microsoft_clarity_project_id') as string;

		await updateSetting('gemini_api_key', gemini_api_key || '', tenantId);
		await updateSetting('gemini_api_model', gemini_api_model || 'gemini-2.5-flash', tenantId);
		await updateSetting('site_url', site_url || '', tenantId);

		await updateSetting('payment_gateway', payment_gateway, tenantId);
		await updateSetting('asaas_api_key', asaas_api_key || '', tenantId);
		await updateSetting('asaas_api_url', asaas_api_url || 'https://api-sandbox.asaas.com/v3', tenantId);
		await updateSetting('asaas_webhook_secret', asaas_webhook_secret || '', tenantId);
		await updateSetting('stripe_secret_key', stripe_secret_key || '', tenantId);
		await updateSetting('stripe_publishable_key', stripe_publishable_key || '', tenantId);
		await updateSetting('stripe_webhook_secret', stripe_webhook_secret || '', tenantId);
		await updateSetting('stripe_currency', stripe_currency, tenantId);
		await updateSetting('enable_member_login', enable_member_login, tenantId);

		await updateSetting('resend_api_key', resend_api_key || '', tenantId);
		await updateSetting('resend_from_email', resend_from_email || 'onboarding@resend.dev', tenantId);
		await updateSetting('enable_otp_login', enable_otp_login, tenantId);
		await updateSetting('sidebar_products_display_mode', sidebar_products_display_mode || 'carousel', tenantId);
		await updateSetting('microsoft_clarity_project_id', microsoft_clarity_project_id || '', tenantId);

		throw redirect(303, '/admin/settings?tab=api&success=true');
	},

	seo: async ({ request }) => {
		const tenantId = getTenantId();
		const data = await request.formData();

		const rss_feed_title = data.get('rss_feed_title') as string;
		const rss_feed_description = data.get('rss_feed_description') as string;
		const sitemap_priority_home = data.get('sitemap_priority_home') as string;
		const sitemap_priority_posts = data.get('sitemap_priority_posts') as string;
		const sitemap_priority_categories = data.get('sitemap_priority_categories') as string;
		const sitemap_changefreq_home = data.get('sitemap_changefreq_home') as string;
		const sitemap_changefreq_posts = data.get('sitemap_changefreq_posts') as string;
		const google_news_keywords = data.get('google_news_keywords') as string;
		const google_news_image_min_width = data.get('google_news_image_min_width') as string;
		const ads_txt = data.get('ads_txt') as string;

		await updateSetting('rss_feed_title', rss_feed_title || '', tenantId);
		await updateSetting('rss_feed_description', rss_feed_description || '', tenantId);
		await updateSetting('sitemap_priority_home', sitemap_priority_home || '1.0', tenantId);
		await updateSetting('sitemap_priority_posts', sitemap_priority_posts || '0.9', tenantId);
		await updateSetting(
			'sitemap_priority_categories',
			sitemap_priority_categories || '0.6',
			tenantId
		);
		await updateSetting('sitemap_changefreq_home', sitemap_changefreq_home || 'daily', tenantId);
		await updateSetting('sitemap_changefreq_posts', sitemap_changefreq_posts || 'weekly', tenantId);
		await updateSetting(
			'google_news_keywords',
			google_news_keywords || 'noticia, artigo, blog',
			tenantId
		);
		await updateSetting('google_news_image_min_width', google_news_image_min_width || '1600', tenantId);
		await updateSetting('ads_txt', ads_txt || '', tenantId);

		throw redirect(303, '/admin/settings?tab=seo&success=true');
	},

	security: async ({ request, cookies }) => {
		try {
			const { validateSession, verifyLogin, hashPassword, validatePasswordStrength } = await import('$lib/server/auth');
			const token = cookies.get('admin_session');
			const username = await validateSession(token || '');
			if (!username) {
				return fail(401, { message: 'Não autorizado' });
			}

			const data = await request.formData();
			const current_password = data.get('current_password') as string;
			const new_password = data.get('new_password') as string;
			const confirm_password = data.get('confirm_password') as string;

			if (!current_password || !new_password || !confirm_password) {
				return fail(400, { message: 'Preencha todos os campos' });
			}

			if (new_password !== confirm_password) {
				return fail(400, { message: 'A nova senha e a confirmação não coincidem' });
			}

			// Validar força da nova senha
			const strength = validatePasswordStrength(new_password);
			if (!strength.valid) {
				return fail(400, { message: strength.message });
			}

			// Verificar se a senha atual está correta
			const valid = await verifyLogin(username, current_password);
			if (!valid) {
				return fail(400, { message: 'Senha atual incorreta' });
			}

			// Atualizar senha no banco
			const hashedPassword = await hashPassword(new_password);
			const { updateUserPassword } = await import('$lib/server/database');
			await updateUserPassword(username, hashedPassword);

			throw redirect(303, '/admin/settings?tab=security&success=true');
		} catch (e) {
			if (isRedirect(e)) throw e;
			console.error('Error changing admin password:', e);
			return fail(500, { message: 'Erro ao alterar a senha' });
		}
	}
};
