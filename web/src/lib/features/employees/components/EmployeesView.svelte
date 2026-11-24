<script lang="ts">
	import { goto } from '$app/navigation';
	import { employeeNewPath, employeePath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import { assignableRoles } from '$lib/features/roles/assignable';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import type { Field } from '$lib/components/form/types';
	import Pager from '$lib/components/pager/Pager.svelte';
	import BulkActions from '$lib/components/table/BulkActions.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatNumber } from '$lib/format/currency';
	import type { EmployeesState } from '../employees.svelte';
	import { employeeColumns } from '../columns';
	import { termText } from '$lib/text/terms';
	import { employeeText } from '$lib/text/employees';
	import { format } from '$lib/text/format';

	let { employees }: { employees: EmployeesState } = $props();

	const columns = $derived(employeeColumns(employees.branchName));

	const roleOptions = $derived(assignableRoles(employees.roles).map((role) => ({ value: role.id, label: role.name })));
	const outletOptions = $derived(employees.outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));

	const changeFields = $derived<Field[]>([
		{ key: 'role_id', label: termText.role, kind: 'select', options: roleOptions },
		{ key: 'outlet_id', label: termText.branch, kind: 'select', options: outletOptions },
		{ key: 'is_active', label: employeeText.accountStatus, kind: 'toggle', yes: termText.active, no: termText.inactive }
	]);
</script>

<Card flush>
	<CardHeader divided title={employeeText.listTitle} description={format(employeeText.accountsCaption, { count: formatNumber(employees.total, 0) })} />
	<ListSearch value={employees.search} placeholder={employeeText.searchPlaceholder} label={employeeText.search} onsearch={(query) => employees.setSearch(query)} />
	{#if employees.items.length === 0}
		{@const noMatch = noMatchText('karyawan', employees.search !== '', employees.filters.count > 0)}
		{#if noMatch}
			<Notice text={noMatch} />
		{:else}
			<Notice title={emptyText.employees.title} text={emptyText.employees.text}/>
		{/if}
	{:else}
		<DataTable sort={employees.sort} {columns} rows={employees.items} rowKey={(row) => row.id} loading={employees.loading} selection={employees.selection} selectable={(row) => !row.locked} onopen={(row) => void goto(employeePath(row.id))}>
			{#snippet first(row)}
				<span class="block">{row.name || row.username}</span>
				<span class="block text-xs font-normal text-slate-500">@{row.username}</span>
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={row.is_active ? 'success' : 'neutral'}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={employees.page} total={employees.total} unit="karyawan" disabled={employees.loading} onchange={(page) => employees.setPage(page)} />
		</div>
	{/if}
</Card>

<BulkActions
	selection={employees.selection}
	noun="karyawan"
	bind:removing={employees.bulkRemoveOpen}
	bind:changing={employees.changeOpen}
	fields={changeFields}
	onchange={(changes) => void employees.changeSelected(changes)}
	busy={employees.busy}
	error={employees.actionError}
	onremove={() => void employees.removeSelected()}
	oncancel={() => employees.closeDialogs()}
>
	{employeeText.removeNote}
</BulkActions>
