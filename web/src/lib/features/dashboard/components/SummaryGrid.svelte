<script lang="ts">
	import type { Snippet } from 'svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { unfold } from '$lib/motion/transitions';
	import type { DashboardState, PanelKey } from '../dashboard.svelte';
	import DeltaBadge from './DeltaBadge.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import { termText } from '$lib/text/terms';
	import { dashboardCardText } from '$lib/text/dashboard-cards';
	import { format } from '$lib/text/format';

	let { dashboard, children }: { dashboard: DashboardState; children: Snippet<[Exclude<PanelKey, null>]> } = $props();

	// Panel terbuka di bawah baris kartu yang ditekan, supaya kartu lain tidak terdorong ke bawah.
	const fourTilePanel: Record<Exclude<PanelKey, null>, string> = {
		income: 'order-3 tablet:order-5 laptop:order-9',
		expense: 'order-5 laptop:order-9',
		profit: 'order-7 tablet:order-9'
	};
	// Lima ubin: dua per baris di tablet, tiga lalu dua di laptop, dan satu baris di layar lebar.
	const fiveTilePanel: Record<Exclude<PanelKey, null>, string> = {
		income: 'order-3 tablet:order-5 laptop:order-6 monitor-kecil:order-9',
		expense: 'order-5 laptop:order-6 monitor-kecil:order-9',
		profit: 'order-6 tablet:order-7 laptop:order-6 monitor-kecil:order-9'
	};
	const TOP_TILE = 'laptop:col-span-2 monitor-kecil:col-span-1';
	const BOTTOM_TILE = 'laptop:col-span-3 monitor-kecil:col-span-1';
	// Ubin hanya membuka daftar di baliknya bagi akun yang boleh melihat daftar itu.
	const opensDetail = $derived(dashboard.can('view_transaction_list'));
	// Akun yang melihat kelima ubin mendapat lima kolom di layar lebar, supaya tidak ada satu ubin yang turun sendirian.
	const fiveTiles = $derived(dashboard.can('view_trend') && dashboard.can('view_summary'));
	const panelOrder = $derived(fiveTiles ? fiveTilePanel : fourTilePanel);
	const averageCaption = $derived(format(dashboardCardText.averageCaption, { income: formatRupiah(dashboard.totalIncome), count: dashboard.visitors }));
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 {fiveTiles ? 'laptop:grid-cols-6 monitor-kecil:grid-cols-5' : 'laptop:grid-cols-4'}">
	{#if dashboard.can('view_trend')}
		<SummaryCard
			label={termText.income}
			class={fiveTiles ? TOP_TILE : ''}
			caption={dashboardCardText.incomeCaption}
			value={formatRupiah(dashboard.totalIncome)}
			icon="wallet"
			accent="plain"
			expanded={dashboard.opens('income')}
			order={2}
			onclick={opensDetail ? () => dashboard.togglePanel('income') : undefined}
		>
			{#snippet delta()}<DeltaBadge metric={dashboard.comparison?.income} comparison={dashboard.comparison} />{/snippet}
		</SummaryCard>

		<SummaryCard
			label={termText.expense}
			class={fiveTiles ? TOP_TILE : ''}
			caption={dashboardCardText.expenseCaption}
			value={formatRupiah(dashboard.totalExpense)}
			icon="shopping-cart"
			accent="plain"
			expanded={dashboard.opens('expense')}
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
			expanded={dashboard.opens('profit')}
			order={6}
			onclick={opensDetail ? () => dashboard.togglePanel('profit') : undefined}
		>
			{#snippet delta()}<DeltaBadge metric={dashboard.comparison?.profit} comparison={dashboard.comparison} />{/snippet}
		</SummaryCard>

		<SummaryCard
			label={dashboardCardText.averagePerReceipt}
			class={fiveTiles ? BOTTOM_TILE : ''}
			caption={averageCaption}
			value={formatRupiah(dashboard.averageTransaction)}
			icon="receipt-2"
			accent="plain"
			expanded={dashboard.opens('average')}
			order={7}
			onclick={opensDetail ? () => dashboard.togglePanel('income', 'average') : undefined}
		>
			{#snippet delta()}<DeltaBadge metric={dashboard.comparison?.average_transaction} comparison={dashboard.comparison} />{/snippet}
		</SummaryCard>
	{/if}

	{#if dashboard.can('view_summary')}
		<!-- shortcut: angka dan panel pelanggan disembunyikan karena nama ketikan kasir belum menjadi data pelanggan, buka lagi setelah alur pelanggan kasir dibenahi. -->
		<SummaryCard
			label={dashboardCardText.visitors}
			class={fiveTiles ? BOTTOM_TILE : ''}
			caption={dashboardCardText.visitorsCaption}
			value={format(dashboardCardText.receiptsCount, { count: dashboard.visitors })}
			icon="users"
			accent="plain"
			order={8}
		>
			{#snippet delta()}<DeltaBadge metric={dashboard.comparison?.transactions} comparison={dashboard.comparison} money={false} />{/snippet}
		</SummaryCard>
	{/if}

	{#if dashboard.panel}
		<div class="col-span-full {panelOrder[dashboard.panel]}" transition:unfold>
			{@render children(dashboard.panel)}
		</div>
	{/if}
</div>

<p class="mt-3 flex items-start gap-1.5 text-xs text-slate-500">
	<i class="ti ti-info-circle mt-0.5 text-sm" aria-hidden="true"></i>
	{dashboardCardText.businessDayNote}
</p>
