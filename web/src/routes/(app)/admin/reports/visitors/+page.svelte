<script lang="ts">
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import VisitorView from '$lib/features/visitor/components/VisitorView.svelte';
	import { VisitorState } from '$lib/features/visitor/visitor.svelte';
	import { pageText } from '$lib/text/pages';

	const visitor = new VisitorState();
</script>

<ReportShell report={visitor} title={pageText.visitorsTitle} description={pageText.visitorsDescription}>
	{#snippet children(data)}
		<VisitorView {data} {visitor} />
	{/snippet}
</ReportShell>
