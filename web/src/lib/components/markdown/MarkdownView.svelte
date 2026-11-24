<script lang="ts">
	import { parseMarkdown, type Inline } from './markdown';

	let { source }: { source: string } = $props();

	const blocks = $derived(parseMarkdown(source));
	const HEADING_SIZE = { 1: 'text-2xl font-semibold', 2: 'text-xl font-semibold', 3: 'text-base font-semibold' } as const;
	const inlineClass = (inline: Inline) => (inline.kind === 'bold' ? 'font-semibold' : inline.kind === 'italic' ? 'italic' : '');
</script>

{#snippet inlines(parts: Inline[])}{#each parts as part, index (index)}<span class={inlineClass(part)}>{part.text}</span>{/each}{/snippet}

<div class="flex flex-col gap-3 text-sm leading-6 text-slate-800">
	{#each blocks as block, index (index)}
		{#if block.kind === 'heading'}
			<p class="{HEADING_SIZE[block.level]} text-slate-800">{@render inlines(block.inlines)}</p>
		{:else if block.kind === 'paragraph'}
			<p class="whitespace-pre-line">{@render inlines(block.inlines)}</p>
		{:else if block.kind === 'bullets'}
			<ul class="flex list-disc flex-col gap-1 pl-5">
				{#each block.items as item, at (at)}<li>{@render inlines(item)}</li>{/each}
			</ul>
		{:else if block.kind === 'numbers'}
			<ol class="flex list-decimal flex-col gap-1 pl-5">
				{#each block.items as item, at (at)}<li>{@render inlines(item)}</li>{/each}
			</ol>
		{:else if block.kind === 'checks'}
			<ul class="flex flex-col gap-1.5">
				{#each block.items as item, at (at)}
					<li class="flex items-start gap-2">
						<i class="ti {item.checked ? 'ti-square-check-filled text-brand' : 'ti-square text-slate-500'} mt-0.5 text-xl leading-none" aria-hidden="true"></i>
						<span class={item.checked ? 'text-slate-500 line-through' : ''}>{@render inlines(item.inlines)}</span>
					</li>
				{/each}
			</ul>
		{:else if block.kind === 'quote'}
			<blockquote class="whitespace-pre-line rounded-r-lg border-l-4 border-brand-line bg-brand-page px-3 py-2 text-slate-700">{@render inlines(block.inlines)}</blockquote>
		{:else if block.kind === 'divider'}
			<hr class="border-slate-200" />
		{:else if block.kind === 'image'}
			<img src={block.url} alt={block.alt} loading="lazy" class="max-h-80 w-full rounded-lg border border-slate-100 object-contain" />
		{:else if block.kind === 'video'}
			<!-- svelte-ignore a11y_media_has_caption -->
			<video src={block.url} title={block.alt} controls playsinline preload="metadata" class="max-h-80 w-full rounded-lg border border-slate-100 bg-slate-800"></video>
		{/if}
	{/each}
</div>
