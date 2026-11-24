<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import OptionsView from '$lib/features/options/components/OptionsView.svelte';
	import { OptionsState } from '$lib/features/options/options.svelte';
	import { pageText } from '$lib/text/pages';

	const options = new OptionsState();
</script>

<ManageShell manage={options} filters={options.filters} title={pageText.optionsTitle} description={pageText.optionsDescription} loadingText={pageText.loadingOptions}>
	{#snippet actions()}
		<MoreButton selection={[options.selection, options.extraSelection]} />
	{/snippet}
	{#snippet children()}
		<OptionsView {options} />
	{/snippet}
</ManageShell>
