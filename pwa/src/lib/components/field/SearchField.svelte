<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import TextField from './TextField.svelte';

	/** Kolom pencarian: kolom teks dengan ikon kaca pembesar di ujung kanan. */
	let { value = $bindable(''), label, oninput }: { value?: string; label: string; oninput?: () => void } = $props();
</script>

<TextField bind:value {label} {oninput} enterkeyhint="search">
	{#snippet trailing()}<span class="pr-3"><AppIcon icon="Search" tint="content-muted" size={20} /></span>{/snippet}
</TextField>
