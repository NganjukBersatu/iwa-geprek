<script lang="ts">
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatNumber } from '$lib/format/currency';
	import { format } from '$lib/text/format';
	import { sopReadersText } from '$lib/text/sop-readers';
	import { readerColumns } from '../reader-columns';
	import type { SopReadersState } from '../readers.svelte';

	let { readers }: { readers: SopReadersState } = $props();

	const summary = $derived(format(sopReadersText.summary, { read: formatNumber(readers.readCount, 0), audience: formatNumber(readers.audienceCount, 0), version: readers.version }));
</script>

<Card flush>
	<CardHeader divided title={sopReadersText.readers} description={summary} />
	{#if readers.items.length === 0}
		<Notice text={noMatchText(sopReadersText.unit, false, readers.filters.count > 0) ?? sopReadersText.empty} />
	{:else}
		<DataTable sort={readers.sort} columns={readerColumns} rows={readers.items} rowKey={(row) => row.id} loading={readers.loading}>
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={row.current ? 'success' : row.read_version === null ? 'danger' : 'warning'}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={readers.page} total={readers.total} unit={sopReadersText.unit} disabled={readers.loading} onchange={(page) => readers.setPage(page)} />
		</div>
	{/if}
</Card>
