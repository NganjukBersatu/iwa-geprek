<script lang="ts">
	import type { Snippet } from 'svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import BottomSheet from './BottomSheet.svelte';

	/** Lembar formulir seragam: isian dari pemanggil, pesan galat, dan tombol simpan, yang tidak bisa ditutup selama [submitting]. */
	let {
		title,
		submitLabel,
		onSubmit,
		onDismiss,
		submitting = false,
		canSubmit = true,
		error = null,
		loadingOnSubmit = false,
		children
	}: {
		title: string;
		submitLabel: string;
		onSubmit: () => void;
		onDismiss: () => void;
		submitting?: boolean;
		canSubmit?: boolean;
		error?: string | null;
		loadingOnSubmit?: boolean;
		children: Snippet;
	} = $props();
</script>

<BottomSheet {title} {onDismiss} dismissible={!submitting}>
	<div class="flex w-full flex-col gap-3">
		{@render children()}
		{#if error}<InlineMessage text={error} />{/if}
		<PrimaryButton text={submitLabel} onclick={onSubmit} enabled={canSubmit && !submitting} loading={loadingOnSubmit && submitting} />
	</div>
</BottomSheet>
