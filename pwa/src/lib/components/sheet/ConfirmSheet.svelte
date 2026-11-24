<script lang="ts">
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import { t } from '$lib/text/t';
	import BottomSheet from './BottomSheet.svelte';

	/** Konfirmasi tindakan yang tidak bisa diurungkan: pesan, tombol lanjut, dan tombol batal. */
	let {
		title,
		message,
		confirmLabel,
		onConfirm,
		onDismiss,
		destructive = false,
		enabled = true,
		confirmEnabled = true,
		dismissLabel = t('common_cancel')
	}: {
		title: string;
		message: string;
		confirmLabel: string;
		onConfirm: () => void;
		onDismiss: () => void;
		destructive?: boolean;
		enabled?: boolean;
		confirmEnabled?: boolean;
		dismissLabel?: string;
	} = $props();
</script>

<BottomSheet {title} {onDismiss} dismissible={enabled}>
	<div class="flex w-full flex-col gap-3">
		<p class="text-body m-0 text-content">{message}</p>
		<PrimaryButton text={confirmLabel} onclick={onConfirm} enabled={enabled && confirmEnabled} container={destructive ? 'danger' : 'primary'} />
		<PrimaryButton text={dismissLabel} onclick={onDismiss} {enabled} container="selected" content="primary" />
	</div>
</BottomSheet>
