<script lang="ts">
	import { depositText } from '$lib/text/deposits';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { onMount } from 'svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import SummaryBadge from '$lib/components/card/SummaryBadge.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import BulkBar from '$lib/components/table/BulkBar.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import FilterButton from '$lib/components/filter/FilterButton.svelte';
	import FilterChips from '$lib/components/filter/FilterChips.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import { formatPercentPlain, formatRupiah } from '$lib/format/currency';
	import { live } from '$lib/live/live';
	import { SALES_TABLES } from '$lib/live/tables';
	import { loadBranchOptions } from '$lib/stores/branch';
	import { spotlight } from '$lib/motion/spotlight';
	import Reveal from '$lib/components/motion/Reveal.svelte';
	import { OverviewState } from '$lib/features/finance/overview.svelte';
	import DepositDialogs from '$lib/features/deposits/components/DepositDialogs.svelte';
	import DepositHistory from '$lib/features/deposits/components/DepositHistory.svelte';
	import DepositSummary from '$lib/features/deposits/components/DepositSummary.svelte';
	import OverviewChart from '$lib/features/finance/components/OverviewChart.svelte';
	import OverviewTable from '$lib/features/finance/components/OverviewTable.svelte';
	import QcPanel from '$lib/features/finance/components/QcPanel.svelte';
	import { QC_ANCHOR } from '$lib/nav/pages';
	import TransactionList from '$lib/features/finance/components/TransactionList.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { pageText } from '$lib/text/pages';
	import { format } from '$lib/text/format';

	const overview = new OverviewState();

	const data = $derived(overview.data);
	const rows = $derived(overview.rows);
	const deposits = overview.deposits;
	const withDeposits = $derived(deposits.canView);
	const depositTabs = $derived([
		{ key: 'overview', label: pageText.summary },
		{ key: 'riwayat', label: pageText.depositHistory, ...(deposits.data ? { count: deposits.deposits.length } : {}) }
	]);

	whenChanged(
		() => overview.query,
		(query) => {
			overview.transactions.focusDate = null;
			void overview.load(query);
		}
	);

	whenChanged(() => overview.tableKey, () => overview.reloadTables());

	function showTransactions(date: string): void {
		overview.transactions.focus(date);
		spotlight('daftar-transaksi');
	}

	onMount(() => {
		void loadBranchOptions().then((options) => overview.setBranches(options));
		return live.on(SALES_TABLES, () => void overview.refresh());
	});
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader title={pageText.financeOverviewTitle} description={pageText.financeOverviewDescription}>
		{#snippet actions()}
			<FilterButton filters={overview.filters} />
			{#if deposits.canView}
				<Button label={pageText.depositColumns} icon="columns-3" compact active={deposits.columns} onclick={() => deposits.setColumns(!deposits.columns)} />
				{#if deposits.canManage}
					<Button label={pageText.recordDeposit} icon="plus" variant="primary" compact onclick={() => deposits.openCreate()} />
					<MoreButton selection={deposits.selection} />
				{/if}
			{/if}
		{/snippet}
	</PageHeader>

	<FilterChips filters={overview.filters} />

	{#if deposits.canView}
		<Tabs tabs={depositTabs} label={pageText.summaryView} bind:value={deposits.tab} />
	{/if}

	{#if overview.error}
		<Banner tone="danger" icon="alert-triangle" title={pageText.summaryLoadFailedTitle}>
			{overview.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void overview.load(overview.query)} />
			{/snippet}
		</Banner>
	{:else if overview.loading && !data}
		<SkeletonPage label={format(pageText.overviewLoadingPeriod, { period: overview.periodLabel })} />
	{/if}

	{#if data && withDeposits && deposits.tab === 'riwayat'}
		<DepositSummary {deposits} />
		<DepositHistory {deposits} />
	{:else if data}
		<Reveal>
			<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
				<SummaryCard
					label={termText.income}
					caption={format(pageText.cashAndNonCash, { cash: formatRupiah(data.total.cash_income), nonCash: formatRupiah(data.total.non_cash_income) })}
					value={formatRupiah(data.total.income_total)}
					icon="wallet"
					accent="primary"
				/>
				<SummaryCard
					label={termText.expense}
					caption={format(pageText.cashAndNonCash, { cash: formatRupiah(data.total.cash_expense), nonCash: formatRupiah(data.total.non_cash_expense) })}
					value={formatRupiah(data.total.expense_total)}
					icon="shopping-cart"
					accent="accent"
				>
					{#snippet delta()}<SummaryBadge accent="accent">{formatPercentPlain(data.total.expense_percent)}</SummaryBadge>{/snippet}
				</SummaryCard>
				<SummaryCard
					label={termText.profit}
					caption={format(pageText.cashAndNonCash, { cash: formatRupiah(data.total.cash_profit), nonCash: formatRupiah(data.total.non_cash_profit) })}
					value={formatRupiah(data.total.profit_total)}
					icon="chart-line"
					accent="ink"
				>
					{#snippet delta()}<SummaryBadge accent="ink">{formatPercentPlain(data.total.profit_percent)}</SummaryBadge>{/snippet}
				</SummaryCard>
			</div>

			{#if withDeposits}
				<DepositSummary {deposits} />
			{/if}

			{#if rows.length > 1}
				<OverviewChart {overview} />
			{/if}

			<OverviewTable title={overview.tableTitle} rows={overview.tableRows} total={data.total} deposits={withDeposits ? deposits : null} />

			<p class="text-xs text-slate-500">
				{pageText.financeFootnote}
			</p>

			<div id={QC_ANCHOR}>
				<QcPanel {overview} onselectdate={showTransactions} />
			</div>

			<div id="daftar-transaksi">
				<TransactionList {overview} />
			</div>
		</Reveal>
	{/if}
</div>

{#if withDeposits}
	{#if deposits.canManage}
		<BulkBar selection={deposits.selection} actions={[{ label: depositText.recordDeposit, icon: 'cash', onclick: () => deposits.openCreate() }]} />
	{/if}
	<DepositDialogs {deposits} />
{/if}
