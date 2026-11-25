import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from 'svelte/compiler';
import ts from 'typescript';

// Every sentence a person reads lives in src/lib/text; a screen, a component, or a rule only points to it.
const ROOT = fileURLToPath(new URL('../src', import.meta.url));
// The text folder itself, the names of menus and pages and the ranges of dates (each is the one source of its own words),
// and the layers that hold no sentences for a person: the API client, the chart colours, the export, and the number formats.
const EXEMPT = ['lib/text/', 'lib/nav/', 'lib/date/', 'lib/api/', 'lib/charts/', 'lib/export/', 'lib/format/', 'hooks.server.ts'];

const TEXT_ATTRIBUTES = new Set(['label', 'title', 'placeholder', 'aria-label', 'alt', 'description', 'caption', 'hint', 'text', 'empty', 'subtitle', 'message', 'tooltip', 'heading', 'loadingText', 'value', 'emptyText']);
// Pada elemen HTML bawaan (option, input, button) value adalah kunci formulir, bukan teks yang dibaca pengguna.
const NATIVE_KEY_ATTRIBUTES = new Set(['value']);
const LETTER = /\p{L}/u;
// A sentence or a label: starts with a capital letter and holds only the characters of prose.
const PROSE = /^(?:[−=+–-] )?[A-ZÀ-Ý][\p{L}\p{N} .,:;!?()'"%&·…\-–/+“”]*$/u;
const PROSE_WITH_VALUES = /^[A-ZÀ-Ý{][\p{L}\p{N} .,:;!?()'"%&·…\-–/+“”{}]*$/u;
const STOPWORDS = /\b(yang|dan|atau|untuk|tidak|dengan|dari|pada|ini|itu|belum|sudah|bisa|akan|ke|di)\b/i;
const HYPHENATED_WORD = /^[A-Z][a-z]{2,}(-[a-z]+)+$/;
const INLINE_ELEMENTS = new Set(['strong', 'em', 'b', 'i', 'a', 'span', 'code', 'br', 'small', 'mark', 'u', 'kbd', 'sup', 'sub']);

function walk(dir) {
	return readdirSync(dir).flatMap((name) => {
		const path = join(dir, name);
		return statSync(path).isDirectory() ? walk(path) : [path];
	});
}

function lineOf(source, offset) {
	return source.slice(0, offset).split('\n').length;
}

/** The text of every string in TypeScript code that reads as a sentence, with its offset. */
function codeFindings(code, base, wrapped, found) {
	const text = wrapped ? `(${code})` : code;
	const shift = wrapped ? 1 : 0;
	const file = ts.createSourceFile('x.ts', text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
	const visit = (node) => {
		if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node) || ts.isTypeNode(node) || ts.isPropertySignature(node)) return;
		if (ts.isTemplateExpression(node) && !node.parent?.tag) {
			const pieces = [node.head.text, ...node.templateSpans.map((span) => span.literal.text)];
			const joined = pieces.join('{}').replace(/\s+/g, ' ').trim();
			if (LETTER.test(pieces.join('')) && PROSE_WITH_VALUES.test(joined) && /\s/.test(joined) && !/[/?]|[a-z]-[a-z]|\d:\d/.test(joined)) found.push({ offset: base + node.getStart() - shift, text: joined });
		}
		if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
			const value = node.text.trim();
			const parent = node.parent;
			const isKey = parent && ts.isPropertyAssignment(parent) && parent.name === node;
			const isComparison = parent && ts.isBinaryExpression(parent) && [ts.SyntaxKind.EqualsEqualsEqualsToken, ts.SyntaxKind.ExclamationEqualsEqualsToken].includes(parent.operatorToken.kind);
			const isLookup = parent && (ts.isCaseClause(parent) || ts.isElementAccessExpression(parent));
			const reads = /\s/.test(value) || STOPWORDS.test(value) || /^[A-Z][a-z]+[.…!?]*$/.test(value) || HYPHENATED_WORD.test(value);
			if (!isKey && !isComparison && !isLookup && value.length >= 2 && LETTER.test(value) && PROSE.test(value) && reads) found.push({ offset: base + node.getStart() - shift, text: value });
		}
		ts.forEachChild(node, visit);
	};
	visit(file);
}

function markupFindings(source, found) {
	const tree = parse(source, { modern: true });
	if (tree.instance) codeFindings(source.slice(tree.instance.content.start, tree.instance.content.end), tree.instance.content.start, false, found);
	if (tree.module) codeFindings(source.slice(tree.module.content.start, tree.module.content.end), tree.module.content.start, false, found);

	// Isi {...}, handler, dan prop di markup diperiksa sebagai kode, sehingga teks di dalam ekspresi ikut tertangkap.
	const expressionFindings = (node, wrapped = true) => {
		if (typeof node?.start !== 'number') return;
		codeFindings(source.slice(node.start, node.end), node.start, wrapped, found);
	};

	const visitAttributes = (node) => {
		for (const attribute of node.attributes ?? []) {
			if (attribute.type !== 'Attribute') {
				expressionFindings(attribute.expression);
				continue;
			}
			if (attribute.value === true) continue;
			const parts = Array.isArray(attribute.value) ? attribute.value : [attribute.value];
			for (const part of parts) {
				if (part.type === 'ExpressionTag') expressionFindings(part.expression);
			}
			if (!TEXT_ATTRIBUTES.has(attribute.name) || parts.every((part) => part.type === 'ExpressionTag')) continue;
			if (node.type === 'RegularElement' && NATIVE_KEY_ATTRIBUTES.has(attribute.name)) continue;
			const joined = parts.map((part) => (part.type === 'Text' ? part.data : '{}')).join('').trim();
			if (LETTER.test(joined.replace(/\{\}/g, ''))) found.push({ offset: attribute.start, text: joined });
		}
	};

	const visitNodes = (nodes) => {
		let run = [];
		const flush = () => {
			const joined = run
				.map((node) => (node.type === 'Text' ? node.data : '{}'))
				.join('')
				.replace(/\s+/g, ' ')
				.trim();
			if (LETTER.test(joined.replace(/\{\}/g, ''))) found.push({ offset: run[0].start, text: joined });
			run = [];
		};
		for (const node of nodes) {
			const inline = node.type === 'RegularElement' && INLINE_ELEMENTS.has(node.name) && node.fragment.nodes.every((child) => child.type === 'Text' || child.type === 'ExpressionTag');
			if (node.type === 'Text' || node.type === 'ExpressionTag' || inline) {
				if (node.type === 'ExpressionTag') expressionFindings(node.expression);
				if (inline) {
					visitAttributes(node);
					for (const child of node.fragment.nodes) {
						if (child.type === 'ExpressionTag') expressionFindings(child.expression);
					}
				}
				run.push(node);
				continue;
			}
			if (run.length > 0) flush();
			visitNode(node);
		}
		if (run.length > 0) flush();
	};
	const visitNode = (node) => {
		visitAttributes(node);
		for (const key of ['test', 'expression', 'key', 'tag']) expressionFindings(node[key]);
		expressionFindings(node.declaration, false);
		for (const key of ['fragment', 'consequent', 'alternate', 'body', 'pending', 'then', 'catch', 'fallback']) {
			if (node[key]?.nodes) visitNodes(node[key].nodes);
		}
		if (node.children) visitNodes(node.children);
	};
	visitNodes(tree.fragment.nodes);
}

const violations = [];
for (const path of walk(ROOT)) {
	const file = relative(ROOT, path).split(sep).join('/');
	if (!/\.(ts|svelte)$/.test(file) || file.endsWith('.d.ts') || EXEMPT.some((prefix) => file.startsWith(prefix))) continue;
	const source = readFileSync(path, 'utf8');
	const found = [];
	if (file.endsWith('.svelte')) markupFindings(source, found);
	else codeFindings(source, 0, false, found);
	for (const item of found) violations.push(`${file}:${lineOf(source, item.offset)}  ${JSON.stringify(item.text.length > 80 ? `${item.text.slice(0, 77)}...` : item.text)}`);
}

if (violations.length > 0) {
	console.error('Teks untuk pengguna ditulis di luar src/lib/text. Pindahkan ke berkas teks domainnya dan panggil dari sana:\n');
	console.error(violations.join('\n'));
	process.exit(1);
}
console.log('Teks: semua dari src/lib/text.');
