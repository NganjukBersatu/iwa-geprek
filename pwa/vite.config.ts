import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import pkg from './package.json';

export default defineConfig({
	define: { __APP_VERSION__: JSON.stringify(pkg.version) },
	server: {
		port: 5175,
		strictPort: true
	},
	plugins: [tailwindcss(), sveltekit()]
});
