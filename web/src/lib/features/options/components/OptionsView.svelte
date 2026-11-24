<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { goto } from '$app/navigation';
	import BulkActions from '$lib/components/table/BulkActions.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { extraNewPath, extraPath, variantGroupNewPath, variantGroupPath } from '$lib/nav/pages';
	import { extraColumns, groupColumns } from '../columns';
	import type { OptionsState } from '../options.svelte';
	import BranchPriceBadge from '$lib/components/form/BranchPriceBadge.svelte';
	import { termText } from '$lib/text/terms';
	import { optionText } from '$lib/text/options';

	let { options }: { options: OptionsState } = $props();

	const extrasColumns = $derived(extraColumns(options.outlets));
</script>

{#if options.canVariants}
	<Card flush>
		<CardHeader divided title={optionText.variantGroups} description={optionText.variantGroupsDescription}>
			{#snippet actions()}
				<Button label={optionText.addGroup} icon="plus" variant="primary" compact onclick={() => void goto(variantGroupNewPath())} />
			{/snippet}
		</CardHeader>
		{#if options.items.length === 0}
			<Notice text={optionText.noVariantGroups} />
		{:else}
			<DataTable sort={options.sort} columns={groupColumns} rows={options.items} rowKey={(row) => row.id} loading={options.loading} selection={options.selection} onopen={(row) => void goto(variantGroupPath(row.id))}>
				{#snippet first(row)}
					<span class="inline-flex items-center gap-2">
						<span>{row.name}</span>
						{#if row.required}<Badge tone="info">{optionText.required}</Badge>{/if}
						{#if !row.is_active}<Badge tone="neutral">{termText.inactive}</Badge>{/if}
					</span>
				{/snippet}
			</DataTable>
		{/if}
	</Card>
{/if}

{#if options.canExtras}
	<Card flush>
		<CardHeader divided title={termText.extra} description={optionText.extrasDescription}>
			{#snippet actions()}
				<Button label={optionText.addExtra} icon="plus" variant="primary" compact onclick={() => void goto(extraNewPath())} />
			{/snippet}
		</CardHeader>
		{#if options.extras.length === 0}
			<Notice text={optionText.noExtras} />
		{:else}
			<DataTable sort={options.extraSort} columns={extrasColumns} rows={options.extras} rowKey={(row) => row.id} selection={options.extraSelection} trailing="harga" onopen={(row) => void goto(extraPath(row.id))}>
				{#snippet first(row)}
					<span class="inline-flex items-center gap-2">
						<span>{row.name}</span>
						{#if !row.is_active}<Badge tone="neutral">{termText.inactive}</Badge>{/if}
						<BranchPriceBadge item={row} />
					</span>
				{/snippet}
			</DataTable>
		{/if}
	</Card>
{/if}

<BulkActions
	selection={options.selection}
	noun="kelompok varian"
	bind:removing={options.bulkRemoveGroups}
	busy={options.busy}
	error={options.actionError}
	onremove={() => void options.removeSelectedGroups()}
	oncancel={() => options.closeDialogs()}
>
	{optionText.groupRemoveNote}
</BulkActions>

<BulkActions
	selection={options.extraSelection}
	noun="ekstra"
	bind:removing={options.bulkRemoveExtras}
	busy={options.busy}
	error={options.actionError}
	onremove={() => void options.removeSelectedExtras()}
	oncancel={() => options.closeDialogs()}
>
	{optionText.extraRemoveNote}
</BulkActions>

