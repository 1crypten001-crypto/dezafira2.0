<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from "$app/forms";


    let { data, form } = $props();
  const lang = $derived($page.data.language || 'pt');
let newCategoryName = $state("");
    let newCategoryDescription = $state("");
    let editingId = $state<number | null>(null);
    let editingName = $state("");
    let editingDescription = $state("");

    function startEdit(id: number, name: string, description: string | null) {
        editingId = id;
        editingName = name;
        editingDescription = description || "";
    }

    function cancelEdit() {
        editingId = null;
        editingName = "";
        editingDescription = "";
    }

    function confirmDelete(event: Event) {
        if (!confirm(t(lang, 'admin.categories.confirm_delete'))) {
            event.preventDefault();
        }
    }
</script>

<svelte:head>
    <title>Admin | {t(lang, "admin.products.categories_title")}</title>
</svelte:head>

<div class="categories-page">
    <div class="page-header">
        <h1>{t(lang, "admin.products.categories_title")}</h1>
        <p class="subtitle">Crie e gerencie as categorias dos seus recursos digitais</p>
    </div>

    {#if form?.success}
        <div class="alert success">{form.message}</div>
    {/if}
    {#if form?.error}
        <div class="alert error">{form.error}</div>
    {/if}

    <div class="grid-layout">
        <!-- Create New Category -->
        <div class="card create-card">
            <h2>Nova Categoria</h2>
            <form method="POST" action="?/create" use:enhance class="form-container">
                <div class="form-group">
                    <label for="name">Nome da Categoria</label>
                    <input
                        type="text"
                        id="name"
                        name="name"
                        bind:value={newCategoryName}
                        placeholder="Ex: E-books, Scripts, Cursos"
                        required
                        minlength="2"
                    />
                </div>
                <div class="form-group">
                    <label for="description">Descrição (Opcional)</label>
                    <textarea
                        id="description"
                        name="description"
                        bind:value={newCategoryDescription}
                        placeholder="Breve descrição da categoria..."
                        rows="2"
                    ></textarea>
                </div>
                <button type="submit" class="btn btn-primary" style="align-self: flex-end;">{t(lang, "admin.products.categories_new")}</button>
            </form>
        </div>

        <!-- Categories List -->
        <div class="card">
            <h2>Todas as Categorias ({data.categories.length})</h2>

            {#if data.categories.length === 0}
                <div class="empty-state">
                    <p>{t(lang, "admin.categories.empty")}</p>
                </div>
            {:else}
                <div class="categories-list">
                    {#each data.categories as category}
                        <div class="category-item">
                            {#if editingId === category.id}
                                <form
                                    method="POST"
                                    action="?/update"
                                    use:enhance
                                    class="edit-form"
                                >
                                    <input
                                        type="hidden"
                                        name="id"
                                        value={category.id}
                                    />
                                    <div class="form-group">
                                        <label for="edit_name">{t(lang, "admin.ui.name")}</label>
                                        <input
                                            type="text"
                                            id="edit_name"
                                            name="name"
                                            bind:value={editingName}
                                            required
                                            minlength="2"
                                            class="edit-input"
                                        />
                                    </div>
                                    <div class="form-group" style="margin-top: 0.5rem;">
                                        <label for="edit_desc">{t(lang, "admin.ui.description")}</label>
                                        <textarea
                                            id="edit_desc"
                                            name="description"
                                            bind:value={editingDescription}
                                            rows="2"
                                            class="edit-input"
                                        ></textarea>
                                    </div>
                                    <div class="edit-actions">
                                        <button type="submit" class="btn btn-small btn-primary">{t(lang, "admin.ui.save")}</button>
                                        <button
                                            type="button"
                                            class="btn btn-small btn-secondary"
                                            onclick={cancelEdit}
                                        >
                                            Cancelar
                                        </button>
                                    </div>
                                </form>
                            {:else}
                                <div class="category-details">
                                    <span class="category-name">{category.name}</span>
                                    {#if category.description}
                                        <p class="category-desc">{category.description}</p>
                                    {/if}
                                    <span class="category-slug">slug: <code>{category.slug}</code></span>
                                </div>
                                <div class="category-actions">
                                    <button
                                        type="button"
                                        class="btn btn-small btn-secondary"
                                        onclick={() => startEdit(category.id, category.name, category.description)}
                                    >
                                        Editar
                                    </button>
                                    <form
                                        method="POST"
                                        action="?/delete"
                                        use:enhance
                                        style="display: inline;"
                                        onsubmit={confirmDelete}
                                    >
                                        <input
                                            type="hidden"
                                            name="id"
                                            value={category.id}
                                        />
                                        <button
                                            type="submit"
                                            class="btn btn-small btn-danger"
                                        >
                                            {t(lang, "admin.ui.delete")}
                                        </button>
                                    </form>
                                </div>
                            {/if}
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    .categories-page {
        max-width: 1100px;
        margin: 0 auto;
        padding: 1.5rem;
    }

    .page-header {
        margin-bottom: 2rem;
    }

    .page-header h1 {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }

    .subtitle {
        color: var(--text-muted);
        margin: 0.25rem 0 0 0;
    }

    .grid-layout {
        display: grid;
        grid-template-columns: 1fr;
        gap: 1.5rem;
    }

    @media (min-width: 768px) {
        .grid-layout {
            grid-template-columns: 350px 1fr;
        }
    }

    .card {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
        height: fit-content;
    }

    .card h2 {
        font-size: 1.15rem;
        font-weight: 600;
        margin: 0 0 1.25rem 0;
        color: var(--text-primary);
    }

    .form-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .form-group {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }

    .form-group label {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-secondary);
    }

    .form-group input,
    .form-group textarea {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        padding: 0.65rem;
        border-radius: var(--radius-md);
        font-family: inherit;
    }

    .form-group input:focus,
    .form-group textarea:focus {
        outline: none;
        border-color: var(--accent-color, #3b82f6);
    }

    .alert {
        padding: 1rem;
        border-radius: var(--radius-md);
        margin-bottom: 1.5rem;
        font-weight: 500;
    }

    .alert.success {
        background: rgba(34, 197, 94, 0.1);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.2);
    }

    .alert.error {
        background: rgba(239, 68, 68, 0.1);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }

    .categories-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .category-item {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 1rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        gap: 1rem;
    }

    .category-details {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        flex: 1;
    }

    .category-name {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 1.05rem;
    }

    .category-desc {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin: 0;
    }

    .category-slug {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .category-slug code {
        font-family: monospace;
        background: var(--bg-primary);
        padding: 0.1rem 0.3rem;
        border-radius: var(--radius-xs);
    }

    .category-actions {
        display: flex;
        gap: 0.5rem;
        align-self: center;
    }

    .edit-form {
        width: 100%;
        display: flex;
        flex-direction: column;
    }

    .edit-input {
        width: 100%;
    }

    .edit-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.75rem;
    }

    .empty-state {
        text-align: center;
        padding: 2rem 0;
        color: var(--text-muted);
    }
</style>
