<script lang="ts">
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import type { SessionChangesState } from '../session-changes.svelte';
	import MoneyChangesTable from './MoneyChangesTable.svelte';
	import { moneyChangeText } from '$lib/text/money-changes';
	import { format } from '$lib/text/format';

	let { changes }: { changes: SessionChangesState } = $props();
</script>

{#if changes.error}
	<Notice text={format(moneyChangeText.changesLoadFailedDetail, { detail: changes.error })} />
{:else if changes.data === null}
	<Notice loading text={moneyChangeText.loading} />
{:else if changes.data.items.length === 0}
	<Notice text={moneyChangeText.noChangesInSession} />
{:else}
	<MoneyChangesTable rows={changes.data.items} allBranches={false} sort={changes.sort} loading={changes.loading} />
	<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
		<Pager page={changes.data.page} total={changes.data.total} unit="perubahan" disabled={changes.loading} onchange={(page) => changes.setPage(page)} />
	</div>
{/if}
