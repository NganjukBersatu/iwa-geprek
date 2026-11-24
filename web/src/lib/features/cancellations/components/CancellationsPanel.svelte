<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import DepositedDayWarning from '../../deposits/components/DepositedDayWarning.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import Skeleton from '$lib/components/skeleton/Skeleton.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import type { CancellationsState } from '../cancellations.svelte';
	import { cancellationText } from '$lib/text/cancellations';
	import { format } from '$lib/text/format';

	let { cancellations, allBranches }: { cancellations: CancellationsState; allBranches: boolean } = $props();
</script>

<Card flush>
	<CardHeader divided title={cancellationText.title} description={cancellationText.description} />

	{#if cancellations.error}
		<div class="p-4"><Banner tone="danger" icon="alert-triangle" title={cancellationText.loadFailedTitle}>{cancellations.error}</Banner></div>
	{:else if cancellations.loading && cancellations.items.length === 0}
		<SkeletonList rows={4} label={cancellationText.loading} />
	{:else if cancellations.items.length === 0}
		<Notice text={cancellationText.noRequests} />
	{:else}
		{#if cancellations.loading}<Skeleton class="h-1 w-full rounded-none" />{/if}
		<ul class="divide-y divide-slate-100">
			{#each cancellations.items as item (item.id)}
				<li>
					<button
						type="button"
						class="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-brand-page focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand tablet:px-5"
						onclick={() => cancellations.open(item)}
					>
						<span class="min-w-0">
							<span class="block text-sm font-semibold text-slate-800">
								{item.receipt_number ?? '—'} · {formatRupiah(item.order_total)}
								{#if allBranches}<span class="text-xs font-normal text-slate-500">· {item.outlet_name}</span>{/if}
							</span>
							<span class="block truncate text-xs text-slate-600">{item.items_summary}</span>
							<span class="block text-xs text-slate-500">{format(cancellationText.requestedBy, { cashier: item.cashier, requester: item.requested_by, time: formatDateTime(item.created_at) })}</span>
						</span>
						<i class="ti ti-chevron-right shrink-0 text-slate-400" aria-hidden="true"></i>
					</button>
				</li>
			{/each}
		</ul>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={cancellations.page} total={cancellations.total} unit="pengajuan" disabled={cancellations.loading} onchange={(page) => cancellations.setPage(page)} />
		</div>
	{/if}
</Card>

{#if cancellations.opened}
	{@const item = cancellations.opened}
	{@const confirming = cancellations.approving !== null}
	{@const busy = cancellations.busyId === item.id}
	<!-- Konfirmasi persetujuan tampil di modal yang sama, bukan modal kedua di atasnya (rules 6.18). -->
	<Modal
		open
		title={format(confirming ? cancellationText.approveTitleNamed : cancellationText.detailTitle, { order: item.receipt_number ?? '' })}
		description={confirming ? undefined : cancellationText.detailDescription}
		size="sm"
		{busy}
		onclose={() => cancellations.closeDetail()}
	>
		{#if confirming}
			<p class="text-sm leading-6 text-slate-700">
				{format(cancellationText.approveCancelNote, { order: item.receipt_number ?? '', amount: formatRupiah(item.order_total) })}
			</p>
			<DepositedDayWarning warning={cancellations.warning} />
			{#if cancellations.actionError}
				<p class="mt-3 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{cancellations.actionError}</p>
			{/if}
		{:else}
			<dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
				<dt class="text-slate-500">{cancellationText.value}</dt><dd class="font-semibold text-slate-800">{formatRupiah(item.order_total)}</dd>
				{#if allBranches}<dt class="text-slate-500">{cancellationText.branch}</dt><dd class="text-slate-800">{item.outlet_name}</dd>{/if}
				<dt class="text-slate-500">{cancellationText.orderItems}</dt><dd class="break-words text-slate-800">{item.items_summary}</dd>
				<dt class="text-slate-500">{cancellationText.cashier}</dt><dd class="text-slate-800">{item.cashier}</dd>
				<dt class="text-slate-500">{cancellationText.requested}</dt><dd class="text-slate-800">{format(cancellationText.requestedAt, { requester: item.requested_by, time: formatDateTime(item.created_at) })}</dd>
				<dt class="text-slate-500">{cancellationText.reason}</dt><dd class="break-words text-slate-800">{item.reason ?? cancellationText.noReason}</dd>
			</dl>
			{#if cancellations.actionError}
				<p class="mt-3 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{cancellations.actionError}</p>
			{/if}
		{/if}
		{#snippet footer()}
			{#if confirming}
				<CancelButton disabled={busy} onclick={() => cancellations.closeDialogs()} />
				<Button label={cancellationText.approveConfirm} variant="danger" disabled={busy || cancellations.warning.checking} onclick={() => void cancellations.confirmApprove()} />
			{:else}
				<Button label={cancellationText.reject} icon="x" disabled={busy} onclick={() => void cancellations.reject(item)} />
				<Button label={cancellationText.approve} icon="check" variant="danger" disabled={busy} onclick={() => cancellations.askApprove(item)} />
			{/if}
		{/snippet}
	</Modal>
{/if}
