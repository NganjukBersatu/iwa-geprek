import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../src', import.meta.url));
// Canvas drawing takes raw colours, not classes: chart themes and the white backing a photo gets before it becomes a JPEG.
const HEX_ALLOWED = new Set(['app.css', 'app.html', join('lib', 'charts', 'theme.ts'), join('lib', 'image', 'shrink.ts'), join('styles', 'brand.css'), join('lib', 'charts', 'brand-colors.ts')]);
const FAMILIES =
	'red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|gray|zinc|neutral|stone|mauve|olive|mist|taupe';
const UTILITIES = 'bg|text|border|ring|fill|stroke|from|via|to|divide|outline|decoration|shadow|accent|caret|placeholder';

const rules = [
	{ name: 'hex mentah', test: (file) => !HEX_ALLOWED.has(file), pattern: /(?<![&\w])#[0-9a-fA-F]{3,8}\b/ },
	{ name: 'fungsi warna mentah', test: (file) => file !== 'app.css' && !HEX_ALLOWED.has(file), pattern: /\b(?:rgba?|hsla?|oklch|oklab|lab|lch)\(/ },
	{
		name: 'keluarga warna di luar palet',
		test: () => true,
		pattern: new RegExp(String.raw`\b(?:${UTILITIES})-(?:${FAMILIES})-\d{2,3}\b`)
	},
	{
		name: 'langkah slate di luar palet',
		test: () => true,
		pattern: new RegExp(String.raw`\b(?:${UTILITIES})-slate-(?:900|950)\b`)
	},
	{
		name: 'warna sembarang pada kelas',
		test: () => true,
		pattern: new RegExp(String.raw`\b(?:${UTILITIES})-\[(?:#|rgb|hsl|oklch)`)
	}
];

function walk(dir) {
	return readdirSync(dir).flatMap((name) => {
		const path = join(dir, name);
		return statSync(path).isDirectory() ? walk(path) : [path];
	});
}

const violations = [];
for (const path of walk(ROOT)) {
	if (!/\.(svelte|ts|css|html)$/.test(path)) continue;
	const file = relative(ROOT, path);
	readFileSync(path, 'utf8')
		.split('\n')
		.forEach((line, index) => {
			for (const rule of rules) {
				if (rule.test(file) && rule.pattern.test(line)) {
					violations.push(`${file.split(sep).join('/')}:${index + 1}  ${rule.name}  ${line.trim().slice(0, 90)}`);
				}
			}
		});
}

if (violations.length > 0) {
	console.error(`Warna di luar palet (${violations.length}):\n${violations.join('\n')}`);
	process.exit(1);
}
console.log('Warna: semua sesuai palet.');
