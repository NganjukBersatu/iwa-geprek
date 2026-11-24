<script lang="ts">
	import type { Snippet } from 'svelte';

	/** Baris daftar: [leading] di kiri, judul dengan keterangan bertingkat, dan [trailing] di kanan. */
	let {
		title,
		detail,
		caption,
		footnote,
		onclick,
		leading,
		trailing
	}: {
		title: string;
		detail?: string | null;
		caption?: string | null;
		footnote?: string | null;
		onclick?: () => void;
		leading?: Snippet;
		trailing?: Snippet;
	} = $props();
</script>

{#snippet body()}
	{@render leading?.()}
	<div class="min-w-0 flex-1">
		<p class="text-body m-0 text-content">{title}</p>
		{#if detail}<p class="text-caption m-0 text-content">{detail}</p>{/if}
		{#if caption}<p class="text-caption m-0 text-content-muted">{caption}</p>{/if}
		{#if footnote}<p class="text-caption m-0 text-primary">{footnote}</p>{/if}
	</div>
	{@render trailing?.()}
{/snippet}

{#if onclick}
	<button type="button" {onclick} class="flex w-full items-center gap-3 p-3 text-start">{@render body()}</button>
{:else}
	<div class="flex w-full items-center gap-3 p-3">{@render body()}</div>
{/if}
