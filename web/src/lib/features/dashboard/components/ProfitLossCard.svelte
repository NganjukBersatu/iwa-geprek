<script lang="ts">
	import { access } from '$lib/auth/access.svelte';
	import { PAGES } from '$lib/nav/pages';
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import MetricTile from '$lib/components/card/MetricTile.svelte';
	import { formatNumber, formatRupiah } from '$lib/format/currency';
	import type { DashboardState } from '../dashboard.svelte';
	import { termText } from '$lib/text/terms';
	import { dashboardCardText } from '$lib/text/dashboard-cards';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	let { dashboard }: { dashboard: DashboardState } = $props();

	let detail = $state(false);

	const report = $derived(dashboard.profitLoss);
	const inventory = $derived(dashboard.inventory);

	function percent(value: string | null, suffix = ''): string {
		return value === null ? '—' : `${formatNumber(value, 1)}%${suffix}`;
	}
</script>

{#if report}
	{@const loss = Number(report.net_profit) < 0}
	<Card>
		<CardHeader
			class="mb-4"
			title={dashboardCardText.profitAndLoss}
			description={format(dashboardCardText.netProfitFormula, { period: dashboard.periodLabel })}
		>
			{#snippet actions()}
				<Button label={detail ? dashboardCardText.closeDetails : dashboardCardText.details} onclick={() => (detail = !detail)} />
			{/snippet}
		</CardHeader>

		<div class="grid grid-cols-1 gap-3 tablet:grid-cols-2 laptop:grid-cols-4">
			<MetricTile tone="brand" label={termText.revenue} value={formatRupiah(report.revenue)} note="{report.transaction_count} transaksi" />
			<MetricTile label={dashboardCardText.costOfGoodsSold} value={formatRupiah(report.cost_of_goods_sold)} note="laba kotor {percent(report.gross_margin_percent)}" />
			<MetricTile tone="warning" label={dashboardCardText.operatingCost} value={formatRupiah(report.operating_expenses)} note="yang tercatat di Pengeluaran, selain belanja bahan" />
			<MetricTile
				tone={loss ? 'danger' : 'success'}
				label={dashboardCardText.netProfit}
				value={formatRupiah(report.net_profit)}
				note={report.net_margin_percent === null ? '—' : format(dashboardCardText.ofRevenue, { percent: percent(report.net_margin_percent) })}
				negative={loss}
			/>
		</div>

		{#if report.orders_without_lines > 0}
			<p class="mt-3 rounded-lg bg-warning-50 px-3 py-2 text-xs text-warning-700">
				<i class="ti ti-alert-triangle" aria-hidden="true"></i>
				<RichText template={dashboardCardText.ordersWithoutLinesNote} values={{ count: formatNumber(report.orders_without_lines, 0), revenue: formatRupiah(report.revenue_without_lines), effect: dashboardCardText.higherThanActual }} />
			</p>
		{/if}
		{#if report.lines_without_cost > 0}
			<p class="mt-3 rounded-lg bg-warning-50 px-3 py-2 text-xs text-warning-700">
				<i class="ti ti-alert-triangle" aria-hidden="true"></i>
				<RichText template={dashboardCardText.costIncompleteNote} values={{ count: report.lines_without_cost, examples: report.items_without_cost.length
					? `: ${report.items_without_cost.slice(0, 6).join(', ')}${report.items_without_cost.length > 6 ? ', …' : ''}`
					: '', effect: dashboardCardText.higherThanActual }} />
			</p>
		{/if}

		{#if detail}
			<div class="mt-4 grid gap-4 laptop:grid-cols-[1fr_20rem]">
				<div class="flex flex-col gap-3">
					<FigureList
						figures={[
							{ label: dashboardCardText.revenueValid, value: formatRupiah(report.revenue) },
							{ label: dashboardCardText.minusCostOfGoods, value: formatRupiah(report.cost_of_goods_sold) },
							{ label: dashboardCardText.grossProfitLine, value: formatRupiah(report.gross_profit), emphasis: 'total' },
							{ label: dashboardCardText.minusWaste, value: formatRupiah(report.waste) },
							{ label: dashboardCardText.minusRnd, value: formatRupiah(report.rnd) },
							{ label: dashboardCardText.minusCountDifference, value: formatRupiah(report.count_difference) },
							{
								label: dashboardCardText.minusOperating,
								value: formatRupiah(report.operating_expenses),
								note: dashboardCardText.operatingNote
							},
							{ label: dashboardCardText.netProfitLine, value: formatRupiah(report.net_profit), emphasis: loss ? 'bad' : 'good' }
						]}
					/>
					<p class="text-xs text-slate-500">
						<RichText template={dashboardCardText.cashFlowComparison} values={{ label: dashboardCardText.cashFlow, purchases: formatRupiah(report.ingredient_purchases), amount: formatRupiah(report.cash_flow) }} />
					</p>
				</div>

				{#if dashboard.can('view_inventory_value')}
				<div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
					<p class="text-xs font-semibold text-slate-500">{dashboardCardText.idleMoney}</p>
					{#if inventory}
						<p class="mt-1 text-xl font-semibold text-slate-800">{formatRupiah(inventory.ingredient_stock_value)}</p>
						<p class="text-xs text-slate-500">{dashboardCardText.inventoryValueNote}</p>
						{#if inventory.dormant_count > 0}
							<p class="mt-3 rounded-lg bg-warning-50 px-3 py-2 text-xs text-warning-700">
								<RichText template={dashboardCardText.dormantNote} values={{ count: inventory.dormant_count, value: formatRupiah(inventory.dormant_value) }} />
								{#if access.opens(PAGES.stockTurnoverReport.screen)}<a href={PAGES.stockTurnoverReport.path} class="font-semibold underline">{format(dashboardCardText.seeListAt, { page: PAGES.stockTurnoverReport.label })}</a>.{/if}
							</p>
						{:else}
							<p class="mt-3 text-xs text-slate-500">{dashboardCardText.allIngredientsMoving}</p>
						{/if}
					{:else if dashboard.inventoryFailed}
						<p class="mt-1 text-sm text-danger-700">{dashboardCardText.inventoryValueLoadFailed}</p>
					{:else}
						<p class="mt-2 text-slate-500"><i class="ti ti-loader-2 animate-spin" aria-hidden="true"></i></p>
					{/if}
				</div>
				{/if}
			</div>
		{/if}
	</Card>
{/if}
