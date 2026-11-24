<script lang="ts">
	import { goto } from '$app/navigation';
	import { paymentMethodNewPath, paymentMethodPath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { BRANCH_SORT, withBranchColumn } from '$lib/components/table/branch-column';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { paymentMethodColumns } from '../columns';
	import type { PaymentMethodsState } from '../payment-methods.svelte';
	import PaymentMethodForm from './PaymentMethodForm.svelte';
	import { termText } from '$lib/text/terms';
	import { paymentMethodText } from '$lib/text/payment-methods';

	let { methods }: { methods: PaymentMethodsState } = $props();

	const columns = $derived(withBranchColumn(paymentMethodColumns, methods.filters.allBranches, BRANCH_SORT));
</script>

{#if methods.actionError}
	<Banner tone="danger" icon="alert-triangle">{methods.actionError}</Banner>
{/if}

<Card flush>
	<CardHeader divided title={paymentMethodText.methods} description={paymentMethodText.listDescription} />
	{#if methods.items.length === 0}
		<Notice title={emptyText.paymentMethods.title} text={emptyText.paymentMethods.text}/>
	{:else}
		<DataTable sort={methods.sort} {columns} rows={methods.items} rowKey={(row) => row.id} loading={methods.loading} onopen={(row) => void goto(paymentMethodPath(row.id))}>
			{#snippet first(row)}
				<span class="inline-flex items-center gap-2">
					<i class="ti {row.icon} text-xl text-slate-500" aria-hidden="true"></i>
					<span>{row.label}</span>
					<span class="font-mono text-xs text-slate-500">{row.code}</span>
					{#if !row.is_active}<Badge tone="neutral">{termText.inactive}</Badge>{/if}
				</span>
			{/snippet}
		</DataTable>
	{/if}
</Card>

