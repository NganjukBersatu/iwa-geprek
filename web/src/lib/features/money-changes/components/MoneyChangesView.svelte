<script lang="ts">
	import type { MoneyChangeReport } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import type { MoneyChangesState } from '../money-changes.svelte';
	import MoneyChangesTable from './MoneyChangesTable.svelte';
	import { moneyChangeText } from '$lib/text/money-changes';

	let { data, changes }: { data: MoneyChangeReport; changes: MoneyChangesState } = $props();
</script>

<Card flush>
	<CardHeader divided title={moneyChangeText.title} description={moneyChangeText.description} />
	{#if data.items.length === 0}
		<Notice text={moneyChangeText.noChanges} />
	{:else}
		<MoneyChangesTable rows={data.items} allBranches={changes.allBranches} sort={changes.sort} loading={changes.loading} />
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={data.page} total={data.total} unit="perubahan" disabled={changes.loading} onchange={(page) => changes.setPage(page)} />
		</div>
	{/if}
</Card>
