<script lang="ts">
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import VoidsView from '$lib/features/voids/components/VoidsView.svelte';
	import { VoidsState } from '$lib/features/voids/voids.svelte';
	import { pageText } from '$lib/text/pages';

	const voids = new VoidsState();
</script>

<ReportShell report={voids} title={pageText.voidsTitle} description={pageText.voidsDescription}>
	{#snippet children(data)}
		<VoidsView {data} {voids} />
	{/snippet}
</ReportShell>
