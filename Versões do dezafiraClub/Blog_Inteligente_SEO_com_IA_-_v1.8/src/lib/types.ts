export interface Post {
  id: number;
  title: string;
  slug: string;
  content: string;
  excerpt: string | null;
  cover_image: string | null;
  published: number;
  pinterest_enabled: number;
  pinterest_image: string | null;
  is_premium?: number;
  view_count?: number;
  created_at: string;
  updated_at: string;
  categories?: string;
  category_ids?: string;
  author_email?: string;
  category_name?: string;
  is_featured?: number;
  youtube_video_url?: string | null;
  tags?: string | null;
}

export interface Category {
	id: number;
	name: string;
	slug: string;
	description?: string | null;
	pinterest_enabled?: number;
	updated_at?: string;
	post_count?: number;
}

export interface User {
  id: number;
  username: string;
  password: string;
  name?: string;
  cpf?: string;
  phone?: string;
  created_at: string;
}

export interface PaginationData {
  posts: Post[];
  page: number;
  totalPages: number;
  totalPosts: number;
}

export interface SearchData {
  posts: Post[];
  page: number;
  totalPages: number;
  totalPosts: number;
  searchQuery: string;
}
