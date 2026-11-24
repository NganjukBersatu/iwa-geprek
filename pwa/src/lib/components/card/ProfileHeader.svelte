<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import ImagePreview from '$lib/components/media/ImagePreview.svelte';

	const AVATAR_SIZE = 116;
	const CAMERA_BADGE_SIZE = 38;
	const CAMERA_BADGE_BORDER = 3;
	const DECORATION_SIZE = 170;

	/** Kepala halaman Profil: avatar yang membuka pratinjau foto dan lencana kamera untuk ganti foto, nama, serta label peran dan cabang dengan tombol keluar. */
	let {
		name,
		labels,
		photoUrl,
		logoutLabel,
		changePhotoLabel,
		onLogout,
		onChangePhoto
	}: {
		name: string;
		labels: readonly string[];
		photoUrl: string | null;
		logoutLabel: string;
		changePhotoLabel: string;
		onLogout: () => void;
		onChangePhoto: (() => void) | null;
	} = $props();

	let previewUrl = $state<string | null>(null);

	// Tanpa foto tidak ada yang bisa dipratinjau, jadi ketukan avatar langsung membuka ganti foto.
	function tapAvatar(): void {
		if (photoUrl) previewUrl = photoUrl;
		else onChangePhoto?.();
	}
</script>

<div class="relative w-full overflow-hidden rounded-card bg-surface-accent">
	<span class="pointer-events-none absolute" use:dynamicStyle={{ top: '14px', right: '-28px', transform: 'rotate(-12deg)', opacity: '0.13' }}>
		<AppIcon icon="UserCircle" tint="content" size={DECORATION_SIZE} />
	</span>
	<div class="relative flex items-center gap-4 p-4">
		<div class="relative shrink-0" use:dynamicStyle={{ width: `${AVATAR_SIZE}px`, height: `${AVATAR_SIZE}px` }}>
			<button
				type="button"
				onclick={tapAvatar}
				disabled={!photoUrl && !onChangePhoto}
				aria-label={photoUrl ? undefined : changePhotoLabel}
				class="flex size-full items-center justify-center overflow-hidden rounded-full bg-primary"
			>
				{#if photoUrl}
					<img src={photoUrl} alt="" class="size-full object-cover" />
				{:else}
					<AppIcon icon="UserCircle" tint="on-primary" size={40} />
				{/if}
			</button>
			{#if onChangePhoto}
				<button
					type="button"
					onclick={onChangePhoto}
					aria-label={changePhotoLabel}
					class="absolute right-0 bottom-0 flex items-center justify-center rounded-full bg-accent"
					use:dynamicStyle={{ width: `${CAMERA_BADGE_SIZE}px`, height: `${CAMERA_BADGE_SIZE}px`, border: `${CAMERA_BADGE_BORDER}px solid var(--color-surface-accent)` }}
				>
					<AppIcon icon="Camera" tint="content" size={20} label={changePhotoLabel} />
				</button>
			{/if}
		</div>
		<div class="flex min-w-0 flex-1 flex-col gap-2">
			<p class="text-title m-0 line-clamp-2 text-content">{name}</p>
			<div class="flex flex-wrap gap-2">
				{#each labels as label (label)}
					<span class="text-label rounded-full bg-surface px-3 py-1 text-content">{label}</span>
				{/each}
			</div>
			<button type="button" onclick={onLogout} class="flex w-fit items-center gap-2 self-start rounded-full bg-danger px-3 py-2">
				<AppIcon icon="Logout" tint="on-primary" size={20} />
				<span class="text-label truncate text-on-primary">{logoutLabel}</span>
			</button>
		</div>
	</div>
</div>

{#if previewUrl}<ImagePreview url={previewUrl} onDismiss={() => (previewUrl = null)} />{/if}
