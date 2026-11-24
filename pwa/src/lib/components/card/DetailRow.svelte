<script lang="ts">
	import type { Snippet } from 'svelte';

	/** Pasangan label dan nilai; nilai berupa teks atau konten bebas (misalnya lencana). */
	let { label, value, valueContent }: { label: string; value?: string | null; valueContent?: Snippet } = $props();
</script>

<div class="flex w-full items-center gap-3 p-3">
	<p class="text-body m-0 flex-1 text-content-muted">{label}</p>
	{#if valueContent}
		{@render valueContent()}
	{:else if value != null}
		<p class="text-body m-0 flex-1 text-end text-content">{value}</p>
	{/if}
</div>
