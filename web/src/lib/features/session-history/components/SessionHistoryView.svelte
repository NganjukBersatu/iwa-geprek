<script lang="ts">
	import { sessionPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import type { SessionHistoryPage } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import type { SessionHistoryState } from '../session-history.svelte';
	import { sessionHistoryColumns } from '../columns';
	import { termText } from '$lib/text/terms';
	import { sessionHistoryText } from '$lib/text/session-history';

	let { data, history }: { data: SessionHistoryPage; history: SessionHistoryState } = $props();

	const columns = sessionHistoryColumns;
</script>

<Card flush>
	<CardHeader divided title={sessionHistoryText.listTitle} description={sessionHistoryText.listDescription} />
	<ListSearch value={history.search} placeholder={sessionHistoryText.searchPlaceholder} label={sessionHistoryText.search} onsearch={(query) => history.setSearch(query)} />
	{#if data.items.length === 0}
		<Notice text={noMatchText('sesi', history.search !== '', history.filters.get('status_sesi') !== null) ?? sessionHistoryText.noSessions} />
	{:else}
		<DataTable {columns} rows={data.items} rowKey={(row) => row.id} trailing="selisih" loading={history.loading} sort={history.sort} onopen={(row) => void goto(sessionPath(row.id))}>
			{#snippet first(row)}
				<span class="inline-flex items-center gap-2">
					<span>{row.cashier_username}</span>
					{#if row.running}<Badge tone="success">{termText.running}</Badge>{/if}
				</span>
				<span class="block text-xs font-normal text-slate-500">{row.shift_code ?? EMPTY_VALUE}</span>
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={data.page} total={data.total} unit="sesi" disabled={history.loading} onchange={(page) => history.setPage(page)} />
		</div>
	{/if}
</Card>
