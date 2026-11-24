// Membuat src/lib/text/release-notes.ts dari versi dan ringkasan "Yang baru" milik APK dan PWA, supaya halaman Unduhan tidak menyalin tangan.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const app = join(root, '../app');
const employee = join(root, '../pwa');
const out = join(root, 'src/lib/text/release-notes.ts');

const read = (path) => readFileSync(path, 'utf8');

function unescapeXml(text) {
	return text
		.replace(/\\'/g, "'")
		.replace(/\\"/g, '"')
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&quot;/g, '"')
		.replace(/&apos;/g, "'")
		.replace(/&amp;/g, '&');
}

const kebab = (name) =>
	name
		.replace(/([a-z0-9])([A-Z])/g, '$1-$2')
		.replace(/([A-Z])([A-Z][a-z])/g, '$1-$2')
		.replace(/([a-zA-Z])([0-9])/g, '$1-$2')
		.toLowerCase();

const apkVersion = read(join(app, 'version.properties')).match(/^versionName=(\S+)\s*$/m)?.[1];
if (!apkVersion) throw new Error('versionName tidak ditemukan di app/version.properties');
const iosVersion = JSON.parse(read(join(employee, 'version.json'))).version;
if (typeof iosVersion !== 'string' || iosVersion === '') throw new Error('version tidak ditemukan di pwa/version.json');

const texts = {};
const xml = read(join(app, 'core/src/commonMain/composeResources/values/strings_release.xml')).replace(/<!--[\s\S]*?-->/g, '');
for (const match of xml.matchAll(/<string name="([^"]+)">([\s\S]*?)<\/string>/g)) texts[match[1]] = unescapeXml(match[2].trim());

const iconClasses = {};
const appIcons = read(join(app, 'core/src/commonMain/kotlin/id/kongstudio/cafe/ui/theme/icon/AppIcons.kt'));
for (const [, appName, , iconName] of appIcons.matchAll(/val (\w+): ImageVector get\(\) = (\w+)\.(\w+)/g)) iconClasses[appName] = kebab(iconName.replace(/Filled$/, ''));
const webfont = read(join(root, 'node_modules/@tabler/icons-webfont/dist/tabler-icons.min.css'));
const known = new Set([...webfont.matchAll(/\.ti-([a-z0-9-]+):before/g)].map((match) => match[1]));

function note(source, key, icon) {
	const text = texts[key];
	if (text === undefined) throw new Error(`${source}: teks ${key} tidak ada di strings_release.xml`);
	const name = iconClasses[icon];
	if (name === undefined) throw new Error(`${source}: ikon ${icon} tidak ada di AppIcons.kt`);
	if (!known.has(name)) throw new Error(`${source}: kelas ti-${name} tidak ada di webfont Tabler`);
	return { icon: name, text };
}

function notesOf(source, matches) {
	const notes = matches.map(([key, icon]) => note(source, key, icon));
	if (notes.length === 0) throw new Error(`${source}: ringkasan kosong atau bentuk barisnya berubah`);
	return notes;
}

const operationalSource = 'ReleaseNotes.kt';
const releaseNotesKt = read(join(app, 'shared/src/commonMain/kotlin/id/kongstudio/cafe/feature/release/ReleaseNotes.kt'));

// Baris "Res.string.x to AppIcons.y" di dalam satu daftar bernama, supaya Yang baru dan Perbaikan tidak tercampur.
function entriesOf(name) {
	const block = releaseNotesKt.match(new RegExp(`val ${name}\\b[^=]*=\\s*listOf\\(([\\s\\S]*?)\\n\\)`))?.[1];
	if (block === undefined) throw new Error(`${operationalSource}: daftar ${name} tidak ditemukan`);
	return [...block.matchAll(/Res\.string\.(\w+) to AppIcons\.(\w+)/g)].map((match) => [match[1], match[2]]);
}

const operational = notesOf(operationalSource, entriesOf('ApkReleaseNotes'));
const employeeSource = 'release-notes.ts web karyawan';
const employeeNotes = notesOf(
	employeeSource,
	[...read(join(employee, 'src/lib/features/release/release-notes.ts')).matchAll(/icon: '(\w+)', key: '(\w+)'/g)].map((match) => [match[2], match[1]])
);

const list = (notes) => notes.map((item) => `\t{ icon: ${JSON.stringify(item.icon)}, text: ${JSON.stringify(item.text)} },`);
const body = [
	'// Dibuat oleh scripts/generate-release.mjs dari app Android dan web karyawan. Jangan diubah tangan.',
	'',
	"import type { ReleaseNote } from '$lib/features/download/release';",
	'',
	`export const APK_VERSION = ${JSON.stringify(apkVersion)};`,
	'',
	`export const IOS_VERSION = ${JSON.stringify(iosVersion)};`,
	'',
	'export const APK_NOTES: ReleaseNote[] = [',
	...list(operational),
	'];',
	'',
	'export const IOS_NOTES: ReleaseNote[] = [',
	...list(employeeNotes),
	'];',
	''
].join('\n');

writeFileSync(out, body);
console.log(`release-notes.ts: APK ${apkVersion} (${operational.length} catatan), iPhone ${iosVersion} (${employeeNotes.length} catatan)`);
