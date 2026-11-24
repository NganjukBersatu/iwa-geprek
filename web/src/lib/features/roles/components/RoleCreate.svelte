<script lang="ts">
	import { api } from '$lib/api';
	import type { Permission, Role, RoleCreate, RoleStation } from '$lib/api/types';
	import { PAGES, rolePath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import { groupPermissions } from '../roles.svelte';
	import RoleForm from './RoleForm.svelte';

	type RoleContext = { roles: Role[]; permissions: Permission[]; stations: RoleStation[] };

	const create = new RecordCreateState<Role, RoleCreate, RoleContext>({
		context: async () => {
			const [roles, permissions, stations] = await Promise.all([api.roles.list(), api.roles.permissions(), api.roles.stations()]);
			return { roles, permissions, stations };
		},
		create: (body) => api.roles.create(body),
		name: (role) => role.name,
		after: (role) => rolePath(role.id),
		text: createText('peran')
	});
</script>

<RecordCreateView {create} back={PAGES.roles}>
	{#snippet form(props)}
		{@const permissions = props.context?.permissions ?? []}
		<RoleForm
			role={null}
			groups={groupPermissions(permissions)}
			stations={props.context?.stations ?? []}
			total={permissions.length}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			defaultKeys={permissions.filter((permission) => permission.default_for_new_role).map((permission) => permission.key)}
			canMarkProtected={(props.context?.roles ?? []).some((role) => role.is_protected && role.held_by_viewer)}
			onsave={(body) => props.onsave(body as RoleCreate)}
			onclose={props.onclose}
		/>
	{/snippet}
</RecordCreateView>
