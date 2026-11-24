<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import LoadingDots from '$lib/components/feedback/LoadingDots.svelte';
	import { bgColor, textColor, type ColorToken } from '$lib/theme/colors';

	/** Tombol utama; selama [loading] tombol tidak bisa diketuk dan teksnya diganti titik berdenyut dengan ukuran tetap. */
	let {
		text,
		onclick,
		enabled = true,
		container = 'primary',
		content = 'on-primary',
		loading = false,
		type = 'button',
		class: className = ''
	}: {
		text: string;
		onclick?: () => void;
		enabled?: boolean;
		container?: ColorToken;
		content?: ColorToken;
		loading?: boolean;
		type?: 'button' | 'submit';
		class?: string;
	} = $props();
</script>

<button
	{type}
	disabled={!enabled || loading}
	{onclick}
	class="relative flex min-h-[var(--space-touch)] w-full items-center justify-center rounded-full px-4 py-3 {bgColor[container]} {textColor[content]} {enabled || loading ? '' : 'disabled-look'} {className}"
>
	<span class="text-button text-center" use:dynamicStyle={{ opacity: loading ? 0 : 1 }}>{text}</span>
	{#if loading}
		<span class="absolute inset-0 flex items-center justify-center"><LoadingDots color={content} /></span>
	{/if}
</button>
