<script lang="ts">
	import Badge from '$lib/components/card/Badge.svelte';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { ingredientCountText } from '$lib/text/ingredient-counts';

	/** Satu tampilan Selisih untuk lembar opname dan pengajuan: kosong, Sistem minus, Cocok, atau angka selisihnya. */
	let { difference, closing }: { difference: number | null; closing: string } = $props();
</script>

{#if difference === null}
	<span class="text-slate-300">{EMPTY_VALUE}</span>
{:else if Number(closing) < 0}
	<Badge tone="danger">{ingredientCountText.systemMinus}</Badge>
{:else if difference === 0}
	<Badge tone="success">{ingredientCountText.match}</Badge>
{:else}
	<span class="font-semibold {difference < 0 ? 'text-danger-700' : 'text-info-700'}">{difference > 0 ? '+' : ''}{formatNumber(difference)}</span>
{/if}
