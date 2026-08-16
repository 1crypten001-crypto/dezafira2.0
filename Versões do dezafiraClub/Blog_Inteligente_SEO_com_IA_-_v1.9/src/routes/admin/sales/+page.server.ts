import { getSalesSummary, getSalesHistory, getUsersHoldings, markManualDelivered, queryOne } from '$lib/server/database';
import { sendManualAccessDeliveredEmail } from '$lib/server/resend';
import { fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';

export const load: PageServerLoad = async () => {
	const [summary, history, holdings] = await Promise.all([
		getSalesSummary(),
		getSalesHistory(),
		getUsersHoldings()
	]);

	return {
		summary,
		history,
		holdings
	};
};

export const actions: Actions = {
    markDelivered: async ({ request }) => {
        const data = await request.formData();
        const purchaseId = parseInt(data.get('purchase_id') as string);

        if (!purchaseId || isNaN(purchaseId)) {
            return fail(400, { message: 'ID da compra inválido.' });
        }

        // Busca dados da compra para enviar e-mail de notificação
        const purchase = await queryOne(
            `SELECT pp.*, u.username as buyer_email, u.name as buyer_name, p.name as product_name, p.drive_instructions
             FROM product_purchases pp
             JOIN users u ON pp.user_id = u.id
             LEFT JOIN products p ON pp.product_id = p.id
             WHERE pp.id = ? AND pp.status = 'pending_delivery'`,
            [purchaseId]
        );

        if (!purchase) {
            return fail(404, { message: 'Compra não encontrada ou já entregue.' });
        }

        // Marca como entregue no banco
        await markManualDelivered(purchaseId);

        // Envia e-mail de notificação ao comprador usando nossa utilidade Resend interna
        try {
            const buyerName = purchase.buyer_name || purchase.buyer_email.split('@')[0];
            const productName = purchase.product_name || 'seu produto';
            const instructions = purchase.drive_instructions || 'Verifique sua área de membros ou entre em contato conosco caso não encontre o acesso.';
            const accessId = purchase.buyer_access_id || purchase.buyer_email;

            await sendManualAccessDeliveredEmail(
                purchase.buyer_email,
                buyerName,
                productName,
                accessId,
                instructions
            );
            console.log(`[SALES] Notificação de entrega enviada para ${purchase.buyer_email} (compra #${purchaseId})`);
        } catch (emailErr) {
            // Não falha se o e-mail não enviar — entrega já foi marcada no banco
            console.error('[SALES] Erro ao enviar e-mail de notificação de entrega:', emailErr);
        }

        return { success: true, message: 'Entrega marcada com sucesso! O comprador foi notificado por e-mail.' };
    }
};
