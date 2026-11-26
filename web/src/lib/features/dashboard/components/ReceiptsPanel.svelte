<script lang="ts">
	import IconButton from '$lib/components/button/IconButton.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { formatRupiah } from '$lib/format/currency';
	import { dashboardCardText } from '$lib/text/dashboard-cards';
	import { format } from '$lib/text/format';
	import type { DashboardState } from '../dashboard.svelte';

	/** Struk per hari, minggu, atau bulan di periode dasbor: jumlahnya, pemasukannya, dan rata-rata per struk. */
	let { dashboard }: { dashboard: DashboardState } = $props();

	type Row = DashboardState['chartRows'][number];

	const columns = $derived<Column<Row>[]>([
		{ key: 'hari', label: dashboardCardText.receiptsUnit[dashboard.unit], align: 'left', value: (row) => row.label },
		{ key: 'struk', label: dashboardCardText.receiptsColumn, value: (row) => String(row.orderCount) },
		{ key: 'pemasukan', label: dashboardCardText.receiptsIncome, value: (row) => formatRupiah(row.income) },
		{ key: 'rata', label: dashboardCardText.receiptsAverage, value: (row) => formatRupiah(row.averageTransaction) }
	]);
</script>

<Card padded={false}>
	<CardHeader divided title={format(dashboardCardText.receiptsTitle, { unit: dashboard.unitLabel })} description={dashboardCardText.receiptsDescription}>
		{#snippet actions()}
			<IconButton icon="x" label={dashboardCardText.receiptsClose} onclick={() => (dashboard.panel = null)} />
		{/snippet}
	</CardHeader>
	{#if dashboard.chartRows.length === 0}
		<Notice text={dashboardCardText.receiptsEmpty} />
	{:else}
		<DataTable {columns} rows={dashboard.chartRows} rowKey={(row) => row.label} />
	{/if}
</Card>
