import { redirect, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { 
  getNewsletterSubscribers, 
  deleteNewsletterSubscriber,
  getNewsletterCampaigns,
  createNewsletterCampaign,
  getActiveNewsletterEmails,
  getSettings
} from '$lib/server/database';
import { sendNewsletterCampaignEmail, isResendConfigured } from '$lib/server/resend';

export const load: PageServerLoad = async ({ url }) => {
  const page = parseInt(url.searchParams.get('page') || '1');
  const search = url.searchParams.get('q') || '';
  const campaignPage = parseInt(url.searchParams.get('cpage') || '1');
  
  const subscribersData = await getNewsletterSubscribers(page, 20, search);
  const campaignsData = await getNewsletterCampaigns(campaignPage, 10);
  const settings = await getSettings();
  const resendReady = await isResendConfigured();
  
  const activeEmails = await getActiveNewsletterEmails();
  
  return { 
    ...subscribersData, 
    ...campaignsData,
    searchQuery: search,
    activeCount: activeEmails.length,
    activeEmails,
    resendReady,
    siteTitle: settings.site_title || 'Blog',
    siteUrl: settings.site_url || url.origin
  };
};

export const actions: Actions = {
  delete: async ({ request }) => {
    const data = await request.formData();
    const id = data.get('id');
    
    if (!id) {
      return fail(400, { error: 'NL_ID_REQUIRED' });
    }
    
    try {
      await deleteNewsletterSubscriber(parseInt(id as string));
      return { success: true, message: 'NL_DELETE_SUCCESS' };
    } catch (e) {
      console.error('Error deleting subscriber:', e);
      return fail(500, { error: 'NL_DELETE_FAIL' });
    }
  },
  
  sendCampaign: async ({ request, url }) => {
    const data = await request.formData();
    const subject = data.get('subject') as string;
    const content = data.get('content') as string;
    const youtubeVideoUrl = data.get('youtube_video_url') as string || null;
    const sendTo = data.get('send_to') as string; // 'all' | 'selected'
    
    if (!subject || !content) {
      return fail(400, { error: 'NL_SUBJECT_CONTENT' });
    }

    const resendReady = await isResendConfigured();
    if (!resendReady) {
      return fail(400, { error: 'NL_RESEND_NOT_CONFIGURED' });
    }

    try {
      let emails: string[] = [];
      if (sendTo === 'all') {
        emails = await getActiveNewsletterEmails();
      } else {
        const selectedEmailsRaw = data.get('selected_emails') as string;
        emails = selectedEmailsRaw ? selectedEmailsRaw.split(',').map(e => e.trim()).filter(Boolean) : [];
      }

      if (emails.length === 0) {
        return fail(400, { error: 'NL_NO_RECIPIENTS' });
      }

      const settings = await getSettings();
      const siteName = settings.site_title || 'Blog';
      const siteUrl = (settings.site_url || url.origin).replace(/\/$/, '');

      const success = await sendNewsletterCampaignEmail(
        emails,
        subject,
        content,
        youtubeVideoUrl,
        siteName,
        siteUrl
      );

      if (!success) {
        return fail(500, { error: 'NL_SEND_FAIL' });
      }

      await createNewsletterCampaign({
        subject,
        content,
        youtubeVideoUrl: youtubeVideoUrl || undefined,
        recipientsCount: emails.length
      });

      return {
        success: true,
        message: 'NL_CAMPAIGN_SENT',
        subject,
        count: emails.length
      };
    } catch (e) {
      console.error('Error executing campaign delivery action:', e);
      return fail(500, { error: 'NL_SERVER_ERROR' });
    }
  }
};
