<script lang="ts">
  import { page } from "$app/stores";
  import { t, formatMoney, adminErrorMessage } from "$lib/i18n";
  import { enhance } from "$app/forms";

  let { form } = $props();
  const lang = $derived($page.data.language || 'pt');
  const formError = $derived(adminErrorMessage(lang, form?.message || form?.error));

  let priceValue = $state('');
  let intervalDays = $state('30');
  let priceCents = $state(0);

  function formatPrice(cents: number) {
    return formatMoney(lang, cents || 0);
  }

  function generateSlug(name: string) {
    return name.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/[\s_]+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  }

  function handleNameInput(e: Event) {
    const input = e.target as HTMLInputElement;
    const slugInput = document.getElementById('slug') as HTMLInputElement;
    if (slugInput && !slugInput.dataset.touched) {
      slugInput.value = generateSlug(input.value);
    }
  }

  function handleSlugInput() {
    const slugInput = document.getElementById('slug') as HTMLInputElement;
    if (slugInput) slugInput.dataset.touched = '1';
  }

  /** Digits only → treat as BRL cents (e.g. 1990 → R$ 19,90) */
  function parsePriceToCents(value: string) {
    const cleaned = value.replace(/[^0-9]/g, '');
    return parseInt(cleaned || '0', 10);
  }
</script>

<svelte:head>
  <title>{t(lang, "admin.premium.create_title")}</title>
</svelte:head>

<div class="new-plan-page">
  <div class="page-header">
    <h1>{t(lang, "admin.premium.create_title")}</h1>
    <p class="subtitle">{t(lang, "admin.premium.create_subtitle")}</p>
  </div>

  <form method="POST" use:enhance class="plan-form">
    <div class="form-section">
      <div class="form-group">
        <label for="name">{t(lang, "admin.premium.plan_name")}</label>
        <input
          type="text"
          id="name"
          name="name"
          placeholder={t(lang, "admin.premium.name_placeholder")}
          required
          oninput={handleNameInput}
        />
      </div>

      <div class="form-group">
        <label for="slug">{t(lang, "admin.premium.slug_label")}</label>
        <input
          type="text"
          id="slug"
          name="slug"
          placeholder={t(lang, "admin.premium.slug_placeholder")}
          required
          oninput={handleSlugInput}
        />
        <small>{t(lang, "admin.premium.slug_hint")}</small>
      </div>

      <div class="form-group">
        <label for="description">{t(lang, "admin.ui.description")}</label>
        <textarea
          id="description"
          name="description"
          rows="2"
          placeholder={t(lang, "admin.premium.description_placeholder")}
        ></textarea>
      </div>
    </div>

    <div class="section-divider"></div>

    <div class="form-section">
      <div class="form-row">
        <div class="form-group">
          <label for="price_cents">{t(lang, "admin.premium.price_cents")}</label>
          <div class="price-input-group">
            <input
              type="text"
              id="price_cents"
              name="price_cents_display"
              placeholder={t(lang, "admin.premium.price_placeholder")}
              value={priceValue}
              oninput={(e) => {
                const raw = (e.target as HTMLInputElement).value;
                priceValue = raw;
                priceCents = parsePriceToCents(raw);
              }}
            />
            <span class="input-suffix">{t(lang, "admin.premium.currency_suffix")}</span>
          </div>
          <input type="hidden" name="price_cents" value={priceCents} />
          {#if priceCents > 0}
            <small>{t(lang, "admin.premium.price_value", { price: formatPrice(priceCents) })}</small>
          {/if}
        </div>

        <div class="form-group">
          <label for="interval_days">{t(lang, "admin.premium.billing_cycle")}</label>
          <select id="interval_days" name="interval_days" bind:value={intervalDays}>
            <option value="30">{t(lang, "admin.premium.interval_monthly")}</option>
            <option value="90">{t(lang, "admin.premium.interval_quarterly")}</option>
            <option value="180">{t(lang, "admin.premium.interval_semiannual")}</option>
            <option value="365">{t(lang, "admin.premium.interval_yearly")}</option>
          </select>
        </div>
      </div>
    </div>

    <div class="section-divider"></div>

    <div class="form-section">
      <div class="form-group">
        <label for="features">{t(lang, "admin.premium.features")}</label>
        <textarea
          id="features"
          name="features"
          rows="6"
          placeholder={t(lang, "admin.premium.features_placeholder")}
        ></textarea>
      </div>
    </div>

    <div class="form-section">
      <label class="checkbox-label">
        <input type="checkbox" name="is_active" checked />
        <span>{t(lang, "admin.premium.plan_active")}</span>
      </label>
    </div>

    {#if formError}
      <div class="alert error">{formError}</div>
    {/if}

    <div class="form-actions">
      <a href="/admin/premium/plans" class="btn">{t(lang, "admin.ui.cancel")}</a>
      <button type="submit" class="btn btn-primary">{t(lang, "admin.premium.create_plan")}</button>
    </div>
  </form>
</div>

<style>
  .new-plan-page { max-width: 700px; margin: 0 auto; }
  .page-header { margin-bottom: 2rem; }
  h1 { font-family: var(--font-sans); font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
  .subtitle { color: var(--text-muted); }

  .plan-form { background: var(--bg-primary); padding: 2rem; border-radius: var(--radius-lg); border: 1px solid var(--border-color); }
  .form-section { display: flex; flex-direction: column; gap: 1.5rem; }
  .form-group { display: flex; flex-direction: column; gap: 0.5rem; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }

  label { font-weight: 500; color: var(--text-primary); font-size: 0.875rem; }
  input[type="text"], select, textarea {
    width: 100%; padding: 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-sans);
  }
  input:focus, select:focus, textarea:focus { outline: none; border-color: var(--text-primary); }

  .price-input-group { position: relative; display: flex; align-items: center; }
  .price-input-group input { padding-left: 2.5rem; }
  .input-suffix { position: absolute; left: 0.75rem; color: var(--text-muted); font-weight: 500; }

  .checkbox-label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-weight: 600; }
  input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--text-primary); }

  .section-divider { height: 1px; background: var(--border-light); margin: 1.5rem 0; }
  .form-actions { margin-top: 2rem; display: flex; justify-content: flex-end; gap: 1rem; }
  .alert { padding: 1rem; border-radius: var(--radius-md); margin-bottom: 1.5rem; font-size: 0.875rem; }
  .error { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
  small { color: var(--text-muted); font-size: 0.75rem; }

  @media (max-width: 640px) {
    .form-row { grid-template-columns: 1fr; }
  }
</style>
