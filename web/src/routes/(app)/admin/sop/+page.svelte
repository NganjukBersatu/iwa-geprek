<script lang="ts">
	import { NEW_SOP_PATH } from '$lib/nav/pages';
	import Button from '$lib/components/button/Button.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import SopView from '$lib/features/sop/components/SopView.svelte';
	import { SopState } from '$lib/features/sop/sop.svelte';
	import { pageText } from '$lib/text/pages';

	const sop = new SopState();
</script>

<ManageShell
	manage={sop}
	title={pageText.sopTitle}
	description={pageText.sopDescription}
	loadingText="Memuat SOP..."
>
	{#snippet actions()}
		<Button label={pageText.addSop} icon="plus" variant="primary" compact href={NEW_SOP_PATH} />
	{/snippet}
	{#snippet children()}
		<SopView {sop} />
	{/snippet}
</ManageShell>
