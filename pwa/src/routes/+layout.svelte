<script lang="ts">
	import '@tabler/icons-webfont/dist/tabler-icons.min.css';
	import '../app.css';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import SplashScreen from '$lib/components/splash/SplashScreen.svelte';
	import { current } from '$lib/auth/current.svelte';
	import BlockedScreen from '$lib/features/blocked/BlockedScreen.svelte';
	import { browserDevice, isBlockedDevice } from '$lib/platform/device';
	import { keepAppCurrent } from '$lib/platform/app-update';

	let { children } = $props();

	keepAppCurrent();

	// Cadangan untuk kerangka yang sudah tersimpan di perangkat: server sudah menolak lebih dulu.
	const blocked = isBlockedDevice(browserDevice());

	onMount(() => {
		if (!blocked) void current.restore();
	});

	// Belum masuk selalu ke layar masuk; yang sudah masuk tidak perlu melihatnya lagi.
	$effect(() => {
		if (!current.restored) return;
		const path = page.url.pathname;
		if (!current.session && path !== '/login') void goto('/login', { replaceState: true });
		else if (current.session && (path === '/login' || path === '/')) void goto('/dashboard', { replaceState: true });
	});
</script>

{#if blocked}
	<BlockedScreen />
{:else}
	<SplashScreen ready={current.restored}>
		{@render children()}
	</SplashScreen>
{/if}
