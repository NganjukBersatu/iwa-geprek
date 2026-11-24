<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { EmployeeCreate, Role } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import { PAGES } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { assignableRoles } from '../../roles/assignable';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { employeeText } from '$lib/text/employees';

	let roles = $state<Role[] | null>(null);
	let outlets = $state<{ id: string; name: string }[]>([]);
	let error = $state('');

	async function load(): Promise<void> {
		error = '';
		try {
			const [foundRoles, foundOutlets] = await Promise.all([api.roles.list(), branchList()]);
			roles = foundRoles;
			outlets = foundOutlets.map((outlet) => ({ id: outlet.id, name: outlet.name }));
		} catch (cause) {
			error = userMessage(cause, employeeText.contextLoadFailed);
		}
	}

	onMount(() => void load());

	const entryColumns = $derived<Field[]>([
		{ key: 'name', label: termText.name, required: true },
		{ key: 'username', label: employeeText.username, required: true },
		{ key: 'password', label: employeeText.password, required: true },
		{ key: 'role_id', label: termText.role, kind: 'select', required: true, options: assignableRoles(roles ?? []).map((role) => ({ value: role.id, label: role.name })) },
		{ key: 'outlet_id', label: termText.branch, kind: 'select', options: outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })) }
	]);
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
		title={employeeText.bulkTitle}
		hint={employeeText.bulkHint}
		columns={entryColumns}
		submit={(rows) => api.employees.bulk.create(rows as unknown as EmployeeCreate[])}
		submitLabel="Simpan semua karyawan"
		onclose={() => void goto(PAGES.user.path)}
	/>
{:else}
	<Notice loading text={employeeText.contextLoading} />
{/if}
