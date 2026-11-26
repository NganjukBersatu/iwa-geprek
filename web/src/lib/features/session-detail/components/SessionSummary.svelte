<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import type { SessionHistoryRow } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { drawerFigures, outsideFigures } from '../../session-history/reconciliation';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { format } from '$lib/text/format';

	let { row }: { row: SessionHistoryRow } = $props();

	const hasRevenue = $derived(Number(row.revenue) > 0);
	const cashShare = $derived(Number(row.revenue) > 0 ? Math.round((Number(row.cash_revenue) / Number(row.revenue)) * 100) : 0);
</script>

<Card flush>
	<div class="flex flex-col gap-1.5 border-b border-brand-line bg-brand-soft p-4 tablet:p-5">
		<span class="text-xs font-medium text-brand-deep">{sessionDetailText.sessionRevenue}</span>
		<span class="text-2xl font-semibold text-slate-800">{formatRupiah(row.revenue)}</span>
		<div class="mt-2 flex h-3 w-full gap-0.5 overflow-hidden rounded-full bg-brand-tint" role="img" aria-label={format(sessionDetailText.cashSharePercent, { cash: cashShare, nonCash: 100 - cashShare })}>
			{#if hasRevenue}
				<div class="h-full bg-brand" use:dynamicStyle={{ width: `${cashShare}%` }}></div>
				<div class="h-full flex-1 bg-brand-accent"></div>
			{/if}
		</div>
		<span class="mt-1 flex flex-wrap justify-between gap-x-3 gap-y-1 text-xs font-medium text-brand-ink">
			<span class="inline-flex items-center gap-1.5"><span class="size-2.5 rounded-sm bg-brand" aria-hidden="true"></span>{format(sessionDetailText.cashPercentLabel, { percent: cashShare })}</span>
			<span class="inline-flex items-center gap-1.5"><span class="size-2.5 rounded-sm bg-brand-accent" aria-hidden="true"></span>{format(sessionDetailText.nonCashPercentLabel, { percent: hasRevenue ? 100 - cashShare : 0 })}</span>
		</span>
		<span class="mt-1 text-xs text-brand-deep">{format(sessionDetailText.expenseLabel, { amount: formatRupiah(row.expenses) })}</span>
	</div>
	<div class="border-b border-slate-100 p-4 tablet:p-5">
		<FigureList title={sessionDetailText.drawerCash} figures={drawerFigures(row)} />
	</div>
	<div class="p-4 tablet:p-5">
		<FigureList title={sessionDetailText.outsideDrawer} figures={outsideFigures(row)} />
	</div>
</Card>
