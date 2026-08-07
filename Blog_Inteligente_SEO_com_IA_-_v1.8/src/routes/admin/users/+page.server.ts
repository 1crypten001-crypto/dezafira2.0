import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { 
  query, 
  getAllPremiumPlans, 
  deleteUser, 
  grantPremiumAccessManual, 
  revokePremiumAccessManual 
} from '$lib/server/database';

export const load: PageServerLoad = async () => {
  // Load users with their latest subscription details
  const members = await query(`
    SELECT u.id, u.username, u.created_at, 
           s.status as sub_status, s.expires_at as sub_expires_at, s.plan_id,
           p.name as plan_name
    FROM users u
    LEFT JOIN premium_subscriptions s ON u.id = s.user_id 
      AND s.id = (SELECT MAX(id) FROM premium_subscriptions WHERE user_id = u.id)
    LEFT JOIN premium_plans p ON s.plan_id = p.id
    WHERE u.role = 'member'
    ORDER BY u.created_at DESC
  `);

  const plans = await getAllPremiumPlans();

  return {
    members,
    plans
  };
};

export const actions: Actions = {
  delete: async ({ request }) => {
    const data = await request.formData();
    const userIdStr = data.get('user_id') as string;

    if (!userIdStr) {
      return fail(400, { error: 'ID do usuário não fornecido' });
    }

    const userId = parseInt(userIdStr);
    try {
      await deleteUser(userId);
      return { success: 'Usuário excluído com sucesso' };
    } catch (e) {
      console.error('Error deleting user:', e);
      return fail(500, { error: 'Erro ao excluir usuário' });
    }
  },

  togglePremium: async ({ request }) => {
    const data = await request.formData();
    const userIdStr = data.get('user_id') as string;
    const action = data.get('action') as string; // 'grant' or 'revoke'
    const planIdStr = data.get('plan_id') as string;

    if (!userIdStr) {
      return fail(400, { error: 'ID do usuário não fornecido' });
    }

    const userId = parseInt(userIdStr);

    try {
      if (action === 'grant') {
        const plans = await getAllPremiumPlans();
        const activePlans = plans.filter(p => p.is_active !== 0);
        
        let planId = planIdStr ? parseInt(planIdStr) : null;
        if (!planId && activePlans.length > 0) {
          planId = activePlans[0].id;
        }

        if (!planId) {
          return fail(400, { error: 'Nenhum plano premium ativo cadastrado' });
        }

        await grantPremiumAccessManual(userId, planId, 30);
        return { success: 'Acesso Premium concedido por 30 dias' };
      } else if (action === 'revoke') {
        await revokePremiumAccessManual(userId);
        return { success: 'Acesso Premium revogado' };
      }

      return fail(400, { error: 'Ação inválida' });
    } catch (e) {
      console.error('Error toggling premium access:', e);
      return fail(500, { error: 'Erro ao alterar acesso premium' });
    }
  }
};
