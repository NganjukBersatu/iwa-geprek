<script lang="ts">
	import type { MoneyChange } from '$lib/api/types';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { ListSort } from '$lib/components/table/list-sort.svelte';
	import { moneyChangeColumns } from '../columns';

	let { rows, allBranches, sort, loading = false }: { rows: MoneyChange[]; allBranches: boolean; sort: ListSort; loading?: boolean } = $props();

	const columns = $derived(moneyChangeColumns(allBranches));
</script>

<DataTable {columns} {rows} rowKey={(row) => row.id} trailing="selisih" {loading} {sort} />
