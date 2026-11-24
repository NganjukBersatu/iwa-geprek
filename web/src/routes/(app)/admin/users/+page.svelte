<script lang="ts">
	import { termText } from '$lib/text/terms';
	import { employeeBulkPath, employeeNewPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import AddButton from '$lib/components/button/AddButton.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import EmployeesView from '$lib/features/employees/components/EmployeesView.svelte';
	import { EmployeesState } from '$lib/features/employees/employees.svelte';
	import { employeeColumns } from '$lib/features/employees/columns';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { pageText } from '$lib/text/pages';

	const employees = new EmployeesState();
</script>

<ManageShell
	manage={employees}
	filters={employees.filters}
	title={pageText.employeesTitle}
	description={pageText.employeesDescription}
	loadingText={pageText.loadingUsers}
>
	{#snippet actions()}
		<AddButton label={pageText.addEmployee} onone={() => void goto(employeeNewPath())} onmany={() => void goto(employeeBulkPath())} />
		<MoreButton selection={employees.selection} exporter={{ title: termText.employee, columns: employeeColumns(employees.branchName), rows: () => employees.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<EmployeesView {employees} />
	{/snippet}
</ManageShell>
