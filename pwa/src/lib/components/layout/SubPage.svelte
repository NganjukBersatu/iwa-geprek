<script lang="ts">
	import type { Snippet } from 'svelte';
	import { goto } from '$app/navigation';
	import SubPageHeader from './SubPageHeader.svelte';

	/** Halaman turunan: judul dengan tombol kembali di atas, isi mengisi sisanya. */
	let { title, backHref, children }: { title: string; backHref: string; children: Snippet } = $props();
</script>

<div class="flex h-full w-full flex-col">
	<SubPageHeader {title} onBack={() => void goto(backHref)} />
	<div class="relative min-h-0 flex-1">{@render children()}</div>
</div>
