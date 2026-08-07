import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import fs from 'fs';
import path from 'path';

export const GET: RequestHandler = async ({ params }) => {
	const filename = params.filename;

	// Prevent path traversal attacks
	if (!filename || filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
		throw error(400, 'Nome de arquivo inválido');
	}

	const filePath = path.join(process.cwd(), 'static', 'uploads', 'products', filename);

	if (!fs.existsSync(filePath)) {
		console.error(`File not found at path: ${filePath}`);
		throw error(404, 'Arquivo não encontrado');
	}

	try {
		const fileBuffer = fs.readFileSync(filePath);
		
		// Guess content type based on extension
		const ext = path.extname(filename).toLowerCase();
		let contentType = 'application/octet-stream';
		
		if (ext === '.pdf') contentType = 'application/pdf';
		else if (ext === '.zip') contentType = 'application/zip';
		else if (ext === '.rar') contentType = 'application/x-rar-compressed';
		else if (ext === '.7z') contentType = 'application/x-7z-compressed';
		else if (ext === '.mp3') contentType = 'audio/mpeg';
		else if (ext === '.mp4') contentType = 'video/mp4';
		else if (ext === '.png') contentType = 'image/png';
		else if (ext === '.jpg' || ext === '.jpeg') contentType = 'image/jpeg';
		else if (ext === '.webp') contentType = 'image/webp';
		else if (ext === '.txt') contentType = 'text/plain';

		const inlineTypes = ['audio/mpeg', 'video/mp4', 'image/png', 'image/jpeg', 'image/webp', 'application/pdf'];
		const isInline = inlineTypes.includes(contentType);

		return new Response(fileBuffer, {
			headers: {
				'Content-Type': contentType,
				'Content-Disposition': isInline 
					? 'inline' 
					: `attachment; filename="${filename}"`,
				'Cache-Control': 'public, max-age=31536000'
			}
		});
	} catch (e) {
		console.error('Error serving product file:', e);
		throw error(500, 'Erro ao ler o arquivo no servidor');
	}
};
