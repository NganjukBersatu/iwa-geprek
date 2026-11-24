// Membuat src/lib/text/strings.ts dari teks app Android (strings.xml), supaya kata-kata PWA identik dan satu sumber.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const values = join(root, '../app/core/src/commonMain/composeResources/values');
const out = join(root, 'src/lib/text/strings.ts');
const FILES = [
	...['strings.xml', 'strings_brand.xml', 'strings_failure.xml', 'strings_release.xml'].map((file) => join(values, file)),
	// Teks khusus PWA, nama diawali web_.
	join(root, 'src/lib/text/strings_web.xml'),
	join(root, 'src/lib/text/strings_web_brand.xml')
];

function unescapeXml(text) {
	return text
		.replace(/\\n/g, '\n')
		.replace(/\\'/g, "'")
		.replace(/\\"/g, '"')
		.replace(/\\@/g, '@')
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&quot;/g, '"')
		.replace(/&apos;/g, "'")
		.replace(/&amp;/g, '&');
}

const strings = {};
const arrays = {};
for (const file of FILES) {
	const xml = readFileSync(file, 'utf8').replace(/<!--[\s\S]*?-->/g, '');
	for (const match of xml.matchAll(/<string name="([^"]+)">([\s\S]*?)<\/string>/g)) strings[match[1]] = unescapeXml(match[2].trim());
	for (const match of xml.matchAll(/<string-array name="([^"]+)">([\s\S]*?)<\/string-array>/g)) {
		arrays[match[1]] = [...match[2].matchAll(/<item>([\s\S]*?)<\/item>/g)].map((item) => unescapeXml(item[1].trim()));
	}
}

const quote = (value) => JSON.stringify(value);
const body = [
	'// Dibuat oleh scripts/generate-strings.mjs dari strings.xml app Android. Jangan diubah tangan.',
	'',
	'export const strings = {',
	...Object.entries(strings).map(([key, value]) => `\t${key}: ${quote(value)},`),
	'} as const;',
	'',
	'export const stringArrays = {',
	...Object.entries(arrays).map(([key, items]) => `\t${key}: [${items.map(quote).join(', ')}],`),
	'} as const;',
	'',
	'export type StringKey = keyof typeof strings;',
	'export type ArrayKey = keyof typeof stringArrays;',
	''
].join('\n');

mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, body);
console.log(`strings.ts: ${Object.keys(strings).length} teks, ${Object.keys(arrays).length} daftar`);
