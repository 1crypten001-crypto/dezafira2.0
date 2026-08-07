import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { searchPosts } from '$lib/server/database';

export const GET: RequestHandler = async ({ url }) => {
  try {
    const q = url.searchParams.get('q') || '';
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    if (!q || q.trim().length < 2) {
      return json({ 
        error: 'Query deve ter pelo menos 2 caracteres' 
      }, { status: 400 });
    }

    const results = await searchPosts(q.trim(), page, limit);

    return json({
      query: q,
      ...results
    });
  } catch (error) {
    console.error('Search API error:', error);
    return json({ error: 'Erro na busca' }, { status: 500 });
  }
};