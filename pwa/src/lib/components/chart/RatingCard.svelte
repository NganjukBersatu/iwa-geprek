<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import RatingStars from './RatingStars.svelte';

	/** Kartu bintang: [stars] dan [valueText] selalu tampak, dan [details] terbuka halus di bawahnya saat kartu diketuk; tanpa [details] kartu tidak bisa dibuka. */
	let {
		stars,
		valueText,
		starsDescription,
		openLabel,
		closeLabel,
		details
	}: { stars: number; valueText: string; starsDescription: string; openLabel: string; closeLabel: string; details?: Snippet } = $props();

	let open = $state(false);
</script>

{#snippet head()}
	<RatingStars {stars} description={starsDescription} />
	<span class="text-body flex-1 text-content">{valueText}</span>
	{#if details}
		<span use:dynamicStyle={{ transform: `rotate(${open ? 180 : 0}deg)`, transition: 'transform var(--effect-standard) var(--ease-standard)' }}>
			<AppIcon icon="ChevronDown" tint="content-muted" size={20} />
		</span>
	{/if}
{/snippet}

<ListCard>
	{#if details}
		<button type="button" onclick={() => (open = !open)} aria-label={open ? closeLabel : openLabel} class="flex w-full items-center gap-3 p-3 text-start">{@render head()}</button>
	{:else}
		<div class="flex w-full items-center gap-3 p-3">{@render head()}</div>
	{/if}
	{#if details}
		<div class="grid" use:dynamicStyle={{ 'grid-template-rows': open ? '1fr' : '0fr', transition: 'grid-template-rows var(--effect-standard) var(--ease-standard)' }}>
			<div class="overflow-hidden">
				<Divider />
				{@render details()}
			</div>
		</div>
	{/if}
</ListCard>
