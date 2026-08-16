<script lang="ts">
  import { Breadcrumb } from '$lib/components';
  import { page } from '$app/stores';
  import { t, formatDate } from '$lib/i18n';
  let { data } = $props();
  const lang = $derived($page.data.language || data?.settings?.site_language || 'pt');
</script>

<svelte:head>
  <title>{data.settings?.site_title || "Blog"} | {t(lang, 'legal.privacy_title')}</title>
</svelte:head>

<div class="privacy-page">
  <div class="container">
    <Breadcrumb items={[
      { label: t(lang, 'legal.privacy_crumb') }
    ]} />

    <article class="content">
      <h1>{t(lang, 'legal.privacy_title')}</h1>
      <p><strong>{t(lang, 'common.last_updated')}</strong> {formatDate(lang, new Date())}</p>
      <h2>{t(lang, 'legal.privacy.s1_t')}</h2>
      <p>{t(lang, 'legal.privacy.s1_p')}</p>
      <h2>{t(lang, 'legal.privacy.s2_t')}</h2>
      <h3>{t(lang, 'legal.privacy.s2_h1')}</h3>
      <ul>
        <li>{t(lang, 'legal.privacy.s2_i1')}</li>
        <li>{t(lang, 'legal.privacy.s2_i2')}</li>
        <li>{t(lang, 'legal.privacy.s2_i3')}</li>
      </ul>
      <h3>{t(lang, 'legal.privacy.s2_h2')}</h3>
      <ul>
        <li>{t(lang, 'legal.privacy.s2_n1')}</li>
        <li>{t(lang, 'legal.privacy.s2_n2')}</li>
        <li>{t(lang, 'legal.privacy.s2_n3')}</li>
      </ul>
      <h2>{t(lang, 'legal.privacy.s3_t')}</h2>
      <p>{t(lang, 'legal.privacy.s3_p')}</p>
      <ul>
        <li>{t(lang, 'legal.privacy.s3_i1')}</li>
        <li>{t(lang, 'legal.privacy.s3_i2')}</li>
        <li>{t(lang, 'legal.privacy.s3_i3')}</li>
        <li>{t(lang, 'legal.privacy.s3_i4')}</li>
      </ul>
      <h2>{t(lang, 'legal.privacy.s4_t')}</h2>
      <p>{t(lang, 'legal.privacy.s4_p')}</p>
      <ul>
        <li>{t(lang, 'legal.privacy.s4_i1')}</li>
        <li>{t(lang, 'legal.privacy.s4_i2')}</li>
        <li>{t(lang, 'legal.privacy.s4_i3')}</li>
      </ul>
      <p>{t(lang, 'legal.privacy.s4_note')}</p>
      <h2>{t(lang, 'legal.privacy.s5_t')}</h2>
      <p>{t(lang, 'legal.privacy.s5_p')}</p>
      <ul>
        <li>{t(lang, 'legal.privacy.s5_i1')}</li>
        <li>{t(lang, 'legal.privacy.s5_i2')}</li>
        <li>{t(lang, 'legal.privacy.s5_i3')}</li>
      </ul>
      <h2>{t(lang, 'legal.privacy.s6_t')}</h2>
      <p>{t(lang, 'legal.privacy.s6_p')}</p>
      <h2>{t(lang, 'legal.privacy.s7_t')}</h2>
      <p>{t(lang, 'legal.privacy.s7_p')}</p>
      <ul>
        <li>{t(lang, 'legal.privacy.s7_i1')}</li>
        <li>{t(lang, 'legal.privacy.s7_i2')}</li>
        <li>{t(lang, 'legal.privacy.s7_i3')}</li>
        <li>{t(lang, 'legal.privacy.s7_i4')}</li>
      </ul>
      <h2>{t(lang, 'legal.privacy.s8_t')}</h2>
      <p>{t(lang, 'legal.privacy.s8_p')}</p>
      <h2>{t(lang, 'legal.privacy.s9_t')}</h2>
      <p>{t(lang, 'legal.privacy.s9_p')}</p>
      <h2>{t(lang, 'legal.privacy.s10_t')}</h2>
      <p>{t(lang, 'legal.privacy.s10_p')}</p>
      <h2>{t(lang, 'legal.privacy.s11_t')}</h2>
      <p>{t(lang, 'legal.privacy.s11_p')}</p>

    </article>
  </div>
</div>

<style>
  .privacy-page {
    min-height: calc(100vh - 200px);
    padding: 3rem 0 6rem;
  }
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 20px;
  }
  .content {
    background: var(--bg-primary);
    padding: 4rem;
    border-radius: 24px;
    border: 1px solid var(--border-light);
    box-shadow: var(--shadow-md);
    margin-top: 1rem;
  }
  .content h1 {
    font-family: var(--font-serif);
    font-size: clamp(2.5rem, 5vw, 3.5rem);
    font-weight: 600;
    line-height: 1.15;
    color: var(--text-primary);
    margin: 0 0 1rem;
  }
  .content > p:first-of-type {
    font-size: 0.9rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 3rem;
    border-bottom: 1px solid var(--border-light);
    padding-bottom: 1.5rem;
  }
  .content h2 {
    font-size: 1.35rem;
    margin: 2rem 0 0.75rem;
    color: var(--text-primary);
  }
  .content h3 {
    font-size: 1.05rem;
    margin: 1.25rem 0 0.5rem;
  }
  .content p, .content li {
    color: var(--text-secondary);
    line-height: 1.7;
  }
  .content ul {
    padding-left: 1.25rem;
  }
  @media (max-width: 640px) {
    .content { padding: 1.5rem; }
  }
</style>
