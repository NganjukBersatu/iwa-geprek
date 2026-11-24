<script lang="ts">
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import ConfirmSheet from '$lib/components/sheet/ConfirmSheet.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { t } from '$lib/text/t';
	import type { Batch } from '../batches';

	type Pending = 'none' | 'fix' | 'cancel' | 'delete';

	/** Yang bisa dilakukan pada pengisian yang sudah dikirim: perbaiki isinya, batalkan, atau hapus; tombol mengikuti hak dari server. */
	let {
		batch,
		submitting,
		error,
		onFix,
		onCancel,
		onDelete,
		onDismiss
	}: { batch: Batch; submitting: boolean; error: string | null; onFix: () => void; onCancel: () => void; onDelete: () => void; onDismiss: () => void } = $props();

	let pending = $state<Pending>('none');
	let confirming = $state<Pending>('none');
</script>

<BottomSheet title={batch.name} {onDismiss} dismissible={!submitting}>
	<div class="flex w-full flex-col gap-3">
		<AppText role="body" color="content-muted">{t('batch_manage_hint')}</AppText>
		{#if error}<InlineMessage text={error} />{/if}
		{#if batch.canFix}
			<PrimaryButton
				text={t('batch_fix_action')}
				onclick={() => {
					pending = 'fix';
					onFix();
				}}
				enabled={!submitting}
				loading={submitting && pending === 'fix'}
			/>
		{/if}
		{#if batch.canCancel}
			<PrimaryButton text={t('batch_cancel_action')} onclick={() => (confirming = 'cancel')} enabled={!submitting} loading={submitting && pending === 'cancel'} container="selected" content="primary" />
		{/if}
		{#if batch.canDelete}
			<PrimaryButton
				text={t('batch_delete_action')}
				onclick={() => (confirming = 'delete')}
				enabled={!submitting}
				loading={submitting && pending === 'delete'}
				container="danger-container"
				content="on-danger-container"
			/>
		{/if}
	</div>
</BottomSheet>

{#if confirming === 'cancel'}
	<ConfirmSheet
		title={t('batch_cancel_action')}
		message={t('batch_cancel_message')}
		confirmLabel={t('batch_cancel_confirm')}
		onConfirm={() => {
			confirming = 'none';
			pending = 'cancel';
			onCancel();
		}}
		onDismiss={() => (confirming = 'none')}
		enabled={!submitting}
	/>
{/if}
{#if confirming === 'delete'}
	<ConfirmSheet
		title={t('batch_delete_action')}
		message={t('batch_delete_message')}
		confirmLabel={t('batch_delete_confirm')}
		onConfirm={() => {
			confirming = 'none';
			pending = 'delete';
			onDelete();
		}}
		onDismiss={() => (confirming = 'none')}
		destructive
		enabled={!submitting}
	/>
{/if}
