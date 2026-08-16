<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, scale } from 'svelte/transition';
    import { page } from '$app/stores';
    import { t } from '$lib/i18n';
    import { ageState, confirmAgeGlobal } from '$lib/stores/age.svelte';

    let { is18Plus = false } = $props();
    let showModal = $state(false);
    const lang = $derived($page.data.language || 'pt');

    onMount(() => {
        if (is18Plus && !ageState.confirmed) {
            showModal = true;
            document.body.style.overflow = 'hidden';
        }
    });

    function confirmAge() {
        confirmAgeGlobal();
        showModal = false;
        document.body.style.overflow = '';
    }

    function goBack() {
        window.history.back();
    }
</script>

{#if showModal}
    <div class="age-verification-overlay" transition:fade={{ duration: 300 }}>
        <div class="modal-content" in:scale={{ duration: 400, start: 0.95 }}>
            <div class="warning-icon">18+</div>
            <h2>{t(lang, 'age.title')}</h2>
            <p>{t(lang, 'age.body')}</p>
            
            <div class="actions">
                <button class="btn-confirm" onclick={confirmAge}>
                    {t(lang, 'age.confirm')}
                </button>
                <button class="btn-cancel" onclick={goBack}>
                    {t(lang, 'age.cancel')}
                </button>
            </div>
            
            <p class="footer-note">
                {t(lang, 'age.note')}
            </p>
        </div>
    </div>
{/if}

<style>
    .age-verification-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(12px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    }

    .modal-content {
        background: var(--bg-primary);
        max-width: 500px;
        width: 100%;
        padding: 3rem;
        border-radius: 32px;
        text-align: center;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        border: 1px solid var(--border-light);
    }

    .warning-icon {
        width: 80px;
        height: 80px;
        background: #ff4757;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 auto 2rem;
        box-shadow: 0 8px 16px rgba(255, 71, 87, 0.3);
    }

    h2 {
        font-family: var(--font-serif);
        font-size: 2rem;
        margin-bottom: 1.5rem;
        color: var(--text-primary);
    }

    p {
        color: var(--text-secondary);
        line-height: 1.6;
        margin-bottom: 2.5rem;
        font-size: 1.05rem;
    }

    .actions {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .btn-confirm {
        background: var(--text-primary);
        color: var(--bg-primary);
        border: none;
        padding: 1.25rem;
        border-radius: 16px;
        font-weight: 700;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
    }

    .btn-confirm:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        filter: brightness(1.1);
    }

    .btn-cancel {
        background: transparent;
        color: var(--text-secondary);
        border: 1px solid var(--border-light);
        padding: 1rem;
        border-radius: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .btn-cancel:hover {
        background: var(--bg-secondary);
        color: var(--text-primary);
    }

    .footer-note {
        margin-top: 2rem;
        margin-bottom: 0;
        font-size: 0.85rem;
        opacity: 0.6;
    }

    @media (max-width: 640px) {
        .modal-content {
            padding: 2rem;
        }
    }
</style>
