<script lang="ts">
	import { page } from '$app/state';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import SopReadersView from '$lib/features/sop/components/SopReadersView.svelte';
	import { readerColumns } from '$lib/features/sop/reader-columns';
	import { SopReadersState } from '$lib/features/sop/readers.svelte';
	import { sopEditPath } from '$lib/nav/pages';
	import { format } from '$lib/text/format';
	import { sopReadersText } from '$lib/text/sop-readers';

	const sopId = page.params['id'] as string;
	const readers = new SopReadersState(sopId);
	const title = $derived(readers.title ? format(sopReadersText.pageTitle, { title: readers.title }) : sopReadersText.pageTitleFallback);
</script>

<ManageShell manage={readers} filters={readers.filters} {title} description={sopReadersText.pageDescription} loadingText={sopReadersText.loading} back={{ label: sopReadersText.back, path: sopEditPath(sopId) }}>
	{#snippet actions()}
		<MoreButton exporter={{ title, columns: readerColumns, rows: () => readers.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<SopReadersView {readers} />
	{/snippet}
</ManageShell>
