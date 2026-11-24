<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { IngredientCountRequest } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { live } from '$lib/live/live';
	import { ingredientCountRequestPath } from '$lib/nav/pages';
	import { ingredientCountRequestText as text } from '$lib/text/ingredient-count-requests';
	import { pendingRequestColumns } from '../columns';
	import type { IngredientCountRequestsState } from '../ingredient-count-requests.svelte';

	let { requests }: { requests: IngredientCountRequestsState } = $props();

	onMount(() => {
		void requests.load();
		return live.on(requests.tables, () => void requests.refresh());
	});
</script>

<Card flush>
	<CardHeader divided title={text.listTitle} description={text.listDescription} />
	{#if requests.error}
		<div class="p-4"><Banner tone="danger" icon="alert-triangle" title={text.loadFailedTitle}>{requests.error}</Banner></div>
	{:else if requests.loading && requests.items.length === 0}
		<SkeletonList rows={3} label={text.loadingList} />
	{:else if requests.items.length === 0}
		<Notice text={text.empty} />
	{:else}
		<DataTable columns={pendingRequestColumns} rows={requests.items} rowKey={(row) => row.id} loading={requests.loading} onopen={(row: IngredientCountRequest) => void goto(ingredientCountRequestPath(row.id))} />
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={requests.page} total={requests.total} unit={text.unit} disabled={requests.loading} onchange={(page) => requests.setPage(page)} />
		</div>
	{/if}
</Card>
