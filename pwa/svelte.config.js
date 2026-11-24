import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { announcerStyleHash } from './scripts/csp-hash.mjs';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	compilerOptions: {
		runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
	},
	kit: {
		// adapter-node: hasil build dijalankan sebagai server Node (`node build`), cocok untuk Railway.
		// PORT/HOST dibaca dari environment oleh adapter.
		adapter: adapter({ out: 'build' }),
		// Inline styles are never allowed: values go through the style object (the dynamicStyle action) and the one inline style SvelteKit writes itself is allowed by its hash.
		csp: {
			mode: 'auto',
			directives: {
				'default-src': ['self'],
				'script-src': ['self'],
				'style-src': ['self'],
				'style-src-attr': ['unsafe-hashes', announcerStyleHash()],
				'img-src': ['self', 'data:', 'blob:', 'https:'],
				'media-src': ['self', 'blob:', 'https:'],
				'font-src': ['self', 'data:'],
				'connect-src': ['self'],
				'worker-src': ['self'],
				'manifest-src': ['self'],
				'object-src': ['none'],
				'base-uri': ['self'],
				'form-action': ['self'],
				'frame-ancestors': ['none'],
				// Violations are sent to the backend through the API proxy.
				'report-uri': ['/api/csp-reports']
			}
		}
	}
};

export default config;
