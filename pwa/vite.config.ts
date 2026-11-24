import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
// Versi PWA milik klien; copier update tidak menimpa version.json.
import release from './version.json' with { type: 'json' };

export default defineConfig({
	define: { __APP_VERSION__: JSON.stringify(release.version) },
	server: {
		port: 5175,
		strictPort: true
	},
	plugins: [tailwindcss(), sveltekit()]
});
