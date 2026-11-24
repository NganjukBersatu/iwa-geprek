<script lang="ts">
	import { goto } from '$app/navigation';
	import { lossBulkPath, lossNewPath } from '$lib/nav/pages';
	import AddButton from '$lib/components/button/AddButton.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import LossesView from '$lib/features/ingredient-losses/components/LossesView.svelte';
	import { IngredientLossesState } from '$lib/features/ingredient-losses/ingredient-losses.svelte';
	import { WASTE } from '$lib/features/ingredient-losses/kinds';
	import { lossColumns } from '$lib/features/ingredient-losses/columns';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { pageText } from '$lib/text/pages';

	const losses = new IngredientLossesState();
</script>

<ManageShell
	manage={losses}
	filters={losses.filters}
	title={pageText.lossesTitle}
	description={pageText.lossesDescription}
	loadingText="Memuat catatan..."
>
	{#snippet actions()}
		<AddButton label={pageText.record} onone={() => void goto(lossNewPath(losses.kind))} onmany={() => void goto(lossBulkPath())} />
		<MoreButton exporter={{ title: losses.kind === WASTE ? pageText.exportTitles.waste : pageText.exportTitles.rnd, columns: lossColumns(losses.kind), rows: () => losses.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<LossesView {losses} />
	{/snippet}
</ManageShell>
