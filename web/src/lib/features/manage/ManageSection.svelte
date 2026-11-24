<script lang="ts" generics="T extends { id: string }">
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import BulkResultDialog from '$lib/components/dialog/BulkResultDialog.svelte';
	import Reveal from '$lib/components/motion/Reveal.svelte';
	import { live } from '$lib/live/live';
	import type { ManageState } from './manage.svelte';
	import { actionText } from '$lib/text/actions';
	import { listText } from '$lib/text/lists';

	/** Isi satu daftar kelola tanpa judul halaman: memuat ulang saat query berubah atau data berubah di server, dengan keadaan memuat dan gagal. */
	let { manage, loadingText, children }: { manage: ManageState<T>; loadingText: string; children: Snippet } = $props();

	whenChanged(() => manage.query, () => void manage.queryChanged());
	onMount(() => (manage.tables.length > 0 ? live.on(manage.tables, () => void manage.refresh()) : undefined));
</script>

{#if manage.error}
	<Banner tone="danger" icon="alert-triangle" title={listText.loadFailedTitle}>
		{manage.error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void manage.load()} />
		{/snippet}
	</Banner>
{:else if manage.loading && !manage.loaded}
	<SkeletonPage stats={0} label={loadingText} />
{:else}
	<Reveal>
		{@render children()}
	</Reveal>
{/if}

<BulkResultDialog result={manage.outcome?.result ?? null} names={manage.outcome?.names ?? []} verb={manage.outcome?.verb ?? ''} onclose={() => (manage.outcome = null)} />
