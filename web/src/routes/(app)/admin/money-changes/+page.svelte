<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import { moneyChangeColumns } from '$lib/features/money-changes/columns';
	import MoneyChangesView from '$lib/features/money-changes/components/MoneyChangesView.svelte';
	import { MoneyChangesState } from '$lib/features/money-changes/money-changes.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import { pageText } from '$lib/text/pages';

	const changes = new MoneyChangesState();
</script>

<ReportShell report={changes} title={pageText.moneyChangesTitle} description={pageText.moneyChangesDescription}>
	{#snippet extra()}
		<MoreButton exporter={{ title: pageText.exportTitles.moneyChanges, columns: moneyChangeColumns(changes.allBranches), rows: () => changes.exportRows() }} />
	{/snippet}
	{#snippet children(data)}
		<MoneyChangesView {data} {changes} />
	{/snippet}
</ReportShell>
