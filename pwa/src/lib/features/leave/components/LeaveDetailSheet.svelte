<script lang="ts">
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import DetailList from '$lib/components/card/DetailList.svelte';
	import type { DetailListRow } from '$lib/components/card/types';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import PhotoPair from '$lib/components/media/PhotoPair.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import ConfirmSheet from '$lib/components/sheet/ConfirmSheet.svelte';
	import { t } from '$lib/text/t';
	import { leaveRangeLabel, leaveStatusLabel, leaveStatusTone, leaveTypeLabel, type LeaveRequest } from '../leave.svelte';

	/** Detail satu pengajuan; yang masih menunggu bisa dibatalkan oleh pemohonnya. */
	let { request, working, error, onCancel, onDismiss }: { request: LeaveRequest; working: boolean; error: string | null; onCancel: () => void; onDismiss: () => void } = $props();

	let confirming = $state(false);

	const attachmentUrl = $derived(request.attachmentUrl);
	const isPdf = $derived(attachmentUrl?.split('?')[0]?.toLowerCase().endsWith('.pdf') ?? false);

	const rows = $derived<DetailListRow[]>([
		{ label: t('leave_detail_type'), value: leaveTypeLabel(request.type) },
		{ label: t('leave_detail_date'), value: leaveRangeLabel(request) },
		{ label: t('leave_detail_reason'), value: request.reason },
		{ label: t('leave_detail_status'), valueContent: statusBadge },
		...(request.decidedBy ? [{ label: t('leave_detail_decided_by'), value: request.decidedBy }] : []),
		...(request.managerNote ? [{ label: t('leave_detail_note'), value: request.managerNote }] : []),
		...(request.attachmentLink ? [{ label: t('leave_detail_link'), value: request.attachmentLink }] : []),
		...(isPdf ? [{ label: t('leave_attachment'), value: t('leave_attachment_pdf') }] : [])
	]);
</script>

{#snippet statusBadge()}<StatusBadge text={leaveStatusLabel(request.status)} tone={leaveStatusTone(request.status)} />{/snippet}

<BottomSheet title={t('leave_detail_title')} {onDismiss}>
	<div class="flex w-full flex-col gap-3">
		<DetailList {rows} />
		{#if attachmentUrl && !isPdf}
			<PhotoPair first={{ url: attachmentUrl, caption: t('leave_attachment') }} second={{ url: null, caption: '' }} />
		{/if}
		{#if error}<InlineMessage text={error} />{/if}
		{#if request.status === 'pending'}
			<div class="pt-2"><PrimaryButton text={t('leave_cancel_action')} onclick={() => (confirming = true)} container="danger" loading={working} /></div>
		{/if}
	</div>
</BottomSheet>

{#if confirming}
	<ConfirmSheet
		title={t('leave_cancel_title')}
		message={t('leave_cancel_message')}
		confirmLabel={t('leave_cancel_confirm')}
		onConfirm={() => {
			onCancel();
			confirming = false;
		}}
		onDismiss={() => (confirming = false)}
		destructive
		enabled={!working}
	/>
{/if}
