<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { Role, RoleCreate } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import { PAGES } from '$lib/nav/pages';
	import { roleText } from '$lib/text/roles';
	import { actionText } from '$lib/text/actions';

	let roles = $state<Role[] | null>(null);
	let error = $state('');

	async function load(): Promise<void> {
		error = '';
		try {
			roles = await api.roles.list();
		} catch (cause) {
			error = userMessage(cause, roleText.listLoadFailed);
		}
	}

	onMount(() => void load());

	const entryColumns = $derived<Field[]>([
		{ key: 'name', label: roleText.roleName, required: true, placeholder: roleText.roleNameExample },
		{ key: 'description', label: roleText.description },
		{ key: 'copy_from', label: roleText.copyPermissionsFrom, kind: 'select', options: (roles ?? []).map((role) => ({ value: role.id, label: role.name })) }
	]);

	function createMany(rows: Record<string, string | number>[]) {
		const items: RoleCreate[] = rows.map((row) => {
			const source = (roles ?? []).find((role) => role.id === row['copy_from']);
			return { name: String(row['name']), description: row['description'] ? String(row['description']) : null, permissions: source && !source.full_access ? source.permissions : [], is_protected: false };
		});
		return api.roles.bulk.create(items);
	}
</script>

{#if error}
	<Banner tone="danger" icon="alert-triangle" title={actionText.pageLoadFailed}>
		{error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void load()} />
		{/snippet}
	</Banner>
{:else if roles}
	<BulkEntryDialog
		asPage
		title={roleText.bulkTitle}
		hint={roleText.bulkHint}
		columns={entryColumns}
		submit={createMany}
		submitLabel="Simpan semua peran"
		onclose={() => void goto(PAGES.roles.path)}
	/>
{:else}
	<Notice loading text={roleText.listLoading} />
{/if}
