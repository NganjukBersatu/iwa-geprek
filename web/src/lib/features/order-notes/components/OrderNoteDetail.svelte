<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { OrderNote, OrderNoteRename } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import OrderNoteRenameDialog from './OrderNoteRenameDialog.svelte';
	import { termText } from '$lib/text/terms';
	import { orderNoteText } from '$lib/text/order-notes';
	import { format } from '$lib/text/format';

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<OrderNote, OrderNoteRename, null>(untrack(() => id), {
		load: (noteId) => api.orderNotes.detail(noteId),
		update: (note, body) => api.orderNotes.rename(note, body),
		remove: (note) => api.orderNotes.remove(note),
		name: (note) => note.name,
		text: recordText('catatan', PAGES.orderNotes.label)
	});

	const used = (note: OrderNote) => (note.used_by_orders > 0 ? format(controlText.ordersCount, { count: formatNumber(note.used_by_orders, 0) }) : EMPTY_VALUE);
</script>

<RecordDetailView
	{detail}
	back={PAGES.orderNotes}
	tables={['categories']}
	title={(note) => note.name}
	description={() => orderNoteText.dialogDescription}
	removable={(note) => note.used_by_orders === 0}
>
	{#snippet body(note)}
		<Card>
			<FigureList title={termText.note} figures={[{ label: termText.name, value: note.name }, { label: termText.branch, value: note.outlet_name ?? termText.allBranches }, { label: orderNoteText.inUse, value: used(note) }]} />
			{#if note.used_by_orders > 0}
				<p class="mt-3 text-xs text-slate-600">{orderNoteText.inUseNote}</p>
			{/if}
		</Card>
	{/snippet}
	{#snippet form(props)}
		<OrderNoteRenameDialog note={props.record} busy={props.busy} error={props.error} onsave={(name) => props.onsave({ name })} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote()}
		{orderNoteText.removeNote}
	{/snippet}
</RecordDetailView>
