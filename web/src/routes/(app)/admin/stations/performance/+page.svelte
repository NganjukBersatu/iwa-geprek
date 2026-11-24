<script lang="ts">
	import PerformanceView from '$lib/features/stations/components/PerformanceView.svelte';
	import { PerformanceState } from '$lib/features/stations/performance.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import { pageText } from '$lib/text/pages';

	const performance = new PerformanceState();
</script>

<ReportShell report={performance} title={pageText.stationPerformanceTitle} description={pageText.stationPerformanceDescription}>
	{#snippet children(data)}
		<PerformanceView {data} {performance} />
	{/snippet}
</ReportShell>
