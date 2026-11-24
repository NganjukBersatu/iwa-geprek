<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { untrack, type Snippet } from 'svelte';
	import { access } from '$lib/auth/access.svelte';
	import { PAGES, pageAt } from '$lib/nav/pages';
	import NoAccess from './NoAccess.svelte';

	/** Menampilkan halaman hanya untuk akun yang berhak; beranda dialihkan ke layar pertama yang boleh dibuka, alamat tertutup lain menampilkan penjelasan dan jalan kembali. */
	let { children }: { children: Snippet } = $props();

	const current = $derived(pageAt(page.url.pathname));
	// An address outside the screen list, such as the profile, is open to every signed-in account.
	const state = $derived(current ? access.screen(current.screen) : 'open');
	const landing = $derived(current?.path === PAGES.dashboard.path);

	// Only a new address asks again after a failed fetch, never the fetch's own outcome.
	$effect(() => {
		void page.url.pathname;
		untrack(() => access.retry());
	});

	$effect(() => {
		if (state !== 'closed' || !landing) return;
		const target = access.firstOpen();
		if (target) void goto(target.path, { replaceState: true });
	});
</script>

{#if state === 'open'}
	{@render children()}
{:else if state === 'closed' && (!landing || !access.firstOpen())}
	<NoAccess back={access.firstOpen()} />
{/if}
