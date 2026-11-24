<script lang="ts">
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import OrderNotesView from '$lib/features/order-notes/components/OrderNotesView.svelte';
	import { OrderNotesState } from '$lib/features/order-notes/order-notes.svelte';
	import { pageText } from '$lib/text/pages';

	const notes = new OrderNotesState();
</script>

<ManageShell manage={notes} title={pageText.orderNotesTitle} description={pageText.orderNotesDescription} loadingText="Memuat catatan pesanan...">
	{#snippet children()}
		<OrderNotesView {notes} />
	{/snippet}
</ManageShell>
