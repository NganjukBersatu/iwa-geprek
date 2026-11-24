<script lang="ts">
	import { api } from '$lib/api';
	import type { Employee, EmployeeCreate, Role } from '$lib/api/types';
	import { PAGES, employeePath } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import { assignableRoles } from '../../roles/assignable';
	import EmployeeForm from './EmployeeForm.svelte';

	type EmployeeContext = { roles: Role[]; outlets: { id: string; name: string }[] };

	const create = new RecordCreateState<Employee, EmployeeCreate, EmployeeContext>({
		context: async () => {
			const [roles, outlets] = await Promise.all([api.roles.list(), branchList()]);
			return { roles, outlets: outlets.map((outlet) => ({ id: outlet.id, name: outlet.name })) };
		},
		create: (body) => api.employees.create(body),
		name: (employee) => employee.name || employee.username,
		after: (employee) => employeePath(employee.id),
		text: createText('karyawan')
	});
</script>

<RecordCreateView {create} back={PAGES.user}>
	{#snippet form(props)}
		<EmployeeForm
			employee={null}
			roles={assignableRoles(props.context?.roles ?? [])}
			outlets={props.context?.outlets ?? []}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(body) => props.onsave(body as EmployeeCreate)}
			onclose={props.onclose}
		/>
	{/snippet}
</RecordCreateView>
