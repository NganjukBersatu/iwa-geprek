<script lang="ts">
	import type { SessionOrder } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { formatNumber, formatRupiah } from '$lib/format/currency';
	import { formatTime } from '$lib/format/datetime';
	import { format } from '$lib/text/format';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { termText } from '$lib/text/terms';

	let { bills }: { bills: SessionOrder[] } = $props();

	const outstanding = $derived(bills.reduce((sum, bill) => sum + Number(bill.total), 0));

	const columns: Column<SessionOrder>[] = [
		{ key: 'pelanggan', label: sessionDetailText.billCustomer, align: 'left', value: (bill) => bill.customer_name ?? termText.unnamed },
		{ key: 'meja', label: sessionDetailText.billTable, align: 'left', value: (bill) => (bill.table_no ? format(sessionDetailText.billTableNumber, { number: bill.table_no }) : sessionDetailText.billTakeAway) },
		{ key: 'waktu', label: sessionDetailText.billCreated, align: 'left', value: (bill) => formatTime(bill.created_at) },
		{ key: 'total', label: termText.total, value: (bill) => formatRupiah(bill.total) }
	];
</script>

<Card flush>
	<CardHeader divided title={sessionDetailText.unpaid} description={format(sessionDetailText.unpaidDescription, { count: formatNumber(bills.length, 0), total: formatRupiah(outstanding) })}>
		{#snippet actions()}
			<Badge tone="warning">{sessionDetailText.unpaid}</Badge>
		{/snippet}
	</CardHeader>
	<DataTable {columns} rows={bills} rowKey={(bill) => bill.id} />
</Card>
