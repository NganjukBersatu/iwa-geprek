import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

// Opsi SvelteKit (adapter dan CSP) ada di vite.config.ts; berkas ini diabaikan selama opsi itu diberikan di sana.
/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess()
};

export default config;
