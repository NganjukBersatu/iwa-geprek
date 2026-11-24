<script lang="ts">
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import type { Tone } from '$lib/components/card/tone';
	import { formatRupiah } from '$lib/format/currency';
	import { dashboardCardText } from '$lib/text/dashboard-cards';

	let {
		title,
		icon,
		tone,
		rows
	}: {
		title: string;
		icon: string;
		tone: Tone;
		rows: { label: string; value: number }[];
	} = $props();
</script>

<Card>
	<CardHeader class="mb-5" {title} description={dashboardCardText.basedOnActivePeriod} {icon} {tone} />
	<ul class="flex flex-col gap-3">
		{#each rows as row (row.label)}
			<li class="flex items-center justify-between gap-2">
				<span class="min-w-0 truncate text-sm text-slate-500">{row.label}</span>
				<span class="shrink-0 text-sm font-semibold text-slate-800">{formatRupiah(row.value)}</span>
			</li>
		{/each}
	</ul>
</Card>
