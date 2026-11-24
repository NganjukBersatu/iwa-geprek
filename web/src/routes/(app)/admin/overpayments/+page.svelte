<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import { overpaymentColumns } from '$lib/features/overpayments/columns';
	import OverpaymentsView from '$lib/features/overpayments/components/OverpaymentsView.svelte';
	import { OverpaymentsState } from '$lib/features/overpayments/overpayments.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import { pageText } from '$lib/text/pages';

	const overpayments = new OverpaymentsState();
</script>

<ReportShell report={overpayments} title={pageText.overpaymentsTitle} description={pageText.overpaymentsDescription}>
	{#snippet extra()}
		<MoreButton exporter={{ title: pageText.exportTitles.overpayments, columns: overpaymentColumns(overpayments.allBranches), rows: () => overpayments.exportRows() }} />
	{/snippet}
	{#snippet children(data)}
		<OverpaymentsView {data} {overpayments} />
	{/snippet}
</ReportShell>
