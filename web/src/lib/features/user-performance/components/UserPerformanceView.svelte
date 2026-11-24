<script lang="ts">
	import { goto } from '$app/navigation';
	import type { PerformanceListRange } from '$lib/api/userPerformance';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { userPerformancePath } from '$lib/nav/pages';
	import { userPerformanceText as t } from '$lib/text/user-performance';
	import { performanceColumns } from '../columns';
	import { RANGE_LABELS } from '../labels';
	import type { UserPerformanceState } from '../user-performance.svelte';

	let { performance }: { performance: UserPerformanceState } = $props();

	const RANGES: PerformanceListRange[] = ['cycle', 'previous'];
	const tabs = RANGES.map((key) => ({ key, label: RANGE_LABELS[key] }));

	function pick(key: string): void {
		const found = RANGES.find((range) => range === key);
		if (found) performance.range = found;
	}
</script>

<Card flush>
	<CardHeader
		divided
		title={t.listTitle}
		description={t.listDescription}
	/>
	<Tabs {tabs} bind:value={() => performance.range, pick} label={t.rangeLabel} />
	<ListSearch value={performance.search} placeholder={t.searchPlaceholder} label={t.searchLabel} onsearch={(query) => performance.setSearch(query)} />
	{#if performance.items.length === 0}
		<Notice text={noMatchText(t.unit, performance.search !== '', performance.filters.count > 0) ?? t.noEmployees} />
	{:else}
		<DataTable sort={performance.sort} columns={performanceColumns} rows={performance.items} rowKey={(row) => row.id} loading={performance.loading} onopen={(row) => void goto(userPerformancePath(row.id))}>
			{#snippet first(row)}
				<span class="block">{row.name}</span>
				{#if row.role_name}<span class="block text-xs font-normal text-slate-400">{row.role_name}</span>{/if}
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'penilaian'}
					{#if row.stars === null}
						<Badge tone="neutral">{column.value(row)}</Badge>
					{:else}
						<span class="inline-flex items-center gap-1 font-semibold text-slate-800"><i class="ti ti-star" aria-hidden="true"></i>{column.value(row)}</span>
					{/if}
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={performance.page} total={performance.total} unit={t.unit} disabled={performance.loading} onchange={(page) => performance.setPage(page)} />
		</div>
	{/if}
</Card>
