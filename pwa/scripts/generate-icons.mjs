// Membuat src/lib/theme/icons.ts dari AppIcons.kt app Android: nama ikon sama dengan app, gambarnya dari webfont Tabler yang dipasang lewat npm.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const appIcons = join(root, '../app/core/src/commonMain/kotlin/id/kongstudio/cafe/ui/theme/icon/AppIcons.kt');
const webfont = join(root, 'node_modules/@tabler/icons-webfont/dist/tabler-icons.min.css');
const out = join(root, 'src/lib/theme/icons.ts');

const kebab = (name) =>
	name
		.replace(/([a-z0-9])([A-Z])/g, '$1-$2')
		.replace(/([A-Z])([A-Z][a-z])/g, '$1-$2')
		.replace(/([a-zA-Z])([0-9])/g, '$1-$2')
		.toLowerCase();

const classes = new Set([...readFileSync(webfont, 'utf8').matchAll(/\.ti-([a-z0-9-]+):before/g)].map((match) => match[1]));
const names = [...readFileSync(appIcons, 'utf8').matchAll(/val (\w+): ImageVector get\(\) = (\w+)\.(\w+)/g)];

const used = {};
for (const [, appName, packName, iconName] of names) {
	// Ikon terisi hanya ada di webfont terpisah yang bentrok dengan set garis, jadi PWA memakai versi garisnya lewat nama tanpa Filled.
	if (iconName.endsWith('Filled')) continue;
	const name = kebab(iconName);
	if (!classes.has(name)) throw new Error(`Kelas ti-${name} untuk ${appName} (${packName}.${iconName}) tidak ada di webfont Tabler`);
	used[appName] = `ti-${name}`;
}

const body = [
	'// Dibuat oleh scripts/generate-icons.mjs dari AppIcons.kt app Android dan webfont Tabler. Jangan diubah tangan.',
	'',
	'export const icons = {',
	...Object.entries(used).map(([name, css]) => `\t${name}: '${css}',`),
	'} as const;',
	'',
	'export type IconName = keyof typeof icons;',
	''
].join('\n');

mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, body);
console.log(`icons.ts: ${Object.keys(used).length} ikon`);
