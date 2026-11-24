<script lang="ts">
	import SourceButton from '$lib/components/button/SourceButton.svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import { chooseFile, pickPhoto, toUploadJpeg } from '$lib/platform/photo';
	import { MEDIA_MAX_PHOTOS, MEDIA_MAX_VIDEOS, VIDEO_MAX_BYTES } from '$lib/platform/upload-limits';
	import { pickVideo, videoFrom } from '$lib/platform/video';
	import { t } from '$lib/text/t';
	import MediaTile from './MediaTile.svelte';
	import type { PickedMedia } from './types';

	const BYTES_PER_MEGABYTE = 1024 * 1024;
	const PHOTO_MIME = 'image/jpeg';
	const PHOTO_NAME = 'foto.jpg';
	const VIDEO_NAME_PREFIX = 'video';

	/** Kolom lampiran: deretan pratinjau yang bisa dihapus, lalu tombol Kamera (foto atau video) dan Galeri (foto dan video sekaligus); [existingPhotos] dan [existingVideos] memperhitungkan lampiran yang sudah tersimpan. */
	let {
		items,
		onchange,
		enabled = true,
		existingPhotos = 0,
		existingVideos = 0
	}: { items: readonly PickedMedia[]; onchange: (items: PickedMedia[]) => void; enabled?: boolean; existingPhotos?: number; existingVideos?: number } = $props();

	let tooLarge = $state(false);
	let unreadable = $state(false);
	let choosingCamera = $state(false);
	let limitReached = $state(false);

	const count = (kind: PickedMedia['kind']) => items.filter((item) => item.kind === kind).length;
	const canAddPhoto = $derived(enabled && existingPhotos + count('photo') < MEDIA_MAX_PHOTOS);
	const canAddVideo = $derived(enabled && existingVideos + count('video') < MEDIA_MAX_VIDEOS);

	const previews = $derived(items.map((item) => (item.kind === 'photo' ? URL.createObjectURL(item.blob) : null)));
	$effect(() => {
		const urls = previews;
		return () => urls.forEach((url) => url && URL.revokeObjectURL(url));
	});

	function hasRoom(kind: PickedMedia['kind']): boolean {
		return kind === 'photo' ? existingPhotos + count('photo') < MEDIA_MAX_PHOTOS : existingVideos + count('video') < MEDIA_MAX_VIDEOS;
	}

	// Satu pintu penambahan: lampiran melewati batas ditolak dengan pesan, bukan hilang diam-diam.
	function add(media: PickedMedia): void {
		tooLarge = false;
		unreadable = false;
		limitReached = !hasRoom(media.kind);
		if (!limitReached) onchange([...items, media]);
	}

	const photoMedia = (blob: Blob): PickedMedia => ({ kind: 'photo', blob, mimeType: PHOTO_MIME, fileName: PHOTO_NAME });

	async function takePhoto(): Promise<void> {
		choosingCamera = false;
		unreadable = false;
		const reading = await pickPhoto('camera');
		if (reading.kind === 'picked') add(photoMedia(reading.photo.blob));
		else if (reading.kind === 'unreadable') unreadable = true;
	}

	async function recordVideo(): Promise<void> {
		choosingCamera = false;
		unreadable = false;
		const reading = await pickVideo('camera');
		if (reading.kind === 'too-large') tooLarge = true;
		else if (reading.kind === 'picked') add({ kind: 'video', blob: reading.video.blob, mimeType: reading.video.mimeType, fileName: VIDEO_NAME_PREFIX + reading.video.extension });
	}

	/** Pemilih galeri tunggal untuk foto dan video: jenis berkas dikenali dari pilihannya. */
	async function pickFromGallery(): Promise<void> {
		const [file] = await chooseFile('image/*,video/*');
		if (!file) return;
		unreadable = false;
		if (file.type.startsWith('video/')) {
			const reading = videoFrom(file);
			if (reading.kind === 'too-large') tooLarge = true;
			else if (reading.kind === 'picked') add({ kind: 'video', blob: reading.video.blob, mimeType: reading.video.mimeType, fileName: VIDEO_NAME_PREFIX + reading.video.extension });
			return;
		}
		const jpeg = await toUploadJpeg(file);
		if (jpeg) add(photoMedia(jpeg));
		else unreadable = true;
	}
</script>

{#if choosingCamera}
	<BottomSheet title={t('photo_camera')} onDismiss={() => (choosingCamera = false)}>
		<div class="flex gap-2">
			<div class="flex-1"><SourceButton label={t('media_take_photo')} icon="Camera" onclick={() => void takePhoto()} enabled={canAddPhoto} /></div>
			<div class="flex-1"><SourceButton label={t('media_video_record')} icon="Video" onclick={() => void recordVideo()} enabled={canAddVideo} /></div>
		</div>
	</BottomSheet>
{/if}

<div class="flex w-full flex-col gap-2">
	{#if items.length > 0}
		<div class="flex flex-wrap gap-2">
			{#each items as item, index (index)}
				<MediaTile onRemove={() => onchange(items.filter((_, at) => at !== index))} removeEnabled={enabled}>
					{#if previews[index]}
						<img src={previews[index]} alt="" class="absolute inset-0 size-full object-cover" />
					{:else}
						<AppIcon icon="Video" tint="primary" size={28} />
					{/if}
				</MediaTile>
			{/each}
		</div>
	{/if}
	<div class="flex gap-2">
		<div class="flex-1"><SourceButton label={t('photo_camera')} icon="Camera" onclick={() => (choosingCamera = true)} enabled={canAddPhoto || canAddVideo} /></div>
		<div class="flex-1"><SourceButton label={t('photo_gallery')} icon="Photo" tone="library" onclick={() => void pickFromGallery()} enabled={canAddPhoto || canAddVideo} /></div>
	</div>
	{#if tooLarge}<InlineMessage text={t('web_video_too_large', Math.round(VIDEO_MAX_BYTES / BYTES_PER_MEGABYTE))} />{/if}
	{#if unreadable}<InlineMessage text={t('web_photo_unreadable')} />{/if}
	{#if limitReached}<InlineMessage text={t('media_limit_reached')} />{/if}
</div>
