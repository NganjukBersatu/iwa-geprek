<script lang="ts">
	import type { Snippet } from 'svelte';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import type { PickedPhoto } from '$lib/platform/photo';
	import PhotoField from './PhotoField.svelte';

	/** Formulir pengiriman berfoto yang seragam; [allowGallery] false memaksa foto dari kamera. */
	let {
		submitLabel,
		onSubmit,
		submitting = false,
		canSubmit = true,
		photoRequired = true,
		allowGallery = true,
		error = null,
		fields
	}: {
		submitLabel: string;
		onSubmit: (photo: Blob | null) => void;
		submitting?: boolean;
		canSubmit?: boolean;
		photoRequired?: boolean;
		allowGallery?: boolean;
		error?: string | null;
		fields?: Snippet;
	} = $props();

	let photo = $state<PickedPhoto | null>(null);
</script>

<div class="flex w-full flex-col gap-3">
	{@render fields?.()}
	<PhotoField {photo} onPicked={(picked) => (photo = picked)} enabled={!submitting} {allowGallery} />
	{#if error}<InlineMessage text={error} />{/if}
	<PrimaryButton
		text={submitLabel}
		onclick={() => onSubmit(photo?.blob ?? null)}
		enabled={(photo !== null || !photoRequired) && canSubmit && !submitting}
		loading={submitting}
	/>
</div>
