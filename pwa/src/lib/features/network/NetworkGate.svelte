<script lang="ts">
	import type { Snippet } from 'svelte';
	import { fade } from 'svelte/transition';
	import { network } from '$lib/platform/network.svelte';
	import NoConnectionScreen from './NoConnectionScreen.svelte';

	/** Putus yang lebih singkat dari ini tidak memunculkan halaman, agar pindah jaringan tidak membuat layar berkedip. */
	const GRACE_MILLIS = 1500;
	const FADE_MILLIS = 240;

	/** Menampilkan layar tanpa koneksi di atas isi selama internet putus dan menyembunyikannya begitu tersambung; isi tetap hidup di bawahnya. */
	let { children }: { children: Snippet } = $props();

	let lost = $state(false);

	$effect(() => {
		if (network.online) {
			lost = false;
			return;
		}
		const timer = setTimeout(() => (lost = true), GRACE_MILLIS);
		return () => clearTimeout(timer);
	});
</script>

<div class="relative h-full w-full">
	{@render children()}
	{#if lost}
		<div class="absolute inset-0 z-40" transition:fade={{ duration: FADE_MILLIS }}><NoConnectionScreen /></div>
	{/if}
</div>
