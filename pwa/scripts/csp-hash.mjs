import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

/** Hash gaya yang ditulis SvelteKit sendiri pada elemen pengumuman pembaca layar; dibaca dari paketnya supaya ikut benar setelah SvelteKit diperbarui. */
export function announcerStyleHash() {
	const root = dirname(createRequire(import.meta.url).resolve('@sveltejs/kit/package.json'));
	const source = readFileSync(join(root, 'src/core/sync/write_root.js'), 'utf8');
	const style = /id="svelte-announcer"[^>]*style="([^"]+)"/.exec(source)?.[1];
	if (!style) throw new Error('Gaya elemen svelte-announcer tidak ditemukan di SvelteKit; perbarui scripts/csp-hash.mjs sebelum membangun.');
	return `sha256-${createHash('sha256').update(style).digest('base64')}`;
}
