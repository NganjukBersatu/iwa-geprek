import type { JSONContent } from '@tiptap/core';
import { parseMarkdown, type Block, type Inline } from '../markdown/markdown';

/** The only bridge between the editor's document and the small Markdown of markdown.ts, which the phone app reads too. */

const BULLET_MARKS = /^[•·▪●◦–—]\s*/;
const NUMBER_PAREN = /^(\d+)\)\s+/;
const EXTRA_BLANKS = /\n{3,}/g;

function inlineNodes(inlines: Inline[]): JSONContent[] {
	const nodes: JSONContent[] = [];
	for (const inline of inlines) {
		const marks = inline.kind === 'text' ? undefined : [{ type: inline.kind }];
		inline.text.split('\n').forEach((piece, at) => {
			if (at > 0) nodes.push({ type: 'hardBreak' });
			if (piece) nodes.push({ type: 'text', text: piece, ...(marks ? { marks } : {}) });
		});
	}
	return nodes;
}

function paragraph(inlines: Inline[]): JSONContent {
	const content = inlineNodes(inlines);
	return content.length > 0 ? { type: 'paragraph', content } : { type: 'paragraph' };
}

function blockNode(block: Block): JSONContent {
	switch (block.kind) {
		case 'heading':
			return { type: 'heading', attrs: { level: block.level }, content: inlineNodes(block.inlines) };
		case 'paragraph':
			return paragraph(block.inlines);
		case 'bullets':
			return { type: 'bulletList', content: block.items.map((item) => ({ type: 'listItem', content: [paragraph(item)] })) };
		case 'numbers':
			return { type: 'orderedList', attrs: { start: 1 }, content: block.items.map((item) => ({ type: 'listItem', content: [paragraph(item)] })) };
		case 'checks':
			return {
				type: 'taskList',
				content: block.items.map((item) => ({ type: 'taskItem', attrs: { checked: item.checked }, content: [paragraph(item.inlines)] }))
			};
		case 'quote':
			return { type: 'blockquote', content: [paragraph(block.inlines)] };
		case 'divider':
			return { type: 'horizontalRule' };
		case 'image':
			return { type: 'image', attrs: { src: block.url, alt: block.alt } };
		case 'video':
			return { type: 'video', attrs: { src: block.url, alt: block.alt } };
	}
}

export function toDoc(markdown: string): JSONContent {
	const content = parseMarkdown(markdown).map(blockNode);
	return { type: 'doc', content: content.length > 0 ? content : [{ type: 'paragraph' }] };
}

function inlineText(nodes: JSONContent[] = []): string {
	return nodes
		.map((node) => {
			if (node.type === 'hardBreak') return '\n';
			const text = node.text ?? '';
			if (!text.trim()) return text;
			const marks = new Set((node.marks ?? []).map((mark) => mark.type));
			// The stored Markdown has no bold-and-italic together; bold carries the stronger meaning.
			if (marks.has('bold')) return `**${text}**`;
			if (marks.has('italic')) return `*${text}*`;
			return text;
		})
		.join('');
}

/** A list item's text on one line; nested lists cannot be stored, so their items follow as items of their own. */
function itemLines(item: JSONContent, marker: (at: number, node: JSONContent) => string, start: number): string[] {
	const own: string[] = [];
	const nested: string[] = [];
	for (const child of item.content ?? []) {
		if (child.type === 'paragraph' || child.type === 'heading') own.push(inlineText(child.content).replace(/\n/g, ' ').trim());
		else nested.push(...blockLines(child));
	}
	return [`${marker(start, item)}${own.filter(Boolean).join(' ')}`, ...nested];
}

function blockLines(node: JSONContent): string[] {
	const items = node.content ?? [];
	switch (node.type) {
		case 'paragraph': {
			const text = inlineText(node.content).trim();
			return text ? [text] : [];
		}
		case 'heading': {
			const text = inlineText(node.content).replace(/\n/g, ' ').trim();
			return text ? [`${'#'.repeat(Number(node.attrs?.['level'] ?? 1))} ${text}`] : [];
		}
		case 'bulletList':
			return items.flatMap((item) => itemLines(item, () => '- ', 0));
		case 'orderedList':
			return items.flatMap((item, at) => itemLines(item, (number) => `${number}. `, at + 1));
		case 'taskList':
			return items.flatMap((item) => itemLines(item, (_, task) => (task.attrs?.['checked'] ? '- [x] ' : '- [ ] '), 0));
		case 'blockquote':
			return items
				.flatMap((child) => blockLines(child))
				.flatMap((text) => text.split('\n'))
				.map((line) => `> ${line}`);
		case 'horizontalRule':
			return ['---'];
		case 'image':
		case 'video': {
			const src = String(node.attrs?.['src'] ?? '');
			const alt = String(node.attrs?.['alt'] ?? '').replace(/[[\]]/g, '');
			return src ? [`![${alt}](${src})`] : [];
		}
		default:
			return [];
	}
}

export function toMarkdown(doc: JSONContent): string {
	return (doc.content ?? [])
		.map((node) => blockLines(node).join('\n'))
		.filter(Boolean)
		.join('\n\n');
}

/** Tidies pasted or hurried text: chat-style bullets and "1)" numbers become real lists, and stray spaces and blank lines go. */
export function tidyMarkdown(markdown: string): string {
	const lines = markdown
		.replace(/\r\n?/g, '\n')
		.split('\n')
		.map((line) => line.replace(/\s+$/, ''))
		.map((line) => {
			const trimmed = line.trimStart();
			if (BULLET_MARKS.test(trimmed)) return `- ${trimmed.replace(BULLET_MARKS, '')}`;
			const numbered = trimmed.match(NUMBER_PAREN);
			if (numbered) return `${numbered[1]}. ${trimmed.replace(NUMBER_PAREN, '')}`;
			return line;
		});
	// Reading it back and writing it again also renumbers lists and joins lists split by blank lines.
	return toMarkdown(toDoc(lines.join('\n').replace(EXTRA_BLANKS, '\n\n').trim()));
}
