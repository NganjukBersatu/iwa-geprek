import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import adapter from '@sveltejs/adapter-node';
import { policy, REPORT_GROUP, REPORT_PATH } from './src/lib/security/csp.ts';
import { announcerStyleHash } from './scripts/csp-hash.ts';

export default defineConfig({
	server: {
		port: 5174,
		strictPort: true
	},
	plugins: [
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			adapter: adapter(),
			// svelte.config.js is not read while options are given here, so the policy lives here; violations are still sent to the report address.
			csp: { mode: 'auto', directives: { ...policy, 'style-src-attr': ['unsafe-hashes', announcerStyleHash()], 'report-uri': [REPORT_PATH], 'report-to': [REPORT_GROUP] } }
		})
	]
});
