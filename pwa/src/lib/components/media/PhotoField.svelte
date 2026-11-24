<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import SourceButton from '$lib/components/button/SourceButton.svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import { pickPhoto, type PickedPhoto } from '$lib/platform/photo';
	import { t } from '$lib/text/t';

	/** Rasio lebar : tinggi foto orang (selfie absen); foto kecil selalu dipotong ke rasio ini. */
	const PHOTO_ASPECT_RATIO = 3 / 4;

	/** Kolom foto: pratinjau pilihan, tombol kamera dan galeri (galeri bisa dimatikan lewat [allowGallery]), dengan hasil dikonversi otomatis. */
	let {
		photo,
		onPicked,
		enabled = true,
		allowGallery = true
	}: { photo: PickedPhoto | null; onPicked: (photo: PickedPhoto) => void; enabled?: boolean; allowGallery?: boolean } = $props();

	const preview = $derived(photo ? URL.createObjectURL(photo.blob) : null);

	$effect(() => {
		const url = preview;
		return () => {
			if (url) URL.revokeObjectURL(url);
		};
	});

	let unreadable = $state(false);

	async function pick(source: 'camera' | 'gallery'): Promise<void> {
		unreadable = false;
		const reading = await pickPhoto(source);
		if (reading.kind === 'picked') onPicked(reading.photo);
		else if (reading.kind === 'unreadable') unreadable = true;
	}
</script>

<div class="flex w-full flex-col gap-2">
	{#if preview}
		<img src={preview} alt="" class="w-full rounded-field border border-divider object-cover" use:dynamicStyle={{ 'aspect-ratio': PHOTO_ASPECT_RATIO }} />
	{/if}
	<div class="flex gap-2">
		<div class="flex-1"><SourceButton label={t('photo_camera')} icon="Camera" onclick={() => void pick('camera')} {enabled} /></div>
		{#if allowGallery}
			<div class="flex-1"><SourceButton label={t('photo_gallery')} icon="Photo" onclick={() => void pick('gallery')} tone="library" {enabled} /></div>
		{/if}
	</div>
	{#if unreadable}<InlineMessage text={t('web_photo_unreadable')} />{/if}
</div>
