<script lang="ts">
	import type { LeaveStatus } from '$lib/api/types';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import Skeleton from '$lib/components/skeleton/Skeleton.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import type { Tone } from '$lib/components/card/tone';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import { formatDayMonth } from '$lib/date/range';
	import { LEAVE_STATUS_LABELS, type LeaveRequestsState } from '../leave-requests.svelte';
	import { termText } from '$lib/text/terms';
	import { leaveRequestText } from '$lib/text/leave-requests';
	import { format } from '$lib/text/format';

	let { leave }: { leave: LeaveRequestsState } = $props();

	const tone: Record<LeaveStatus, Tone> = { menunggu: 'warning', disetujui: 'success', ditolak: 'danger' };
	const typeLabel = { izin: leaveRequestText.leave, sakit: termText.sick } as const;
	const period = (start: string, end: string) => (start === end ? formatDayMonth(start) : `${formatDayMonth(start)} – ${formatDayMonth(end)}`);
</script>

<Card flush>
	<CardHeader divided title={leaveRequestText.title} description={leaveRequestText.description} />
	<ListSearch value={leave.search} placeholder={leaveRequestText.searchPlaceholder} label={leaveRequestText.search} onsearch={(query) => leave.setSearch(query)} />

	{#if leave.error}
		<div class="p-4"><Banner tone="danger" icon="alert-triangle" title={leaveRequestText.loadFailedTitle}>{leave.error}</Banner></div>
	{:else if leave.loading && leave.items.length === 0}
		<SkeletonList rows={4} label={leaveRequestText.loading} />
	{:else if leave.items.length === 0}
		<Notice text={leave.search ? leaveRequestText.noMatch : leaveRequestText.noRequests} />
	{:else}
		{#if leave.loading}<Skeleton class="h-1 w-full rounded-none" />{/if}
		<ul class="divide-y divide-slate-100">
			{#each leave.items as item (item.id)}
				<li class="flex flex-col gap-2 px-4 py-3 tablet:flex-row tablet:items-center tablet:justify-between tablet:px-5">
					<div class="min-w-0">
						<p class="text-sm font-semibold text-slate-800">{item.name || item.username} <span class="text-xs font-normal text-slate-500">· {item.role_name}</span></p>
						<p class="text-xs text-slate-600">{typeLabel[item.type]} · {period(item.start_date, item.end_date)}</p>
						<p class="break-words text-xs text-slate-500">{item.reason}</p>
						{#if item.attachment_url}
							<a href={item.attachment_url} target="_blank" rel="noopener" class="inline-flex items-center gap-1 text-xs font-semibold text-brand hover:underline"><i class="ti ti-paperclip" aria-hidden="true"></i>{leaveRequestText.viewAttachment}</a>
						{:else if item.attachment_link}
							<a href={item.attachment_link} target="_blank" rel="noopener" class="inline-flex items-center gap-1 text-xs font-semibold text-brand hover:underline"><i class="ti ti-link" aria-hidden="true"></i>{leaveRequestText.attachmentLink}</a>
						{/if}
						{#if item.decided_by}<p class="text-xs text-slate-500">{format(leaveRequestText.decidedBy, { name: item.decided_by })}</p>{/if}
					</div>
					<div class="flex shrink-0 flex-wrap items-center gap-2">
						<Badge tone={tone[item.status]}>{LEAVE_STATUS_LABELS[item.status]}</Badge>
						{#if item.status !== 'ditolak'}
							<Button label={leaveRequestText.reject} icon="x" variant="dangerSoft" small compact disabled={leave.busyId === item.id} onclick={() => void leave.decide(item, false)} />
						{/if}
						{#if item.status !== 'disetujui'}
							<Button label={leaveRequestText.approve} icon="check" variant="primary" small compact disabled={leave.busyId === item.id} onclick={() => void leave.decide(item, true)} />
						{/if}
						<DeleteButton small disabled={leave.busyId === item.id} onclick={() => leave.askRemove(item)} />
					</div>
				</li>
			{/each}
		</ul>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={leave.page} total={leave.total} unit="pengajuan" disabled={leave.loading} onchange={(page) => leave.setPage(page)} />
		</div>
	{/if}
</Card>

<ConfirmDialog open={leave.removing !== null} title={leaveRequestText.removeTitle} confirmLabel="Hapus" danger busy={leave.busy} error={leave.actionError} onconfirm={() => void leave.confirmRemove()} oncancel={() => leave.closeDialogs()}>
	{#if leave.removing?.status === 'disetujui'}
		{leaveRequestText.removeNote}
	{:else}
		{leaveRequestText.removeIrreversible}
	{/if}
</ConfirmDialog>
