import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		// En desarrollo (npm run dev) redirige la API al backend de Django
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	}
});
