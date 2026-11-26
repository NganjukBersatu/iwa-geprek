<script lang="ts">
	import IconButton from '$lib/components/button/IconButton.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { formatTime } from '$lib/format/datetime';
	import { orderPath } from '$lib/nav/pages';
	import type { DashboardState } from '../dashboard.svelte';
	import { sessionColumns, type SessionKind } from '../columns';
	import { termText } from '$lib/text/terms';
	import { dashboardCardText } from '$lib/text/dashboard-cards';
	import { format } from '$lib/text/format';

	let { dashboard, kind }: { dashboard: DashboardState; kind: SessionKind } = $props();

	const sessions = $derived(dashboard.sessions);
	const title = $derived(
		kind === 'income' ? dashboardCardText.incomePerSession : kind === 'expense' ? dashboardCardText.expensePerSession : dashboardCardText.profitPerSession
	);
	const detailKind = (type: 'income' | 'expense'): boolean => kind === 'profit' || kind === type;

	const columns = $derived(sessionColumns(kind));
</script>

<Card padded={false}>
	<CardHeader
		divided
		{title}
		description={format(dashboardCardText.sessionsCaption, { count: sessions.rows.length, period: dashboard.periodLabel })}
	>
		{#snippet actions()}
			<IconButton icon="x" label={dashboardCardText.closePanel} onclick={() => (dashboard.panel = null)} />
		{/snippet}
	</CardHeader>

	{#if sessions.omitted > 0}
		<p class="border-b border-slate-100 px-4 py-2 text-xs text-warning-700 tablet:px-5">
			{format(dashboardCardText.oldestSessionsOmitted, { count: sessions.omitted })}
		</p>
	{/if}

	{#if sessions.rows.length === 0}
		<Notice text={dashboardCardText.noSessions} />
	{:else}
		<DataTable sort={sessions.sort} {columns} rows={sessions.rows} rowKey={(row) => row.id} trailing="nilai" onunfold={(row) => void sessions.unfold(row.id)}>
			{#snippet first(row)}
				<span class="flex flex-col">
					<span class="font-semibold text-slate-800 wrap-break-word">{row.cashier}</span>
					{#if row.end === null}<span><Badge tone="success">{termText.running}</Badge></span>{/if}
				</span>
			{/snippet}
			{#snippet detail(row)}
				{@const transactions = (sessions.details[row.id] ?? []).filter((item) => detailKind(item.kind))}
				{#if sessions.loadingId === row.id}
					<SkeletonList rows={3} label={dashboardCardText.detailsLoading} />
				{:else if sessions.detailError}
					<p class="py-2 text-xs text-danger-700">{sessions.detailError}</p>
				{:else if transactions.length === 0}
					<p class="py-2 text-xs text-slate-500">{dashboardCardText.noOrdersInSession}</p>
				{:else}
					<ul class="flex flex-col gap-0.5">
						{#each transactions as item, index (index)}
							<li>
								<svelte:element
									this={item.orderId ? 'a' : 'div'}
									href={item.orderId ? orderPath(row.id, item.orderId) : undefined}
									class="flex flex-wrap items-center gap-x-3 gap-y-1 rounded px-1 py-0.5 text-xs {item.orderId ? '-mx-1 hover:bg-brand-soft' : ''}"
								>
									<i class="ti {item.kind === 'income' ? 'ti-arrow-up text-brand' : 'ti-arrow-down text-danger-500'}" aria-hidden="true"></i>
									<span class="w-14 shrink-0 text-slate-500">{formatTime(item.time)}</span>
									<span class="min-w-0 basis-full truncate text-slate-600 tablet:flex-1 tablet:basis-auto">
										{item.description}
										{#if item.qty}<span class="text-slate-500">{format(dashboardCardText.timesMultiplier, { count: item.qty })}</span>{/if}
									</span>
									<span class="font-semibold {item.kind === 'income' ? 'text-brand' : 'text-danger-700'}">
										{item.kind === 'expense' ? '-' : ''}{formatRupiah(item.amount)}
									</span>
									{#if item.orderId}<i class="ti ti-chevron-right shrink-0 text-slate-400" aria-hidden="true"></i>{/if}
								</svelte:element>
							</li>
						{/each}
					</ul>
				{/if}
			{/snippet}
		</DataTable>
	{/if}
</Card>
