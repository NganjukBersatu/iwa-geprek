<script lang="ts">
	import MarginView from '$lib/features/margin/components/MarginView.svelte';
	import { MarginState } from '$lib/features/margin/margin.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import { pageText } from '$lib/text/pages';

	const margin = new MarginState();
</script>

<ReportShell report={margin} title={pageText.marginTitle} description={pageText.marginDescription}>
	{#snippet children(data)}
		<MarginView {data} {margin} />
	{/snippet}
</ReportShell>
