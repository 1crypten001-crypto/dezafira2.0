<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from "$app/forms";


  let { data, form } = $props();
  const lang = $derived($page.data.language || 'pt');
let loadingToggle = $state<number | null>(null);
  let loadingDelete = $state<number | null>(null);

  function formatDate(isoString: string | null) {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleDateString(lang === 'en' ? 'en-US' : lang === 'es' ? 'es-ES' : 'pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function handleConfirmDelete(e: Event) {
    if (!confirm("ATENÇÃO: Isso excluirá permanentemente este usuário, suas sessões e assinaturas locais. Deseja prosseguir?")) {
      e.preventDefault();
    }
  }

  function isPremiumActive(status: string | null, expiresAt: string | null) {
    if (!status || status !== 'active') return false;
    if (!expiresAt) return false;
    return new Date(expiresAt) > new Date();
  }

  function handleDarPremium(e: Event) {
    if (!data.plans || data.plans.length === 0) {
      e.preventDefault();
      alert(t(lang, 'admin.users.no_plan'));
      window.location.href = "/admin/premium/plans";
    }
  }
</script>

<svelte:head>
  <title>{t(lang, "admin.users.title")}</title>
</svelte:head>

<div class="admin-header">
  <div>
    <h1 class="admin-title">{t(lang, "admin.users.heading")}</h1>
    <p class="admin-subtitle">{t(lang, "admin.users.subtitle")}</p>
  </div>
</div>

{#if form?.error}
  <div class="alert error">{form.error}</div>
{/if}

{#if form?.success}
  <div class="alert success">{form.success}</div>
{/if}

<div class="admin-table-container">
  <table class="table">
    <thead>
      <tr>
        <th>ID</th>
        <th>{t(lang, "admin.users.col_email")}</th>
        <th>{t(lang, "admin.users.col_joined")}</th>
        <th>{t(lang, "admin.users.col_premium")}</th>
        <th>{t(lang, "admin.users.col_plan")}</th>
        <th>{t(lang, "admin.users.col_expiry")}</th>
        <th>{t(lang, "admin.ui.actions")}</th>
      </tr>
    </thead>
    <tbody>
      {#if data.members.length === 0}
        <tr>
          <td colspan="7" class="text-center py-4">{t(lang, "admin.users.empty")}</td>
        </tr>
      {/if}
      {#each data.members as member}
        {@const isPremium = isPremiumActive(member.sub_status, member.sub_expires_at)}
        <tr>
          <td>{member.id}</td>
          <td><strong>{member.username}</strong></td>
          <td>{formatDate(member.created_at)}</td>
          <td>
            <span class="status status-{isPremium ? 'published' : 'draft'}">
              {isPremium ? 'Premium Ativo' : 'Inativo / Gratuito'}
            </span>
          </td>
          <td>{member.plan_name || '-'}</td>
          <td>{member.sub_expires_at ? formatDate(member.sub_expires_at) : '-'}</td>
          <td>
            <div class="actions-wrapper">
              <!-- Toggle Premium Form -->
              <form 
                action="?/togglePremium" 
                method="POST" 
                use:enhance={() => {
                  loadingToggle = member.id;
                  return async ({ update }) => {
                    loadingToggle = null;
                    await update();
                  };
                }}
              >
                <input type="hidden" name="user_id" value={member.id} />
                {#if isPremium}
                  <input type="hidden" name="action" value="revoke" />
                  <button 
                    type="submit" 
                    class="btn btn-small btn-secondary" 
                    disabled={loadingToggle === member.id}
                  >
                    {loadingToggle === member.id ? 'Aguarde...' : '{t(lang, "admin.users.revoke_premium")}'}
                  </button>
                {:else}
                  <input type="hidden" name="action" value="grant" />
                  {#if data.plans && data.plans.length > 0}
                    <!-- Select plan if multiple are available -->
                    <select name="plan_id" class="plan-select" disabled={loadingToggle === member.id}>
                      {#each data.plans as plan}
                        {#if plan.is_active !== 0}
                          <option value={plan.id}>{plan.name}</option>
                        {/if}
                      {/each}
                    </select>
                  {/if}
                  <button 
                    type="submit" 
                    class="btn btn-small btn-primary" 
                    disabled={loadingToggle === member.id}
                    onclick={handleDarPremium}
                  >
                    {loadingToggle === member.id ? 'Aguarde...' : 'Dar Premium'}
                  </button>
                {/if}
              </form>

              <!-- Delete User Form -->
              <form 
                action="?/delete" 
                method="POST" 
                use:enhance={() => {
                  loadingDelete = member.id;
                  return async ({ update }) => {
                    loadingDelete = null;
                    await update();
                  };
                }}
              >
                <input type="hidden" name="user_id" value={member.id} />
                <button 
                  type="submit" 
                  class="btn btn-small btn-danger" 
                  onclick={handleConfirmDelete}
                  disabled={loadingDelete === member.id}
                >
                  {loadingDelete === member.id ? 'Excluindo...' : 'Excluir'}
                </button>
              </form>
            </div>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .admin-header {
    margin-bottom: 2rem;
  }

  .admin-title {
    font-family: var(--font-sans);
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 0 0.25rem 0;
  }

  .admin-subtitle {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0;
  }

  .admin-table-container {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow-x: auto;
    width: 100%;
    margin-bottom: 2rem;
  }

  .status {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-family: var(--font-sans);
    font-size: 0.625rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-radius: var(--radius-sm);
  }

  .status-published {
    background: #d1fae5;
    color: #065f46;
  }

  .status-draft {
    background: #f3f4f6;
    color: #374151;
  }

  .actions-wrapper {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .actions-wrapper form {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
  }

  .plan-select {
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    outline: none;
    cursor: pointer;
  }

  .btn-danger {
    border-color: #ef4444;
    color: #ef4444;
  }

  .btn-danger:hover {
    background: #ef4444;
    color: white;
  }

  .text-center {
    text-align: center;
  }
  
  .py-4 {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
  }

  .alert {
    padding: 1rem;
    margin-bottom: 1.5rem;
    border-radius: var(--radius-md);
    font-size: 0.9rem;
  }

  .alert.error {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
  }

  .alert.success {
    background: #f0fdf4;
    color: #16a34a;
    border: 1px solid #bbf7d0;
  }
</style>
