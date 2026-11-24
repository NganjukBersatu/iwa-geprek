<script lang="ts">
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import type { Tone } from '$lib/components/card/tone';

	type Row = { key: string; label: string; meta: string; value: string };

	let {
		title,
		description,
		icon,
		tone,
		rows,
		emptyText,
		ranked = false
	}: {
		title: string;
		description: string;
		icon: string;
		tone: Tone;
		rows: Row[];
		emptyText: string;
		ranked?: boolean;
	} = $props();
</script>

<Card>
	<CardHeader class="mb-5" {title} {description} {icon} {tone} />

	{#if rows.length === 0}
		<p class="text-sm text-slate-500">{emptyText}</p>
	{:else}
		<ul class="flex flex-col gap-3">
			{#each rows as row, index (row.key)}
				<li class="flex items-center gap-3">
					{#if ranked}
						<span class="flex size-6 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-xs font-semibold text-slate-500">{index + 1}</span>
					{/if}
					<span class="flex-1 truncate text-sm text-slate-600">{row.label}</span>
					<span class="shrink-0 text-xs text-slate-500">{row.meta}</span>
					<span class="shrink-0 text-sm font-semibold text-slate-800">{row.value}</span>
				</li>
			{/each}
		</ul>
	{/if}
</Card>
