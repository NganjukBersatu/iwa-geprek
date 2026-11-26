<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { Branch, BranchPeriod } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import { formatDate } from '$lib/date/range';
	import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
	import { periodLabel } from '$lib/features/branch-periods/period-label';
	import { live } from '$lib/live/live';
	import { branchDetailText as text } from '$lib/text/branch-detail';
	import { format } from '$lib/text/format';
	import BranchReadiness from './BranchReadiness.svelte';

	let { branch }: { branch: Branch } = $props();

	let running = $state<BranchPeriod | null>(null);
	let periodState = $state<'loading' | 'ready' | 'failed'>('loading');

	async function loadPeriod(): Promise<void> {
		try {
			const periods = await api.outlets.periods(branch.id);
			running = periods.find((period) => period.running) ?? periods[0] ?? null;
			periodState = 'ready';
		} catch {
			periodState = 'failed';
		}
	}

	onMount(() => {
		void loadPeriod();
		return live.on(['branch_periods'], () => void loadPeriod());
	});

	const plain = (value: string | null) => value || EMPTY_VALUE;
	const money = (value: string | null) => (value !== null ? formatRupiah(Number(value)) : EMPTY_VALUE);
</script>

{#snippet field(label: string, value: string)}
	<div class="min-w-0">
		<dt class="text-xs text-slate-500">{label}</dt>
		<dd class="break-words font-semibold text-slate-800">{value}</dd>
	</div>
{/snippet}

<div class="flex flex-col gap-4 tablet:gap-6">
	<BranchReadiness branchId={branch.id} />

	<Card>
		<CardHeader class="mb-4" title={text.summary.identity} description={text.summary.identityDescription} icon="building-store" />
		<dl class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
			{@render field(text.labels.code, plain(branch.code))}
			{@render field(text.labels.receiptNumber, plain(branch.receipt_number))}
			{@render field(text.labels.status, branch.is_active ? text.open : text.closed)}
			{@render field(text.summary.created, formatDate(branch.created_at.slice(0, 10)))}
		</dl>
	</Card>

	<Card>
		<CardHeader class="mb-4" title={text.period.title} description={text.period.description} icon="calendar" />
		{#if periodState === 'loading'}
			<p class="text-sm text-slate-500">{text.period.loading}</p>
		{:else if periodState === 'failed' || running === null}
			<p class="text-sm text-danger-700">{text.period.failed}</p>
		{:else}
			<dl class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
				{@render field(text.period.label, periodLabel(running))}
				{@render field(text.period.range, format(text.period.rangeValue, { from: formatDate(running.start), to: formatDate(running.end) }))}
			</dl>
		{/if}
	</Card>

	<Card>
		<CardHeader class="mb-4" title={text.summary.location} description={text.summary.locationDescription} icon="map-pin" />
		<dl class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
			{@render field(text.labels.point, branch.latitude !== null && branch.longitude !== null ? `${branch.latitude.toFixed(5)}, ${branch.longitude.toFixed(5)}` : text.notSet)}
			{@render field(text.labels.radius, format(text.radiusMeters, { meters: branch.attendance_radius_meters }))}
		</dl>
	</Card>

	<Card>
		<CardHeader class="mb-4" title={text.summary.money} description={text.summary.moneyDescription} icon="cash" />
		<dl class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
			{@render field(text.labels.cashFloat, money(branch.cash_float))}
			{@render field(text.labels.spendingFloat, money(branch.spending_float))}
		</dl>
	</Card>
</div>
