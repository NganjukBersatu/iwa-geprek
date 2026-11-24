<script lang="ts">
	import { termText } from '$lib/text/terms';
	import { goto } from '$app/navigation';
	import { orderPath } from '$lib/nav/pages';
	import type { SessionHistoryRow, SessionOrder } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ListToolbar from '$lib/components/filter/ListToolbar.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { sessionOrderColumns } from '../columns';
	import type { SessionDetailState } from '../session-detail.svelte';
	import { actionText } from '$lib/text/actions';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { format } from '$lib/text/format';

	let { session, row }: { session: SessionDetailState; row: SessionHistoryRow } = $props();

	const columns = sessionOrderColumns;
</script>

<ListToolbar
	value={session.search}
	placeholder={sessionDetailText.searchOrdersPlaceholder}
	label={sessionDetailText.searchOrders}
	filters={session.orderFilters}
	shown={session.visibleOrders.length}
	total={session.orders?.length ?? 0}
	unit="transaksi"
	onsearch={(query) => session.setSearch(query)}
/>

{#if session.ordersError}
	<Notice text={format(sessionDetailText.ordersLoadFailedDetail, { detail: session.ordersError })} />
{:else if session.orders === null}
	<Notice loading text={sessionDetailText.ordersLoading} />
{:else if session.visibleOrders.length === 0}
	<Notice text={session.orders.length === 0 ? sessionDetailText.noOrders : sessionDetailText.noOrdersMatch} />
{:else}
	<DataTable sort={session.orderSort} {columns} rows={session.visibleOrders} rowKey={(order) => order.id} trailing="total" onopen={(order) => void goto(orderPath(row.id, order.id))}>
		{#snippet first(order)}
			<span class="inline-flex items-center gap-2">
				<span class="{order.voided ? 'text-slate-500 line-through' : ''}">{order.customer_name ?? termText.unnamed}</span>
				{#if order.voided}<Badge tone="danger">{actionText.cancel}</Badge>{/if}
			</span>
			<span class="block text-xs font-normal text-slate-500">{order.table_no ? format(sessionDetailText.tableLabel, { number: order.table_no }) : sessionDetailText.takeaway} · {order.receipt_number ?? sessionDetailText.noReceipt}</span>
		{/snippet}
	</DataTable>
{/if}
