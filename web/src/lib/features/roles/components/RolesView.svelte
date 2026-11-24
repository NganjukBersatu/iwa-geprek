<script lang="ts">
	import { goto } from '$app/navigation';
	import { roleNewPath, rolePath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import type { Field } from '$lib/components/form/types';
	import BulkActions from '$lib/components/table/BulkActions.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { RolesState } from '../roles.svelte';
	import { roleColumns } from '../columns';
	import { roleText } from '$lib/text/roles';

	let { roles }: { roles: RolesState } = $props();

	const columns = $derived(roleColumns(roles));

	const changeFields: Field[] = [
		{ key: 'description', label: roleText.description },
		{ key: 'sort_order', label: roleText.sortOrder, kind: 'number' }
	];
</script>

<Card flush>
	<CardHeader divided title={roleText.listTitle} description={roleText.listDescription} />
	{#if roles.items.length === 0}
		<Notice title={emptyText.roles.title} text={emptyText.roles.text}/>
	{:else}
		<DataTable sort={roles.sort} {columns} rows={roles.items} rowKey={(row) => row.id} trailing="izin" selection={roles.selection} selectable={(row) => !row.full_access && !row.is_protected && !row.locked} onopen={(row) => void goto(rolePath(row.id))}>
			{#snippet first(row)}
				<span class="flex flex-wrap items-center gap-2">
					<span>{row.name}</span>
					{#if row.full_access}
						<Badge tone="brand">{roleText.allPermissions}</Badge>
					{:else if row.is_default}
						<Badge>{roleText.defaultBadge}</Badge>
					{/if}
				</span>
			{/snippet}
		</DataTable>
	{/if}
</Card>

<p class="text-xs text-slate-500">{roleText.ownerNote}</p>

<BulkActions
	selection={roles.selection}
	noun="peran"
	bind:removing={roles.bulkRemoveOpen}
	bind:changing={roles.changeOpen}
	fields={changeFields}
	onchange={(changes) => void roles.changeSelected(changes)}
	busy={roles.busy}
	error={roles.actionError}
	onremove={() => void roles.removeSelected()}
	oncancel={() => roles.closeDialogs()}
>
	{roleText.removeRefusalNote}
</BulkActions>
