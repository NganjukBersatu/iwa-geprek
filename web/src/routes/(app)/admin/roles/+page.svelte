<script lang="ts">
	import { termText } from '$lib/text/terms';
	import { roleBulkPath, roleNewPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import AddButton from '$lib/components/button/AddButton.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import RolesView from '$lib/features/roles/components/RolesView.svelte';
	import { RolesState } from '$lib/features/roles/roles.svelte';
	import { roleColumns } from '$lib/features/roles/columns';
	import { pageText } from '$lib/text/pages';

	const roles = new RolesState();
</script>

<ManageShell
	manage={roles}
	title={pageText.rolesTitle}
	description={pageText.rolesDescription}
	loadingText="Memuat peran..."
>
	{#snippet actions()}
		<AddButton label={pageText.addRole} onone={() => void goto(roleNewPath())} onmany={() => void goto(roleBulkPath())} />
		<MoreButton selection={roles.selection} exporter={{ title: termText.role, columns: roleColumns(roles), rows: () => roles.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<RolesView {roles} />
	{/snippet}
</ManageShell>
