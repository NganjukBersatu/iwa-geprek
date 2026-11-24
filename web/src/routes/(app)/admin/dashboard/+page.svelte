<script lang="ts">
	import { listText } from '$lib/text/lists';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { onMount } from 'svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Skeleton from '$lib/components/skeleton/Skeleton.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import FilterButton from '$lib/components/filter/FilterButton.svelte';
	import FilterChips from '$lib/components/filter/FilterChips.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { live } from '$lib/live/live';
	import { SALES_TABLES, STOCK_TABLES } from '$lib/live/tables';
	import { loadBranchOptions } from '$lib/stores/branch';
	import Reveal from '$lib/components/motion/Reveal.svelte';
	import { DashboardState } from '$lib/features/dashboard/dashboard.svelte';
	import { transactionColumns } from '$lib/features/finance/columns';
	import CashierCard from '$lib/features/dashboard/components/CashierCard.svelte';
	import PeriodTotalsCard from '$lib/features/dashboard/components/PeriodTotalsCard.svelte';
	import ProfitLossCard from '$lib/features/dashboard/components/ProfitLossCard.svelte';
	import CustomerPanel from '$lib/features/dashboard/components/CustomerPanel.svelte';
	import { syncBranchPeriod } from '$lib/features/report/branch-period.svelte';
	import SessionPanel from '$lib/features/dashboard/components/SessionPanel.svelte';
	import SummaryGrid from '$lib/features/dashboard/components/SummaryGrid.svelte';
	import TopListCard from '$lib/features/dashboard/components/TopListCard.svelte';
	import TrendCard from '$lib/features/dashboard/components/TrendCard.svelte';
	import { actionText } from '$lib/text/actions';
	import { pageText } from '$lib/text/pages';
	import { format } from '$lib/text/format';

	const dashboard = new DashboardState();

	const summary = $derived(dashboard.summary);
	// The first load shows a skeleton page; the cards below wait for data instead of flashing empty.
	const firstLoad = $derived(dashboard.loading && !dashboard.loaded);

	syncBranchPeriod(() => dashboard.filters);

	whenChanged(() => dashboard.query, (query) => void dashboard.load(query));
	whenChanged(() => dashboard.filters.get('cabang'), () => void dashboard.loadStock());

	onMount(() => {
		void loadBranchOptions().then((options) => dashboard.setBranches(options));
		const stopSales = live.on(SALES_TABLES, () => void dashboard.refresh());
		const stopStock = live.on(STOCK_TABLES, () => void dashboard.loadStock());
		return () => {
			stopSales();
			stopStock();
		};
	});
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader title={pageText.dashboardTitle} description={pageText.dashboardDescription}>
		{#snippet actions()}
			<FilterButton filters={dashboard.filters} />
			{#if dashboard.can('view_transaction_list')}
				<MoreButton exporter={{ title: pageText.exportTitles.transactions, columns: transactionColumns, rows: () => dashboard.exportRows() }} />
			{/if}
		{/snippet}
	</PageHeader>

	<FilterChips filters={dashboard.filters} />

	{#if dashboard.error}
		<Banner tone="danger" icon="alert-triangle" title={listText.reportLoadFailedTitle}>
			{dashboard.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void dashboard.load(dashboard.query)} />
			{/snippet}
		</Banner>
	{:else if firstLoad}
		<SkeletonPage label={format(pageText.reportLoadingPeriod, { period: dashboard.periodLabel })} />
	{:else if dashboard.loading}
		<Skeleton class="h-1 w-full rounded-full" />
	{/if}

	{#if !firstLoad}
		<Reveal>
			<SummaryGrid {dashboard}>
				{#snippet children(panel)}
					{#if panel === 'customers'}
						<CustomerPanel {dashboard} />
					{:else}
						<SessionPanel {dashboard} kind={panel} />
					{/if}
				{/snippet}
			</SummaryGrid>

			{#if dashboard.can('view_trend')}
				<TrendCard {dashboard} />

				<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2">
					<PeriodTotalsCard title={pageText.incomeSummary} icon="arrow-up" tone="brand" rows={dashboard.chartRows.map((row) => ({ label: row.label, value: row.income }))} />
					<PeriodTotalsCard title={pageText.expenseSummary} icon="arrow-down" tone="accent" rows={dashboard.chartRows.map((row) => ({ label: row.label, value: row.expense }))} />
				</div>
			{/if}

			{#if dashboard.cashiers && dashboard.cashiers.cashiers.length > 0}
				<CashierCard cashiers={dashboard.cashiers.cashiers} sort={dashboard.cashierSort} />
			{/if}

			<ProfitLossCard {dashboard} />

			{#if summary}
				<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2">
					<TopListCard
						title={pageText.bestSellingMenus}
						description={format(pageText.transactionsWithVoided, { count: summary.sales.transaction_count, voided: summary.sales.voided_count > 0 ? ` · ${summary.sales.voided_count} dibatalkan` : '' })}
						icon="star"
						tone="accent"
						ranked
						emptyText="Belum ada transaksi di periode ini."
						rows={summary.sales.top_items.map((menu) => ({
							key: menu.menu_item_id ?? menu.name,
							label: menu.name,
							meta: `${menu.qty}x`,
							value: formatRupiah(menu.total)
						}))}
					/>
					<TopListCard
						title={pageText.worstSellingMenus}
						description={format(pageText.transactionsWithVoided, { count: summary.sales.transaction_count, voided: summary.sales.voided_count > 0 ? ` · ${summary.sales.voided_count} dibatalkan` : '' })}
						icon="trending-down"
						tone="info"
						ranked
						emptyText="Belum ada transaksi di periode ini."
						rows={summary.sales.bottom_items.map((menu) => ({
							key: menu.menu_item_id ?? menu.name,
							label: menu.name,
							meta: `${menu.qty}x`,
							value: formatRupiah(menu.total)
						}))}
					/>
					<TopListCard
						title={pageText.largestExpenses}
						description={format(pageText.cashAndOther, { cash: formatRupiah(summary.expenses.drawer_cash_total), other: formatRupiah(summary.expenses.other_funds_total) })}
						icon="receipt"
						tone="brand"
						emptyText="Belum ada pengeluaran tercatat di periode ini."
						rows={summary.expenses.by_item.slice(0, 8).map((item) => ({
							key: item.item_name,
							label: item.item_name,
							meta: `${item.frequency}x`,
							value: formatRupiah(item.total)
						}))}
					/>
				</div>
			{/if}
		</Reveal>
	{/if}
</div>
