<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { branchPath, PAGES, type BranchTab } from '$lib/nav/pages';
	import { memoryKey, recall } from '$lib/stores/memory';
	import { branchDetailText } from '$lib/text/branch-detail';

	/** Alamat lama sebuah pengaturan cabang: dibuka di tab halaman detail cabang yang sedang dipilih, atau daftar cabang bila belum ada yang dipilih. */
	let { tab }: { tab: BranchTab } = $props();

	onMount(() => {
		const branch = recall(memoryKey.filter('cabang'));
		void goto(typeof branch === 'string' ? branchPath(branch, tab) : PAGES.branches.path, { replaceState: true });
	});
</script>

<Notice loading text={branchDetailText.opening} />
