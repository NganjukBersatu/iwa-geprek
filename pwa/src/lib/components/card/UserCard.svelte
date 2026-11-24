<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { bgColor, type ColorToken } from '$lib/theme/colors';

	/** Kartu identitas pengguna di puncak dashboard; [containerColor] dibuat transparan bila kartu berada di atas latar lain. */
	let {
		name,
		subtitle,
		photoUrl,
		tag,
		containerColor = 'primary',
		padding = '16px'
	}: { name: string; subtitle?: string | null; photoUrl?: string | null; tag?: string | null; containerColor?: ColorToken | 'transparent'; padding?: string } = $props();
</script>

<div class="flex w-full items-center gap-3 rounded-card {containerColor === 'transparent' ? '' : bgColor[containerColor]}" use:dynamicStyle={{ padding: padding }}>
	<div class="flex size-[var(--size-avatar-large)] shrink-0 items-center justify-center overflow-hidden rounded-full bg-on-primary-subtle">
		{#if photoUrl}
			<img src={photoUrl} alt="" class="size-full object-cover" />
		{:else}
			<AppIcon icon="UserCircle" tint="on-primary" size={40} />
		{/if}
	</div>
	<div class="min-w-0 flex-1">
		<p class="text-title m-0 truncate text-on-primary">{name}</p>
		{#if subtitle}<p class="text-body m-0 truncate text-on-primary-muted">{subtitle}</p>{/if}
		{#if tag}<p class="text-label mt-1 inline-block rounded-full bg-surface-accent px-3 py-1 text-content">{tag}</p>{/if}
	</div>
</div>
