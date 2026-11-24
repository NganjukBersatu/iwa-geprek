<script lang="ts">
	import IconButton from '$lib/components/button/IconButton.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { customerText } from '$lib/text/customers';
	import { format } from '$lib/text/format';
	import type { DashboardState } from '../dashboard.svelte';

	let { dashboard }: { dashboard: DashboardState } = $props();

	const customers = $derived(dashboard.customers);
	const report = $derived(customers.report);
	const average = $derived(dashboard.averageCustomers);

	// A day busier than the average by 15% or more counts as crowded, and one 15% lighter as quiet.
	function crowd(value: number): { label: string; tone: 'success' | 'danger' | 'neutral' } {
		const percent = average ? (value / average) * 100 : 100;
		if (percent >= 115) return { label: customerText.crowded, tone: 'success' };
		if (percent <= 85) return { label: customerText.quiet, tone: 'danger' };
		return { label: customerText.normal, tone: 'neutral' };
	}

	function changePage(page: number): void {
		customers.page = page;
		if (dashboard.appliedRange) void customers.load(dashboard.appliedRange);
	}

	whenChanged(
		() => dashboard.appliedRange,
		(range) => {
			if (range) void customers.load(range);
		}
	);
</script>

<Card padded={false}>
	<CardHeader
		divided
		title={customerText.panelTitle}
		description={report ? format(customerText.panelDescription, { total: report.total, visits: report.summary.visits, period: dashboard.periodLabel }) : dashboard.periodLabel}
	>
		{#snippet actions()}
			<IconButton icon="x" label={customerText.closePanel} onclick={() => (dashboard.panel = null)} />
		{/snippet}
	</CardHeader>

	{#if dashboard.chartRows.length > 1}
		<ul class="flex gap-2 overflow-x-auto border-b border-slate-100 px-4 py-3 tablet:px-5">
			{#each dashboard.chartRows as row (row.label)}
				{@const status = crowd(row.customers)}
				<li
					class="flex shrink-0 flex-col items-center rounded-lg border px-3 py-2 text-center {status.tone === 'success' ? 'border-success-200 bg-success-50' : status.tone === 'danger' ? 'border-danger-200 bg-danger-50' : 'border-slate-100 bg-slate-50'}"
					title={format(customerText.newOf, { new: row.newCustomers, repeat: row.repeatCustomers })}
				>
					<span class="text-xs text-slate-500">{row.label}</span>
					<span class="text-sm font-semibold text-slate-800">{row.customers}</span>
					<span class="text-xs {status.tone === 'success' ? 'text-success-700' : status.tone === 'danger' ? 'text-danger-700' : 'text-slate-500'}">{status.label}</span>
				</li>
			{/each}
		</ul>
	{/if}

	{#if customers.error}
		<div class="p-4 tablet:p-5">
			<Banner tone="danger" icon="alert-triangle" title={customerText.loadFailedTitle}>{customers.error}</Banner>
		</div>
	{:else if !report || customers.loading}
		<SkeletonList rows={5} avatar label={customerText.loading} />
	{:else if report.items.length === 0}
		<Notice text={customerText.empty} />
	{:else}
		<ul class="divide-y divide-slate-100">
			{#each report.items as item (item.customer_id)}
				<li class="flex items-center gap-3 px-4 py-4 tablet:gap-4 tablet:px-5">
					<span class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-brand">
						<i class="ti ti-user text-xl" aria-hidden="true"></i>
					</span>
					<span class="min-w-0 flex-1">
						<span class="flex flex-wrap items-center gap-1.5">
							<span class="truncate font-semibold text-slate-800">{item.name}</span>
							<Badge tone={item.is_new ? 'brand' : 'success'}>{item.is_new ? customerText.newLabel : customerText.repeatLabel}</Badge>
							{#if item.status !== 'active'}<Badge>{customerText.inactive}</Badge>{/if}
						</span>
						<span class="block truncate text-xs text-slate-500">{format(customerText.lastVisit, { contact: item.contact ?? customerText.noContact, time: formatDateTime(item.last_visit_at) })}</span>
						<span class="block text-xs text-slate-500 tablet:hidden">
							{format(customerText.visitsAndSpent, { visits: item.visit_count, spent: formatRupiah(item.total_spent), count: item.transaction_count })}
						</span>
					</span>
					<span class="hidden min-w-0 flex-1 tablet:block">
						<span class="block text-xs text-slate-500">{customerText.visits}</span>
						<span class="font-semibold text-slate-800">{format(customerText.visitsCount, { count: item.visit_count })}</span>
					</span>
					<span class="hidden min-w-0 flex-1 text-right tablet:block">
						<span class="block text-xs text-slate-500">{customerText.spent}</span>
						<span class="font-semibold text-slate-800">
							{formatRupiah(item.total_spent)}
							<span class="text-xs font-normal text-slate-500">{format(customerText.transactionsCount, { count: item.transaction_count })}</span>
						</span>
					</span>
				</li>
			{/each}
		</ul>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={report.page} total={report.total} unit={customerText.unit} disabled={customers.loading} onchange={changePage} />
		</div>
	{/if}
</Card>
