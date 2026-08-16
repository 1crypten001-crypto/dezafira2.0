import { redirect, fail } from '@sveltejs/kit';
import { createPremiumPlan } from '$lib/server/database';

export const actions = {
    default: async ({ request }) => {
        const data = await request.formData();

        const name = (data.get('name') as string || '').trim();
        const slug = (data.get('slug') as string || '').trim();
        const description = (data.get('description') as string || '').trim();
        const price_cents = parseInt(String(data.get('price_cents') || '0'), 10) || 0;
        const interval_days = parseInt(String(data.get('interval_days') || '30'), 10) || 30;
        const featuresRaw = (data.get('features') as string) || '';
        const is_active = data.get('is_active') === 'on' ? 1 : 0;

        if (!name || !slug || !price_cents) {
            return fail(400, { message: 'PREMIUM_REQUIRED_FIELDS' });
        }

        let features: string[] = [];
        if (featuresRaw) {
            try {
                features = JSON.parse(featuresRaw);
            } catch {
                features = featuresRaw.split('\n').map((s) => s.trim()).filter(Boolean);
            }
        }

        await createPremiumPlan({
            name,
            slug,
            description,
            price_cents,
            interval_days,
            features,
            is_active
        });

        throw redirect(303, '/admin/premium/plans');
    }
};
