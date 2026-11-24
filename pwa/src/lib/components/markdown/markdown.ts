/**
 * The small Markdown that procedures are written in. The phone app reads the very same rules
 * (ui/component/markdown/MarkdownParser.kt); change one, change both.
 *
 * Blocks, one line at a time: `#`/`##`/`###` headings, `---` divider, `![alt](https://...)` picture on its own line,
 * `> ` quote, `- ` bullets, `1. ` numbers, `- [ ]`/`- [x]` checklist, and everything else as paragraph text.
 * Inside text: `**bold**` and `*italic*`. A line break inside a paragraph stays a line break.
 */
export type Inline = { kind: 'text' | 'bold' | 'italic'; text: string };

export type Block =
	| { kind: 'heading'; level: 1 | 2 | 3; inlines: Inline[] }
	| { kind: 'paragraph'; inlines: Inline[] }
	| { kind: 'bullets'; items: Inline[][] }
	| { kind: 'numbers'; items: Inline[][] }
	| { kind: 'checks'; items: { checked: boolean; inlines: Inline[] }[] }
	| { kind: 'quote'; inlines: Inline[] }
	| { kind: 'divider' }
	| { kind: 'image'; alt: string; url: string };

const HEADING = /^(#{1,3})\s+(.*)$/;
const DIVIDER = /^---+$/;
const IMAGE = /^!\[([^\]]*)\]\((https?:\/\/\S+)\)$/;
const QUOTE = /^>\s?(.*)$/;
const CHECK = /^[-*]\s+\[([ xX])\]\s+(.*)$/;
const BULLET = /^[-*]\s+(.*)$/;
const NUMBER = /^\d+\.\s+(.*)$/;
const EMPHASIS = /\*\*([^*]+)\*\*|\*([^*]+)\*/g;

export function parseInline(text: string): Inline[] {
	const result: Inline[] = [];
	let last = 0;
	for (const match of text.matchAll(EMPHASIS)) {
		const at = match.index ?? 0;
		if (at > last) result.push({ kind: 'text', text: text.slice(last, at) });
		if (match[1] !== undefined) result.push({ kind: 'bold', text: match[1] });
		else result.push({ kind: 'italic', text: match[2] as string });
		last = at + match[0].length;
	}
	if (last < text.length) result.push({ kind: 'text', text: text.slice(last) });
	return result;
}

export function parseMarkdown(source: string): Block[] {
	const blocks: Block[] = [];
	let paragraph: string[] = [];
	let quote: string[] = [];

	const flush = (): void => {
		if (paragraph.length > 0) blocks.push({ kind: 'paragraph', inlines: parseInline(paragraph.join('\n')) });
		if (quote.length > 0) blocks.push({ kind: 'quote', inlines: parseInline(quote.join('\n')) });
		paragraph = [];
		quote = [];
	};

	for (const raw of source.replace(/\r\n?/g, '\n').split('\n')) {
		const line = raw.trim();
		let match: RegExpMatchArray | null;

		if (line === '') {
			flush();
		} else if ((match = line.match(HEADING))) {
			flush();
			blocks.push({ kind: 'heading', level: match[1]!.length as 1 | 2 | 3, inlines: parseInline(match[2]!) });
		} else if (DIVIDER.test(line)) {
			flush();
			blocks.push({ kind: 'divider' });
		} else if ((match = line.match(IMAGE))) {
			flush();
			blocks.push({ kind: 'image', alt: match[1]!, url: match[2]! });
		} else if ((match = line.match(QUOTE))) {
			if (paragraph.length > 0) flush();
			quote.push(match[1]!);
		} else if ((match = line.match(CHECK))) {
			flush();
			const item = { checked: match[1] !== ' ', inlines: parseInline(match[2]!) };
			const last = blocks[blocks.length - 1];
			if (last?.kind === 'checks') last.items.push(item);
			else blocks.push({ kind: 'checks', items: [item] });
		} else if ((match = line.match(BULLET))) {
			flush();
			const last = blocks[blocks.length - 1];
			if (last?.kind === 'bullets') last.items.push(parseInline(match[1]!));
			else blocks.push({ kind: 'bullets', items: [parseInline(match[1]!)] });
		} else if ((match = line.match(NUMBER))) {
			flush();
			const last = blocks[blocks.length - 1];
			if (last?.kind === 'numbers') last.items.push(parseInline(match[1]!));
			else blocks.push({ kind: 'numbers', items: [parseInline(match[1]!)] });
		} else {
			if (quote.length > 0) flush();
			paragraph.push(line);
		}
	}
	flush();
	return blocks;
}
