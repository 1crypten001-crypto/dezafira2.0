<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatDate as fmtDate, formatMoney } from "$lib/i18n";
  import { enhance } from "$app/forms";


    let { data, form } = $props();
  const lang = $derived($page.data.language || 'pt');
let newCategoryName = $state("");
    let editingId = $state<number | null>(null);
    let editingName = $state("");

    function startEdit(id: number, name: string) {
        editingId = id;
        editingName = name;
    }

    function cancelEdit() {
        editingId = null;
        editingName = "";
    }

    function confirmDelete(event: Event) {
        if (!confirm(t(lang, 'admin.categories.confirm_delete'))) {
            event.preventDefault();
        }
    }
</script>

<svelte:head>
    <title>{t(lang, "admin.categories.title")}</title>
</svelte:head>

<div class="categories-page">
    <div class="page-header">
        <h1>{t(lang, "admin.categories.heading")}</h1>
        <p class="subtitle">{t(lang, "admin.categories.heading")}</p>
    </div>

    {#if form?.success}
        <div class="alert success">{form.message}</div>
    {/if}
    {#if form?.error}
        <div class="alert error">{form.error}</div>
    {/if}

    <!-- Create New Category -->
    <div class="card create-card">
        <h2>{t(lang, "admin.categories.new")}</h2>
        <form method="POST" action="?/create" use:enhance>
            <div class="inline-form">
                <input
                    type="text"
                    name="name"
                    bind:value={newCategoryName}
                    placeholder="Nome da categoria..."
                    required
                    minlength="2"
                />
                <button type="submit" class="btn btn-primary">{t(lang, "admin.ui.create")}</button>
            </div>
        </form>
    </div>

    <!-- Categories List -->
    <div class="card">
        <h2>Todas as {t(lang, "admin.categories.heading")} ({data.categories.length})</h2>

        {#if data.categories.length === 0}
            <div class="empty-state">
                <p>Nenhuma categoria cadastrada.</p>
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
                                <input
                                    type="text"
                                    name="name"
                                    bind:value={editingName}
                                    required
                                    minlength="2"
                                    class="edit-input"
                                />
                                <label class="checkbox-label">
                                    <input
                                        type="checkbox"
                                        name="pinterest_enabled"
                                        checked={!!category.pinterest_enabled}
                                    />
                                    <span>Pinterest Feed</span>
                                </label>
                                <div class="edit-actions">
                                    <button
                                        type="submit"
                                        class="btn btn-small btn-primary"
                                        >{t(lang, "admin.ui.save")}</button
                                    >
                                    <button
                                        type="button"
                                        class="btn btn-small"
                                        onclick={cancelEdit}>{t(lang, "admin.ui.cancel")}</button
                                    >
                                </div>
                            </form>
                        {:else}
                            <div class="category-info">
                                <span class="category-name"
                                    >{category.name}</span
                                >
                                <span class="category-slug"
                                    >/{category.slug}</span
                                >
                                {#if category.pinterest_enabled}
                                <span class="pinterest-badge" title="Feed do Pinterest habilitado">
                                    <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14" style="color: #e60023">
                                        <path d="M9.04 14.63c-.35 1.89-.78 3.7-2.06 4.65-.39-2.79.58-4.87 1.03-7.09-1.73-2.9 1.5-5.87 3.37-2.79 2.34 3.69-2.03 7.14.91 8.01 3.07.91 4.33-3.94 2.42-5.36-2.76-1.97-8.02-.45-6.97 4.42.27 1.22 1.41 1.59.49 2.28-.73.53-1.97-.17-2.3-1.21-.79-2.57.28-5.35 1.68-7.11 1.4-1.76 3.5-2.01 5.43-1.99 3.29.03 6.38 1.48 6.81 5.26.49 4.28-1.82 8.98-6.12 8.66-1.17-.08-1.99-.64-2.16-1.73zM10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0z"/>
                                    </svg>
                                </span>
                                {/if}
                            </div>
                            <div class="category-actions">
                                <button
                                    type="button"
                                    class="btn btn-small"
                                    onclick={() =>
                                        startEdit(category.id, category.name)}
                                    >{t(lang, "admin.ui.edit")}</button
                                >
                                <form
                                    method="POST"
                                    action="?/delete"
                                    use:enhance
                                    style="display:inline;"
                                >
                                    <input
                                        type="hidden"
                                        name="id"
                                        value={category.id}
                                    />
                                    <button
                                        type="submit"
                                        class="btn btn-small btn-danger"
                                        onclick={confirmDelete}>{t(lang, "admin.ui.delete")}</button
                                    >
                                </form>
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>

<style>
    .categories-page {
        max-width: 800px;
        margin: 0 auto;
    }

    .page-header {
        margin-bottom: 2rem;
    }

    h1 {
        font-family: var(--font-sans);
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        color: var(--text-muted);
        font-family: var(--font-sans);
    }

    h2 {
        font-family: var(--font-sans);
        font-size: 0.8125rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-secondary);
        margin-bottom: 1rem;
    }

    .card {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .inline-form {
        display: flex;
        gap: 0.75rem;
    }

    .inline-form input {
        flex: 1;
        padding: 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        font-family: var(--font-sans);
        transition: border-color var(--transition-fast);
    }

    .inline-form input:focus {
        outline: none;
        border-color: var(--text-primary);
    }

    .categories-list {
        display: flex;
        flex-direction: column;
    }

    .category-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid var(--border-light);
    }

    .category-item:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }

    .category-item:first-child {
        padding-top: 0;
    }

    .category-info {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .category-name {
        font-family: var(--font-sans);
        font-size: 1rem;
        color: var(--text-primary);
        font-weight: 500;
    }

    .category-slug {
        font-family: "Monaco", "Consolas", monospace;
        font-size: 0.75rem;
        color: var(--text-muted);
        background: var(--bg-tertiary);
        padding: 0.25rem 0.5rem;
        border-radius: var(--radius-sm);
    }

    .category-actions {
        display: flex;
        gap: 0.5rem;
    }

    .edit-form {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .edit-input {
        flex: 1;
        padding: 0.5rem 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        font-family: var(--font-sans);
    }

    .edit-input:focus {
        outline: none;
        border-color: var(--text-primary);
    }

    .edit-actions {
        display: flex;
        gap: 0.5rem;
    }

    .btn-danger {
        border-color: #dc2626;
        color: #dc2626;
    }

    .btn-danger:hover {
        background: #dc2626;
        color: white;
    }

    .alert {
        padding: 1rem;
        border-radius: var(--radius-md);
        margin-bottom: 1.5rem;
        font-family: var(--font-sans);
    }

    .success {
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #a7f3d0;
    }

    .error {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
    }

    .empty-state {
        text-align: center;
        padding: 2rem;
        color: var(--text-muted);
        font-family: var(--font-sans);
    }

    .checkbox-label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-family: var(--font-sans);
        font-size: 0.875rem;
        color: var(--text-secondary);
        cursor: pointer;
        white-space: nowrap;
    }

    .checkbox-label input[type="checkbox"] {
        cursor: pointer;
    }

    .pinterest-badge {
        display: inline-flex;
        align-items: center;
        cursor: help;
    }

    @media (max-width: 640px) {
        .inline-form {
            flex-direction: column;
        }

        .category-item {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.75rem;
        }

        .edit-form {
            flex-direction: column;
        }
    }
</style>
