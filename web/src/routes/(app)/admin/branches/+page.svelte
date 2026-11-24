<script lang="ts">
	import { branchNewPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import Button from '$lib/components/button/Button.svelte';
	import BranchesView from '$lib/features/branches/components/BranchesView.svelte';
	import { BranchesState } from '$lib/features/branches/branches.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { termText } from '$lib/text/terms';
	import { pageText } from '$lib/text/pages';

	const branches = new BranchesState();
</script>

<ManageShell
	manage={branches}
	title={termText.branch}
	description={pageText.branchesDescription}
	loadingText="Memuat cabang..."
>
	{#snippet actions()}
		<Button label={pageText.addBranch} icon="plus" variant="primary" compact onclick={() => void goto(branchNewPath())} />
	{/snippet}
	{#snippet children()}
		<BranchesView {branches} />
	{/snippet}
</ManageShell>
