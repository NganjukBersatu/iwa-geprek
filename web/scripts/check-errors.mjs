import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../src', import.meta.url));
// The client that builds ApiError and the translator are the only places that may read an error's own words.
const ALLOWED = new Set([join('lib', 'api', 'http.ts'), join('lib', 'api', 'user-message.ts')]);
// A screen shows userMessage(error), never what an exception happens to say.
const PATTERN = /instanceof\s+(?:Error|ApiError)\b[^;\n]*\.message\b/;

function walk(dir) {
	return readdirSync(dir).flatMap((name) => {
		const path = join(dir, name);
		return statSync(path).isDirectory() ? walk(path) : [path];
	});
}

const violations = [];
for (const path of walk(ROOT)) {
	const file = relative(ROOT, path);
	if (!/\.(ts|svelte)$/.test(file) || file.endsWith('schema.d.ts') || ALLOWED.has(file)) continue;
	readFileSync(path, 'utf8')
		.split(/\r?\n/)
		.forEach((line, index) => {
			if (PATTERN.test(line)) violations.push(`${file.split(sep).join('/')}:${index + 1}  ${line.trim()}`);
		});
}

if (violations.length > 0) {
	console.error('Error ditampilkan lewat teks bawaan exception. Pakai userMessage(error, fallback) dari $lib/api/user-message:\n');
	console.error(violations.join('\n'));
	process.exit(1);
}
console.log('Error: semua lewat userMessage.');
