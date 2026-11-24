<script lang="ts">
	import { untrack } from 'svelte';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import DetailList from '$lib/components/card/DetailList.svelte';
	import type { DetailListRow } from '$lib/components/card/types';
	import TextField from '$lib/components/field/TextField.svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import AttachmentGallery from '$lib/components/media/AttachmentGallery.svelte';
	import MediaField from '$lib/components/media/MediaField.svelte';
	import type { PickedMedia, RemoteAttachment } from '$lib/components/media/types';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import ConfirmSheet from '$lib/components/sheet/ConfirmSheet.svelte';
	import { whenLabel, longDateLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import type { TaskItem } from '../tasks.svelte';

	/** Detail satu tugas; baris yang tidak punya nilai tidak ditampilkan, dan tombol yang tampil mengikuti hak akses pemakai. */
	let {
		task,
		submitting,
		submitError,
		onComplete,
		onAddAttachments,
		onFixNote,
		onRemoveAttachment,
		onEdit,
		onDelete,
		onOpenSource,
		onDismiss
	}: {
		task: TaskItem;
		submitting: boolean;
		submitError: string | null;
		onComplete: (note: string, media: PickedMedia[]) => void;
		onAddAttachments: (media: PickedMedia[]) => void;
		/** Mengganti catatan selesai tugas yang sudah dikirim. */
		onFixNote: (note: string) => void;
		onRemoveAttachment: (attachment: RemoteAttachment) => void;
		onEdit: () => void;
		onDelete: () => void;
		/** Membuka pengisian yang ditindaklanjuti tugas ini. */
		onOpenSource: () => void;
		onDismiss: () => void;
	} = $props();

	let note = $state('');
	let proof = $state<PickedMedia[]>([]);
	let extra = $state<PickedMedia[]>([]);
	// Catatan selesai yang sedang dibetulkan; dimulai dari yang tersimpan.
	let fixedNote = $state(untrack(() => task.doneNote ?? ''));
	const canChangeFiles = $derived(task.canEdit || task.canFix);
	let confirmDelete = $state(false);
	let deleting = $state(false);

	const performer = $derived(task.assigneeName);
	const photos = $derived(task.attachments.filter((item) => !item.isVideo).length);
	const videos = $derived(task.attachments.filter((item) => item.isVideo).length);

	const rows = $derived<DetailListRow[]>([
		{ label: t('tasks_detail_name'), value: task.title },
		{ label: t('tasks_detail_status'), valueContent: statusBadge },
		...(task.outletName ? [{ label: t('tasks_detail_outlet'), value: task.outletName }] : []),
		...(task.followUp
			? [{ label: t('tasks_detail_follow_up'), value: t('tasks_detail_follow_up_value', task.followUp.name, longDateLabel(task.followUp.day), task.followUp.number, task.followUp.total) }]
			: []),
		...(task.description ? [{ label: t('tasks_detail_description'), value: task.description }] : []),
		...(task.creatorName && task.creatorName !== task.assigneeName ? [{ label: t('tasks_detail_giver'), value: task.creatorName }] : []),
		...(performer ? [{ label: t('tasks_detail_performer'), value: performer }] : []),
		...(task.due ? [{ label: t('tasks_detail_due'), value: whenLabel(task.due) }] : []),
		...(task.doneAt ? [{ label: t('tasks_detail_done_at'), value: whenLabel(task.doneAt) }] : []),
		...(task.doneNote ? [{ label: t('tasks_detail_note'), value: task.doneNote }] : [])
	]);
</script>

{#snippet statusBadge()}
	<StatusBadge text={task.done ? t('tasks_filter_done') : t('tasks_filter_pending')} tone={task.done ? 'positive' : 'warning'} />
{/snippet}

<BottomSheet title={t('tasks_detail_title')} {onDismiss} dismissible={!submitting}>
	<div class="flex w-full flex-col gap-3">
		<DetailList {rows} />
		{#if task.followUp}
			<PrimaryButton text={t('tasks_source_open')} onclick={onOpenSource} enabled={!submitting} container="selected" content="primary" />
		{/if}
		<AttachmentGallery attachments={task.attachments} onRemove={canChangeFiles && !submitting ? onRemoveAttachment : undefined} />

		{#if task.canComplete}
			<TextField bind:value={note} label={t('tasks_complete_note')} enabled={!submitting} />
			<MediaField items={proof} onchange={(items) => (proof = items)} enabled={!submitting} existingPhotos={photos} existingVideos={videos} />
		{:else if canChangeFiles}
			{#if task.canFix}
				<TextField bind:value={fixedNote} label={t('tasks_complete_note')} enabled={!submitting} />
				{#if fixedNote.trim() !== (task.doneNote ?? '')}
					<PrimaryButton text={t('tasks_fix_note_submit')} onclick={() => onFixNote(fixedNote)} enabled={!submitting} />
				{/if}
			{/if}
			<MediaField items={extra} onchange={(items) => (extra = items)} enabled={!submitting} existingPhotos={photos} existingVideos={videos} />
			{#if extra.length > 0}
				<PrimaryButton
					text={t('tasks_attach_submit')}
					onclick={() => {
						onAddAttachments(extra);
						extra = [];
					}}
					enabled={!submitting}
				/>
			{/if}
		{/if}

		{#if submitError}<InlineMessage text={submitError} />{/if}

		{#if task.canComplete}
			<PrimaryButton
				text={t('tasks_complete_submit')}
				onclick={() => {
					deleting = false;
					onComplete(note, proof);
				}}
				enabled={proof.length > 0 && !submitting}
				loading={submitting && !deleting}
			/>
		{/if}
		{#if task.canEdit}
			<PrimaryButton text={t('tasks_edit_action')} onclick={onEdit} enabled={!submitting} container="selected" content="primary" />
		{/if}
		{#if task.canDelete}
			<PrimaryButton text={t('tasks_delete_action')} onclick={() => (confirmDelete = true)} enabled={!submitting} container="danger-container" content="on-danger-container" loading={submitting && deleting} />
		{/if}
	</div>
</BottomSheet>

{#if confirmDelete}
	<ConfirmSheet
		title={t('tasks_delete_action')}
		message={t('tasks_delete_message')}
		confirmLabel={t('tasks_delete_confirm')}
		onConfirm={() => {
			confirmDelete = false;
			deleting = true;
			onDelete();
		}}
		onDismiss={() => (confirmDelete = false)}
		destructive
		enabled={!submitting}
	/>
{/if}
