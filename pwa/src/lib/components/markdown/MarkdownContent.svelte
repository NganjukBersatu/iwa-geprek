<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import RemoteImage from '$lib/components/media/RemoteImage.svelte';
	import { parseMarkdown, type Inline } from './markdown';

	/** Isi slide ditulis dalam Markdown kecil; menggambar judul, paragraf, daftar, kutipan, garis, dan gambar. */
	let { source }: { source: string } = $props();

	const blocks = $derived(parseMarkdown(source));
</script>

{#snippet inline(spans: Inline[])}
	{#each spans as span, index (index)}
		{#if span.kind === 'bold'}<strong class="font-bold">{span.text}</strong>{:else if span.kind === 'italic'}<em>{span.text}</em>{:else}{span.text}{/if}
	{/each}
{/snippet}

<div class="flex w-full flex-col gap-3">
	{#each blocks as block, index (index)}
		{#if block.kind === 'heading'}
			<p class="m-0 whitespace-pre-line text-content {block.level === 1 ? 'text-title' : block.level === 2 ? 'text-title !text-[20px] !leading-[26px]' : 'text-button'}">{@render inline(block.inlines)}</p>
		{:else if block.kind === 'paragraph'}
			<p class="text-body m-0 whitespace-pre-line text-content">{@render inline(block.inlines)}</p>
		{:else if block.kind === 'bullets' || block.kind === 'numbers'}
			{@const numbered = block.kind === 'numbers'}
			<div class="flex flex-col gap-1">
				{#each block.items as item, itemIndex (itemIndex)}
					<div class="text-body flex gap-2 text-content">
						<span>{numbered ? `${itemIndex + 1}.` : '•'}</span>
						<span class="min-w-0 flex-1 whitespace-pre-line">{@render inline(item)}</span>
					</div>
				{/each}
			</div>
		{:else if block.kind === 'checks'}
			<div class="flex flex-col gap-2">
				{#each block.items as item, itemIndex (itemIndex)}
					<div class="flex items-start gap-2">
						<span
							class="flex size-5 shrink-0 items-center justify-center border {item.checked ? 'border-primary bg-primary' : 'border-outline bg-surface'}"
							use:dynamicStyle={{ 'border-radius': '6px' }}
						>
							{#if item.checked}<AppIcon icon="Check" tint="on-primary" size={14} />{/if}
						</span>
						<span class="text-body min-w-0 flex-1 whitespace-pre-line {item.checked ? 'text-content-muted line-through' : 'text-content'}">{@render inline(item.inlines)}</span>
					</div>
				{/each}
			</div>
		{:else if block.kind === 'quote'}
			<div class="flex w-full overflow-hidden rounded-field bg-selected">
				<span class="w-1 shrink-0 bg-primary"></span>
				<p class="text-body m-0 whitespace-pre-line p-3 text-content">{@render inline(block.inlines)}</p>
			</div>
		{:else if block.kind === 'divider'}
			<div class="h-px w-full bg-divider"></div>
		{:else}
			<RemoteImage url={block.url} description={block.alt || null} fit />
		{/if}
	{/each}
</div>
