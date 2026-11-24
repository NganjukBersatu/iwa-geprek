<script lang="ts">
	import { goto } from '$app/navigation';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { orderNotePath } from '$lib/nav/pages';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { orderNoteColumns } from '../columns';
	import type { OrderNotesState } from '../order-notes.svelte';
	import { orderNoteText } from '$lib/text/order-notes';

	let { notes }: { notes: OrderNotesState } = $props();

	const columns = orderNoteColumns;
</script>

{#if notes.actionError}
	<Banner tone="danger" icon="alert-triangle">{notes.actionError}</Banner>
{/if}

<Card flush>
	<CardHeader divided title={orderNoteText.title} description={orderNoteText.description} />
	{#if notes.items.length === 0}
		<Notice text={orderNoteText.noNotes} />
	{:else}
		<DataTable sort={notes.sort} {columns} rows={notes.items} rowKey={(row) => row.id} loading={notes.loading} onopen={(row) => void goto(orderNotePath(row.id))}>
		</DataTable>
	{/if}
</Card>
