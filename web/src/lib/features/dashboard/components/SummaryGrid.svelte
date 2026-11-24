<script lang="ts">
	import type { Snippet } from 'svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { unfold } from '$lib/motion/transitions';
	import type { DashboardState, PanelKey } from '../dashboard.svelte';
	import DeltaBadge from './DeltaBadge.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import { customerText } from '$lib/text/customers';
	import { termText } from '$lib/text/terms';
	import { dashboardCardText } from '$lib/text/dashboard-cards';
	import { format } from '$lib/text/format';

	let { dashboard, children }: { dashboard: DashboardState; children: Snippet<[Exclude<PanelKey, null>]> } = $props();

	// The panel opens under the row of the card pressed, so the other cards are not pushed down.
	const fourTilePanel: Record<Exclude<PanelKey, null>, string> = {
		income: 'order-3 tablet:order-5 laptop:order-9',
		expense: 'order-5 laptop:order-9',
		profit: 'order-7 tablet:order-9',
		customers: 'order-9'
	};
	// Five tiles: two a row on a tablet, three then two on a laptop, and one row on a wide screen.
	const fiveTilePanel: Record<Exclude<PanelKey, null>, string> = {
		income: 'order-3 tablet:order-5 laptop:order-6 monitor-kecil:order-9',
		expense: 'order-5 laptop:order-6 monitor-kecil:order-9',
		profit: 'order-6 tablet:order-7 laptop:order-6 monitor-kecil:order-9',
		customers: 'order-9'
	};
	const TOP_TILE = 'laptop:col-span-2 monitor-kecil:col-span-1';
	const BOTTOM_TILE = 'laptop:col-span-3 monitor-kecil:col-span-1';
	const rows = $derived(dashboard.chartRows);
	const caption = $derived(format(dashboardCardText.totalWithPeriod, { period: dashboard.periodLabel }));
	// A tile opens the list of sessions behind it only for an account that may see them.
	const opensDetail = $derived(dashboard.can('view_transaction_list'));
	// An account that sees all five tiles gets five columns on a wide screen, so no tile drops alone.
	const fiveTiles = $derived(dashboard.can('view_trend') && dashboard.can('view_summary'));
	const panelOrder = $derived(fiveTiles ? fiveTilePanel : fourTilePanel);
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 {fiveTiles ? 'laptop:grid-cols-6 monitor-kecil:grid-cols-5' : 'laptop:grid-cols-4'}">
	{#if dashboard.can('view_trend')}
	<SummaryCard
		label={termText.income}
		class={fiveTiles ? TOP_TILE : ''}
		{caption}
		value={formatRupiah(dashboard.totalIncome)}
		icon="wallet"
		accent="plain"
		expanded={dashboard.panel === 'income'}
		order={2}
		onclick={opensDetail ? () => dashboard.togglePanel('income') : undefined}
	>
		{#snippet delta()}<DeltaBadge metric={dashboard.comparison?.income} comparison={dashboard.comparison} />{/snippet}
	</SummaryCard>

	<SummaryCard
		label={termText.expense}
		class={fiveTiles ? TOP_TILE : ''}
		{caption}
		value={formatRupiah(dashboard.totalExpense)}
		icon="shopping-cart"
		accent="plain"
		expanded={dashboard.panel === 'expense'}
		order={4}
		onclick={opensDetail ? () => dashboard.togglePanel('expense') : undefined}
	>
		{#snippet delta()}<DeltaBadge metric={dashboard.comparison?.expense} comparison={dashboard.comparison} inverse />{/snippet}
	</SummaryCard>

	<SummaryCard
		label={termText.profit}
		class={fiveTiles ? TOP_TILE : ''}
		caption={dashboardCardText.incomeMinusExpense}
		value={formatRupiah(dashboard.totalProfit)}
		icon="chart-line"
		accent="plain"
		expanded={dashboard.panel === 'profit'}
		order={6}
		onclick={opensDetail ? () => dashboard.togglePanel('profit') : undefined}
	>
		{#snippet delta()}<DeltaBadge metric={dashboard.comparison?.profit} comparison={dashboard.comparison} />{/snippet}
	</SummaryCard>

	<SummaryCard
		label={customerText.averageTransaction}
		class={fiveTiles ? BOTTOM_TILE : ''}
		{caption}
		value={formatRupiah(dashboard.averageTransaction)}
		icon="receipt-2"
		accent="plain"
		order={7}
	/>
	{/if}

	{#if dashboard.can('view_summary')}
	<SummaryCard
		label={customerText.cardTitle}
		class={fiveTiles ? BOTTOM_TILE : ''}
		{caption}
		value={format(customerText.people, { count: dashboard.totalCustomers })}
		icon="users"
		accent="plain"
		expanded={dashboard.panel === 'customers'}
		order={8}
		onclick={dashboard.can('view_customer_figures') ? () => dashboard.togglePanel('customers') : undefined}
	>
		{#snippet delta()}<DeltaBadge metric={dashboard.comparison?.customers} comparison={dashboard.comparison} money={false} />{/snippet}
		{#snippet extra()}
			<span class="flex flex-wrap items-center gap-2">
				<Badge><i class="ti ti-user-plus" aria-hidden="true"></i>{format(customerText.newBadge, { count: dashboard.totalNewCustomers })}</Badge>
				<Badge><i class="ti ti-repeat" aria-hidden="true"></i>{format(customerText.repeatBadge, { count: dashboard.totalRepeatCustomers })}</Badge>
			</span>
			<span class="text-xs text-brand-muted">{format(customerText.averagePerPeriod, { count: dashboard.averageCustomers })}</span>
		{/snippet}
	</SummaryCard>
	{/if}

	{#if dashboard.panel}
		<div class="col-span-full {panelOrder[dashboard.panel]}" transition:unfold>
			{@render children(dashboard.panel)}
		</div>
	{/if}
</div>
