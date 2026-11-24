// Menolak literal merek di luar lapisan merek, supaya klon hanya berbeda di jawaban Copier.
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../..', import.meta.url));
const ANSWERS = join(ROOT, '.copier-answers.yml');
const SKIPPED = new Set(['node_modules', 'build', '.svelte-kit', '.git', '.gradle', '.kotlin', '.venv', '__pycache__', 'dist']);
// Hanya folder yang berasal dari template yang diperiksa; folder milik klien (misalnya situs di site/) boleh menyebut mereknya sendiri.
const TEMPLATE_FOLDERS = ['backend', 'web', 'pwa', 'app'];
const TEXT = /\.(py|ts|js|mjs|svelte|css|html|kt|kts|xml|json|webmanifest|toml|properties|md|example)$/;
const BRAND_LAYER = new Set(
	[
		'CLAUDE.md',
		'README.md',
		'backend/app/core/brand.py',
		'web/src/lib/text/brand.ts',
		'web/src/lib/charts/brand-colors.ts',
		'web/src/styles/brand.css',
		'web/src/app.html',
		'web/src/error.html',
		'pwa/src/lib/brand/brand.ts',
		'pwa/src/brand.css',
		'pwa/src/app.html',
		'pwa/static/manifest.webmanifest',
		'pwa/src/lib/text/strings_web_brand.xml',
		// Dibangkitkan dari strings_brand.xml oleh pwa/scripts/generate-strings.mjs.
		'pwa/src/lib/text/strings.ts',
		'app/brand.properties',
		'app/androidApp/src/main/res/values/colors.xml',
		'app/androidApp/src/main/res/values/strings.xml',
		'app/core/src/commonMain/composeResources/values/strings_brand.xml',
		'app/core/src/commonMain/kotlin/id/kongstudio/cafe/ui/theme/color/BrandColors.kt'
	].map((path) => path.split('/').join(sep))
);

if (!existsSync(ANSWERS)) {
	console.log('check-brand: dilewati, berkas jawaban Copier tidak ada (ini repositori template, bukan klon).');
	process.exit(0);
}

function answer(key) {
	const found = readFileSync(ANSWERS, 'utf8').match(new RegExp(String.raw`^${key}:\s*(.+?)\s*$`, 'm'));
	if (!found) throw new Error(`check-brand: jawaban ${key} tidak ada di .copier-answers.yml`);
	return found[1].replace(/^(['"])(.*)\1$/, '$2');
}

function literal(text) {
	return text.replace(/[.*+?^${}()|[\]\\]/g, String.raw`\$&`);
}

const needles = [
	// shortcut: slug tidak diperiksa karena bisa berupa kata umum (misalnya "contoh"), ditingkatkan bila slug diwajibkan unik.
	{ name: 'nama merek', pattern: new RegExp(literal(answer('brand_name')), 'i') },
	{ name: 'applicationId', pattern: new RegExp(literal(answer('application_id'))) }
];

function walk(dir) {
	return readdirSync(dir).flatMap((name) => {
		if (SKIPPED.has(name)) return [];
		const path = join(dir, name);
		return statSync(path).isDirectory() ? walk(path) : [path];
	});
}

const violations = [];
const roots = readdirSync(ROOT).filter((name) => !statSync(join(ROOT, name)).isDirectory() || TEMPLATE_FOLDERS.includes(name));
for (const path of roots.flatMap((name) => (statSync(join(ROOT, name)).isDirectory() ? walk(join(ROOT, name)) : [join(ROOT, name)]))) {
	const file = relative(ROOT, path);
	if (!TEXT.test(file) || BRAND_LAYER.has(file) || file.endsWith('package-lock.json')) continue;
	readFileSync(path, 'utf8')
		.split('\n')
		.forEach((line, index) => {
			for (const needle of needles) {
				if (needle.pattern.test(line)) violations.push(`${file}:${index + 1}  ${needle.name}`);
			}
		});
}

if (violations.length > 0) {
	console.error(`check-brand: ${violations.length} literal merek di luar lapisan merek:\n${violations.join('\n')}`);
	process.exit(1);
}
console.log('check-brand: bersih.');
