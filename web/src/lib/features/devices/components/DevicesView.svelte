<script lang="ts">
	import { goto } from '$app/navigation';
	import { deviceNewPath, devicePath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import type { Device } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { BRANCH_SORT, withBranchColumn } from '$lib/components/table/branch-column';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { DevicesState } from '../devices.svelte';
	import { deviceColumns } from '../columns';
	import { REGISTERED } from '../sections';
	import { deviceText } from '$lib/text/devices';

	let { devices }: { devices: DevicesState } = $props();

	const columns = $derived(withBranchColumn(deviceColumns, devices.filters.allBranches, BRANCH_SORT));
	const hardware = (row: Device) => [row.brand, row.model].filter(Boolean).join(' ');
</script>

<Card flush>
	<CardHeader divided title={deviceText.listTitle} description={deviceText.listDescription}>
		{#snippet actions()}
			{#if devices.items.length > 0}
				<Button label={deviceText.addDevice} icon="plus" variant="primary" compact onclick={() => void goto(deviceNewPath())} />
			{/if}
		{/snippet}
	</CardHeader>
	{#if devices.items.length === 0}
		<Notice title={emptyText.devices.title} text={emptyText.devices.text}>
			<Button label={emptyText.devices.action} icon="plus" variant="primary" onclick={() => void goto(deviceNewPath())} />
		</Notice>
	{:else}
		<DataTable sort={devices.sort} {columns} rows={devices.items} rowKey={(row) => row.id} loading={devices.loading} trailing="status" onopen={(row) => void goto(devicePath(row.id))}>
			{#snippet first(row)}
				<span class="block">{row.name}</span>
				{#if hardware(row)}<span class="block text-xs font-normal text-slate-500">{hardware(row)}</span>{/if}
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={row.status === REGISTERED ? 'success' : 'warning'}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
	{/if}
</Card>
