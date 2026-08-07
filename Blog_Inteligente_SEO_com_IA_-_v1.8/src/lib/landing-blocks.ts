/**
 * Landing page block factories & conversion templates.
 * Used by the visual builder and the public renderer.
 * User-facing copy goes through i18n (pt/en/es) via site/admin language.
 */
import { t } from '$lib/i18n';

export type Block = {
  id: string;
  type: string;
  content?: string;
  styles?: Record<string, string>;
  properties?: Record<string, any>;
  children?: Block[];
};

export function uid(prefix = 'b'): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

const baseStyles = () => ({
  marginTop: '0px',
  marginBottom: '12px',
  paddingTop: '0px',
  paddingBottom: '0px',
  textAlign: 'left'
});

/** Premium Lucide Outline-style SVGs (language-agnostic) */
export const LP_SVG = {
  edit: `<svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle;"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`,
  device: `<svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle;"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>`,
  chart: `<svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 28px; height: 28px; display: inline-block; vertical-align: middle;"><path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/></svg>`
};

function L(lang: string, key: string, vars?: Record<string, string | number>) {
  return t(lang, `admin.landing_pages.builder.${key}`, vars);
}

/** Create a primitive or structural block by type */
export function createBlock(type: string, lang: string = 'pt'): Block {
  const id = uid(type);
  const styles = baseStyles();

  switch (type) {
    case 'section':
      return {
        id,
        type: 'section',
        styles: {
          ...styles,
          paddingTop: '48px',
          paddingBottom: '48px',
          backgroundColor: '#ffffff',
          textColor: '#111827',
          textAlign: 'left'
        },
        properties: {},
        children: []
      };

    case 'container':
      return {
        id,
        type: 'container',
        styles: { ...styles, paddingTop: '8px', paddingBottom: '8px' },
        properties: {},
        children: []
      };

    case 'columns':
    case 'columns-2':
      return createColumns(2, lang);

    case 'columns-3':
      return createColumns(3, lang);

    case 'text':
      return {
        id,
        type: 'text',
        content: `<p>${L(lang, 'default_text_para')}</p>`,
        styles: { ...styles, fontSize: '1rem', textColor: '#111827' },
        properties: {}
      };

    case 'image':
      return {
        id,
        type: 'image',
        styles: { ...styles, borderRadius: '12px' },
        properties: {
          src: 'https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg',
          alt: L(lang, 'default_image_alt')
        }
      };

    case 'button':
      return {
        id,
        type: 'button',
        content: L(lang, 'default_button'),
        styles: {
          ...styles,
          backgroundColor: '#111827',
          textColor: '#ffffff',
          paddingTop: '12px',
          paddingBottom: '12px',
          borderRadius: '8px',
          fontSize: '0.875rem',
          textAlign: 'center'
        },
        properties: { href: '#', productId: null, productSlug: null }
      };

    case 'video':
      return {
        id,
        type: 'video',
        styles: { ...styles },
        properties: { src: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' }
      };

    case 'divider':
      return {
        id,
        type: 'divider',
        styles: {
          ...styles,
          paddingTop: '10px',
          paddingBottom: '10px',
          borderColor: '#e5e7eb',
          borderWidth: '1px',
          borderStyle: 'solid'
        },
        properties: {}
      };

    case 'spacer':
      return {
        id,
        type: 'spacer',
        styles: { ...styles, paddingTop: '32px' },
        properties: {}
      };

    case 'html':
      return {
        id,
        type: 'html',
        content: `<div style="padding:1rem;border:1px dashed #d1d5db;border-radius:8px;"><strong>${L(lang, 'default_html')}</strong></div>`,
        styles: { ...styles },
        properties: {}
      };

    case 'newsletter':
      return {
        id,
        type: 'newsletter',
        content: L(lang, 'newsletter_default_title'),
        styles: { ...styles, textAlign: 'center' },
        properties: {
          title: L(lang, 'newsletter_default_title'),
          description: L(lang, 'newsletter_default_desc'),
          placeholder: L(lang, 'newsletter_default_placeholder'),
          buttonText: L(lang, 'newsletter_default_button')
        }
      };

    case 'cta':
      return createCtaBlock(lang);

    case 'testimonial':
      return createTestimonialBlock(lang);

    case 'pricing':
      return createPricingBlock(false, lang);

    case 'faq':
      return createFaqBlock(lang);

    default:
      return {
        id,
        type: 'text',
        content: `<p>${L(lang, 'default_block_type', { type })}</p>`,
        styles: { ...styles },
        properties: {}
      };
  }
}

export function createColumns(count: 2 | 3 = 2, lang: string = 'pt'): Block {
  const cols: Block[] = [];
  for (let i = 0; i < count; i++) {
    cols.push({
      id: uid('col'),
      type: 'column',
      styles: { paddingTop: '8px', paddingBottom: '8px' },
      properties: {},
      children: [
        {
          id: uid('text'),
          type: 'text',
          content: `<p style="color:#6b7280;">${L(lang, 'column_placeholder', { n: i + 1 })}</p>`,
          styles: { fontSize: '0.95rem', textColor: '#6b7280', marginBottom: '0px' },
          properties: {}
        }
      ]
    });
  }
  return {
    id: uid('columns'),
    type: 'columns',
    styles: {
      marginTop: '0px',
      marginBottom: '16px',
      paddingTop: '0px',
      paddingBottom: '0px'
    },
    properties: { cols: count, gap: '1.5rem' },
    children: cols
  };
}

export function createCtaBlock(lang: string = 'pt'): Block {
  return {
    id: uid('cta'),
    type: 'cta',
    content: L(lang, 'cta_title'),
    styles: {
      paddingTop: '48px',
      paddingBottom: '48px',
      backgroundColor: '#111827',
      textColor: '#ffffff',
      textAlign: 'center',
      borderRadius: '16px',
      marginBottom: '16px'
    },
    properties: {
      subtitle: L(lang, 'cta_subtitle'),
      buttonText: L(lang, 'cta_button'),
      buttonHref: '#',
      buttonBg: '#22c55e',
      buttonColor: '#052e16',
      productId: null,
      productSlug: null
    }
  };
}

export function createTestimonialBlock(lang: string = 'pt'): Block {
  return {
    id: uid('testimonial'),
    type: 'testimonial',
    styles: {
      paddingTop: '24px',
      paddingBottom: '24px',
      backgroundColor: '#f9fafb',
      textColor: '#111827',
      textAlign: 'left',
      borderRadius: '16px',
      marginBottom: '16px'
    },
    properties: {
      quote: L(lang, 'testimonial_quote'),
      author: L(lang, 'testimonial_author'),
      role: L(lang, 'testimonial_role'),
      avatar: '',
      rating: 5
    }
  };
}

export function createPricingBlock(featured = false, lang: string = 'pt'): Block {
  return {
    id: uid('pricing'),
    type: 'pricing',
    styles: {
      paddingTop: '24px',
      paddingBottom: '24px',
      backgroundColor: featured ? '#111827' : '#ffffff',
      textColor: featured ? '#ffffff' : '#111827',
      borderRadius: '16px',
      marginBottom: '16px',
      textAlign: 'center'
    },
    properties: {
      name: featured ? L(lang, 'plan_pro') : L(lang, 'plan_essential'),
      price: featured ? L(lang, 'plan_pro_price') : L(lang, 'plan_essential_price'),
      period: L(lang, 'plan_period'),
      features: featured
        ? [L(lang, 'plan_pro_f1'), L(lang, 'plan_pro_f2'), L(lang, 'plan_pro_f3'), L(lang, 'plan_pro_f4')]
        : [L(lang, 'plan_ess_f1'), L(lang, 'plan_ess_f2'), L(lang, 'plan_ess_f3')],
      buttonText: L(lang, 'plan_subscribe'),
      buttonHref: '#',
      featured,
      productId: null,
      productSlug: null
    }
  };
}

export function createFaqBlock(lang: string = 'pt'): Block {
  return {
    id: uid('faq'),
    type: 'faq',
    styles: {
      paddingTop: '16px',
      paddingBottom: '16px',
      marginBottom: '16px',
      textAlign: 'left'
    },
    properties: {
      title: L(lang, 'faq_title'),
      items: [
        { q: L(lang, 'faq_q1'), a: L(lang, 'faq_a1') },
        { q: L(lang, 'faq_q2'), a: L(lang, 'faq_a2') },
        { q: L(lang, 'faq_q3'), a: L(lang, 'faq_a3') }
      ]
    }
  };
}

/** Full-section conversion templates (inserted as sections) */
export function createTemplate(
  name: 'cta_section' | 'testimonials' | 'pricing' | 'faq_section' | 'product_cta',
  lang: string = 'pt'
): Block {
  if (name === 'cta_section') {
    const sec = createBlock('section', lang) as Block;
    sec.styles = {
      paddingTop: '64px',
      paddingBottom: '64px',
      backgroundColor: '#0f172a',
      textColor: '#fff',
      textAlign: 'center'
    };
    sec.children = [createCtaBlock(lang)];
    sec.children[0].styles = {
      ...sec.children[0].styles,
      backgroundColor: 'transparent',
      marginBottom: '0px'
    };
    return sec;
  }

  if (name === 'testimonials') {
    const sec = createBlock('section', lang) as Block;
    sec.styles = {
      paddingTop: '56px',
      paddingBottom: '56px',
      backgroundColor: '#ffffff',
      textAlign: 'center'
    };
    const title: Block = {
      id: uid('text'),
      type: 'text',
      content: `<h2 style="font-size:1.75rem;font-weight:800;margin:0 0 0.5rem;">${L(lang, 'tpl_testimonials_title')}</h2>`,
      styles: { fontSize: '1.75rem', textAlign: 'center', marginBottom: '8px' },
      properties: {}
    };
    const cols = createColumns(3, lang);
    cols.children = [createTestimonialBlock(lang), createTestimonialBlock(lang), createTestimonialBlock(lang)].map(
      (item, i) => ({
        id: uid('col'),
        type: 'column',
        styles: {},
        properties: {},
        children: [
          {
            ...item,
            properties: {
              ...item.properties,
              author: [L(lang, 'tpl_t1_author'), L(lang, 'tpl_t2_author'), L(lang, 'tpl_t3_author')][i],
              role: [L(lang, 'tpl_t1_role'), L(lang, 'tpl_t2_role'), L(lang, 'tpl_t3_role')][i],
              quote: [L(lang, 'tpl_t1_quote'), L(lang, 'tpl_t2_quote'), L(lang, 'tpl_t3_quote')][i]
            }
          }
        ]
      })
    );
    sec.children = [title, cols];
    return sec;
  }

  if (name === 'pricing') {
    const sec = createBlock('section', lang) as Block;
    sec.styles = {
      paddingTop: '56px',
      paddingBottom: '56px',
      backgroundColor: '#f8fafc',
      textAlign: 'center'
    };
    const title: Block = {
      id: uid('text'),
      type: 'text',
      content: `<h2 style="font-size:1.75rem;font-weight:800;margin:0 0 0.35rem;">${L(lang, 'tpl_pricing_title')}</h2><p style="color:#64748b;margin:0 0 1.5rem;">${L(lang, 'tpl_pricing_sub')}</p>`,
      styles: { textAlign: 'center', marginBottom: '24px' },
      properties: {}
    };
    const cols = createColumns(3, lang);
    cols.children = [
      createPricingBlock(false, lang),
      createPricingBlock(true, lang),
      createPricingBlock(false, lang)
    ].map((p, i) => {
      const names = [L(lang, 'tpl_plan_starter'), L(lang, 'tpl_plan_pro'), L(lang, 'tpl_plan_biz')];
      const prices = [L(lang, 'tpl_price_starter'), L(lang, 'tpl_price_pro'), L(lang, 'tpl_price_biz')];
      return {
        id: uid('col'),
        type: 'column',
        styles: {},
        properties: {},
        children: [
          {
            ...p,
            properties: {
              ...p.properties,
              name: names[i],
              price: prices[i],
              featured: i === 1,
              features:
                i === 0
                  ? [L(lang, 'tpl_s_f1'), L(lang, 'tpl_s_f2'), L(lang, 'tpl_s_f3')]
                  : i === 1
                    ? [L(lang, 'tpl_p_f1'), L(lang, 'tpl_p_f2'), L(lang, 'tpl_p_f3'), L(lang, 'tpl_p_f4')]
                    : [L(lang, 'tpl_b_f1'), L(lang, 'tpl_b_f2'), L(lang, 'tpl_b_f3'), L(lang, 'tpl_b_f4')]
            },
            styles: {
              ...p.styles,
              backgroundColor: i === 1 ? '#111827' : '#ffffff',
              textColor: i === 1 ? '#ffffff' : '#111827'
            }
          }
        ]
      };
    });
    sec.children = [title, cols];
    return sec;
  }

  if (name === 'faq_section') {
    const sec = createBlock('section', lang) as Block;
    sec.styles = {
      paddingTop: '56px',
      paddingBottom: '56px',
      backgroundColor: '#ffffff',
      textAlign: 'left'
    };
    sec.children = [createFaqBlock(lang)];
    return sec;
  }

  // product_cta
  const sec = createBlock('section', lang) as Block;
  sec.styles = {
    paddingTop: '48px',
    paddingBottom: '48px',
    backgroundColor: '#ecfdf5',
    textAlign: 'center'
  };
  const cta = createCtaBlock(lang);
  cta.styles = {
    ...cta.styles,
    backgroundColor: 'transparent',
    textColor: '#064e3b',
    marginBottom: '0'
  };
  cta.content = L(lang, 'product_cta_title');
  cta.properties = {
    ...cta.properties,
    subtitle: L(lang, 'product_cta_sub'),
    buttonText: L(lang, 'product_cta_button'),
    buttonHref: '/products',
    buttonBg: '#059669',
    buttonColor: '#ffffff'
  };
  sec.children = [cta];
  return sec;
}

/** Default starter content for a brand-new landing page (empty content) */
export function getDefaultLandingBlocks(lang: string = 'pt'): Block[] {
  const card = (svg: string, title: string, body: string) =>
    `<div style="background: #ffffff; border: 1px solid #e5e7eb; padding: 2rem; border-radius: 12px; display: inline-block; width: 100%; max-width: 280px; margin: 10px; text-align: left; box-shadow: 0 1px 3px rgba(0,0,0,0.02); box-sizing: border-box; vertical-align: top;"><span style="display: block; margin-bottom: 1rem;">${svg}</span><h3 style="font-size: 1.125rem; font-weight: 700; margin-bottom: 0.5rem;">${title}</h3><p style="font-size: 0.875rem; color: #6b7280; line-height: 1.5; margin: 0;">${body}</p></div>`;

  return [
    {
      id: 'sec-hero',
      type: 'section',
      styles: {
        paddingTop: '80px',
        paddingBottom: '80px',
        backgroundColor: '#ffffff',
        textColor: '#111827',
        textAlign: 'left'
      },
      properties: {},
      children: [
        {
          id: 'hero-grid',
          type: 'container',
          styles: {
            marginTop: '0px',
            marginBottom: '0px',
            paddingTop: '0px',
            paddingBottom: '0px'
          },
          properties: {},
          children: [
            {
              id: 'hero-title',
              type: 'text',
              content: `<h1 style="font-size: 3.25rem; font-weight: 800; line-height: 1.15; letter-spacing: -0.02em; margin-bottom: 1.5rem;">${L(lang, 'starter_hero_title')}</h1>`,
              styles: { fontSize: '3rem', marginBottom: '24px', textColor: '#111827' },
              properties: {}
            },
            {
              id: 'hero-desc',
              type: 'text',
              content: `<p style="font-size: 1.125rem; color: #4b5563; line-height: 1.6; margin-bottom: 2rem; max-width: 550px;">${L(lang, 'starter_hero_desc')}</p>`,
              styles: { fontSize: '1.125rem', marginBottom: '32px', textColor: '#4b5563' },
              properties: {}
            },
            {
              id: 'hero-buttons-container',
              type: 'container',
              styles: {
                marginTop: '0px',
                marginBottom: '0px',
                paddingTop: '0px',
                paddingBottom: '0px'
              },
              properties: {},
              children: [
                {
                  id: 'hero-btn-1',
                  type: 'button',
                  content: L(lang, 'starter_btn_primary'),
                  styles: {
                    backgroundColor: '#111827',
                    textColor: '#ffffff',
                    paddingTop: '12px',
                    paddingBottom: '12px',
                    borderRadius: '8px',
                    fontSize: '0.875rem'
                  },
                  properties: { href: '#' }
                },
                {
                  id: 'hero-btn-2',
                  type: 'button',
                  content: L(lang, 'starter_btn_secondary'),
                  styles: {
                    backgroundColor: '#ffffff',
                    textColor: '#111827',
                    paddingTop: '12px',
                    paddingBottom: '12px',
                    borderRadius: '8px',
                    fontSize: '0.875rem',
                    borderWidth: '1px',
                    borderStyle: 'solid',
                    borderColor: '#e5e7eb',
                    marginLeft: '12px'
                  },
                  properties: { href: '#' }
                }
              ]
            }
          ]
        }
      ]
    },
    {
      id: 'sec-features',
      type: 'section',
      styles: {
        paddingTop: '60px',
        paddingBottom: '60px',
        backgroundColor: '#f9fafb',
        textColor: '#111827',
        textAlign: 'center'
      },
      properties: {},
      children: [
        {
          id: 'feat-title',
          type: 'text',
          content: `<h2 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;">${L(lang, 'starter_feat_title')}</h2>`,
          styles: { fontSize: '2rem', marginBottom: '8px', textColor: '#111827', textAlign: 'center' },
          properties: {}
        },
        {
          id: 'feat-desc',
          type: 'text',
          content: `<p style="color: #6b7280; margin-bottom: 3rem;">${L(lang, 'starter_feat_desc')}</p>`,
          styles: { fontSize: '1rem', marginBottom: '40px', textColor: '#6b7280', textAlign: 'center' },
          properties: {}
        },
        {
          id: 'feat-cards-container',
          type: 'container',
          styles: {
            marginTop: '0px',
            marginBottom: '0px',
            paddingTop: '0px',
            paddingBottom: '0px',
            textAlign: 'center'
          },
          properties: {},
          children: [
            {
              id: 'feat-card-1',
              type: 'text',
              content:
                card(LP_SVG.edit, L(lang, 'starter_card1_title'), L(lang, 'starter_card1_body')) +
                card(LP_SVG.device, L(lang, 'starter_card2_title'), L(lang, 'starter_card2_body')) +
                card(LP_SVG.chart, L(lang, 'starter_card3_title'), L(lang, 'starter_card3_body')),
              styles: { fontSize: '1rem', textColor: '#111827', textAlign: 'center' },
              properties: {}
            }
          ]
        }
      ]
    }
  ];
}

export function youtubeId(url: string | undefined | null): string | null {
  if (!url) return null;
  if (/^[\w-]{11}$/.test(url.trim())) return url.trim();
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/|youtube\.com\/v\/)([\w-]{11})/,
    /[?&]v=([\w-]{11})/
  ];
  for (const re of patterns) {
    const m = url.match(re);
    if (m?.[1]) return m[1];
  }
  return null;
}
