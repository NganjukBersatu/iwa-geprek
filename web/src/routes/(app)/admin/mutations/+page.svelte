<script lang="ts">
	import MutationsView from '$lib/features/mutations/components/MutationsView.svelte';
	import { MutationsState } from '$lib/features/mutations/mutations.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import { pageText } from '$lib/text/pages';

	const mutations = new MutationsState();
</script>

<ReportShell report={mutations} title={pageText.mutationsTitle} description={pageText.mutationsDescription}>
	{#snippet children(data)}
		<MutationsView {data} {mutations} />
	{/snippet}
</ReportShell>
