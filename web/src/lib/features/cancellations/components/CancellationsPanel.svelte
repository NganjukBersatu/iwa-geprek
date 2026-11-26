<script lang="ts">
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import Skeleton from '$lib/components/skeleton/Skeleton.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import type { CancellationsState } from '../cancellations.svelte';
	import { cancellationText } from '$lib/text/cancellations';
	import { cancellationPath } from '$lib/nav/pages';
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
					<a
						href={cancellationPath(item.id)}
						class="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-brand-page focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand tablet:px-5"
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
					</a>
				</li>
			{/each}
		</ul>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={cancellations.page} total={cancellations.total} unit="pengajuan" disabled={cancellations.loading} onchange={(page) => cancellations.setPage(page)} />
		</div>
	{/if}
</Card>
