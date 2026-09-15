import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			// SPA: cualquier ruta no pre-renderizada sirve index.html
			fallback: 'index.html',
			precompress: false,
			strict: true
		})
	}
};

export default config;
