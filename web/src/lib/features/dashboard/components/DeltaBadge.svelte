<script lang="ts">
	import type { Comparison, ComparisonMetric } from '$lib/api/types';
	import SummaryBadge from '$lib/components/card/SummaryBadge.svelte';
	import type { SummaryAccent } from '$lib/components/card/summary-accent';
	import { formatPercent, formatRupiah } from '$lib/format/currency';
	import { dashboardText } from '$lib/text/dashboard';

	let {
		metric,
		comparison,
		inverse = false,
		money = true
	}: {
		metric: ComparisonMetric | undefined;
		comparison: Comparison | null;
		inverse?: boolean;
		money?: boolean;
	} = $props();

	const text = dashboardText.delta;
	const up = $derived(Number(metric?.difference) > 0);
	const down = $derived(Number(metric?.difference) < 0);
	const good = $derived(inverse ? down : up);
	// Colour only says whether the change is better or worse; the card itself stays neutral.
	const accent = $derived<SummaryAccent>(up || down ? (good ? 'green' : 'red') : 'plain');
	const icon = $derived(up ? 'arrow-up-right' : down ? 'arrow-down-right' : 'minus');
	const shown = $derived(metric?.percent === null ? text.fresh : formatPercent(metric?.percent ?? 0));
	const title = $derived(
		metric && comparison ? `${comparison.comparison_label}: ${money ? formatRupiah(metric.previous) : Number(metric.previous)}` : undefined
	);
	// The badge colour follows its card, so screen readers get the direction and whether it is better or worse.
	const label = $derived(up || down ? `${up ? text.up : text.down} ${shown}, ${good ? text.improved : text.worsened}` : text.same);
</script>

{#if metric && comparison}
	<SummaryBadge {accent} {title} label={title ? `${label}. ${title}` : label}>
		<i class="ti ti-{icon} text-sm" aria-hidden="true"></i>
		{shown}
	</SummaryBadge>
{/if}
