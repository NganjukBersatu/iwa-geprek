<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { goto } from '$app/navigation';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { formatNumber } from '$lib/format/currency';
	import { menuTargetPath } from '$lib/nav/pages';
	import { formatRatio, formatSeconds, formatTarget } from '../labels';
	import type { TargetRow, TargetsState } from '../targets.svelte';
	import { termText } from '$lib/text/terms';
	import { stationText } from '$lib/text/stations';

	let { targets }: { targets: TargetsState } = $props();

	const columns: Column<TargetRow>[] = [
		{ key: 'menu', label: termText.menu, align: 'left', value: (row) => row.name },
		{ key: 'stasiun', label: termText.station, align: 'left', value: (row) => row.station_name ?? stationText.noMakerStation },
		{ key: 'target', label: stationText.target, align: 'left', value: (row) => formatTarget(row.branch_target_seconds ?? row.target_seconds) },
		{ key: 'rata', label: stationText.average, value: (row) => formatSeconds(row.average_work_seconds) },
		{ key: 'porsi', label: termText.item, value: (row) => formatNumber(row.tasks, 0) },
		{ key: 'tepat', label: stationText.onTime, value: (row) => formatRatio(row.on_time_ratio) }
	];
</script>

<ListSearch value={targets.search} placeholder={stationText.searchMenuPlaceholder} label={controlText.searchMenu} onsearch={(query) => targets.setSearch(query)} />

<Card flush>
	<CardHeader divided title={termText.menu} description={stationText.targetsDescription} icon="target-arrow" />
	{#if targets.items.length === 0}
		<Notice text={noMatchText('menu', targets.search !== '', targets.filters.count > 0) ?? stationText.noRoutedMenus} />
	{:else}
		<DataTable {columns} rows={targets.items} rowKey={(row) => row.id} onopen={(row) => void goto(menuTargetPath(row.menu_id))} />
	{/if}
</Card>
<Pager page={targets.page} total={targets.total} unit="menu" disabled={targets.loading} onchange={(page) => targets.setPage(page)} />
