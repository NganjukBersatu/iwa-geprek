<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';

	const STAR_COUNT = 5;

	/** Lima bintang terisi sesuai [stars] (0 sampai 5, boleh setengah); bintang kosong memakai warna pemisah. */
	let { stars, description }: { stars: number; description: string } = $props();
</script>

<span class="flex gap-1" role="img" aria-label={description}>
	{#each { length: STAR_COUNT } as _, index (index)}
		{@const filled = Math.min(1, Math.max(0, stars - index))}
		<span class="relative block size-7">
			<AppIcon icon="Star" tint="divider" size={28} />
			{#if filled > 0}
				<span class="absolute inset-0" use:dynamicStyle={{ 'clip-path': `inset(0 ${(1 - filled) * 100}% 0 0)` }}><AppIcon icon="Star" tint="accent" size={28} /></span>
			{/if}
		</span>
	{/each}
</span>
