<script lang="ts">
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import TargetsView from '$lib/features/stations/components/TargetsView.svelte';
	import { TargetsState } from '$lib/features/stations/targets.svelte';
	import { pageText } from '$lib/text/pages';

	const targets = new TargetsState();
</script>

<ManageShell manage={targets} filters={targets.filters} title={pageText.stationTargetsTitle} description={pageText.stationTargetsDescription} loadingText={pageText.loadingTargets}>
	{#snippet children()}
		<TargetsView {targets} />
	{/snippet}
</ManageShell>
