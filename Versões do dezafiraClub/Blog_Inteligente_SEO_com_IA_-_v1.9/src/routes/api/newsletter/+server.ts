import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { subscribeToNewsletter } from '$lib/server/database';

export const POST: RequestHandler = async ({ request }) => {
    try {
        const { email, name } = await request.json();
        
        if (!email) {
            return json({ success: false, error: 'E-mail é obrigatório' }, { status: 400 });
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return json({ success: false, error: 'E-mail inválido' }, { status: 400 });
        }

        await subscribeToNewsletter(email, name);

        return json({ success: true, message: 'Inscrição realizada com sucesso' });
    } catch (error) {
        console.error('Error subscribing to newsletter:', error);
        return json({ success: false, error: 'Erro ao processar inscrição' }, { status: 500 });
    }
};