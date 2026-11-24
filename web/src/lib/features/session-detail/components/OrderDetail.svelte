<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import type { SessionOrder } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { ORDER_TYPE_LABELS } from '../session-detail.svelte';
	import { termText } from '$lib/text/terms';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { format } from '$lib/text/format';

	let { order }: { order: SessionOrder } = $props();

	const facts = $derived([
		{ label: termText.name, value: order.customer_name ?? termText.unnamed },
		{ label: termText.table, value: order.table_no ? format(controlText.tableNumberLabel, { number: order.table_no }) : EMPTY_VALUE },
		{ label: termText.kind, value: ORDER_TYPE_LABELS[order.order_type] ?? order.order_type },
		{ label: termText.time, value: formatDateTime(order.created_at) },
		{ label: termText.method, value: order.payment_method_label ?? EMPTY_VALUE },
		{ label: termText.note, value: order.note ?? EMPTY_VALUE }
	]);
</script>

<div class="grid items-start gap-4 tablet:gap-6 laptop:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
	<Card>
		<CardHeader title={sessionDetailText.orderDetailTitle} icon="receipt" description={format(sessionDetailText.itemsInOrder, { count: order.items.length })} />
		<ul class="mt-3 flex flex-col divide-y divide-slate-100 text-xs text-slate-700">
			{#each order.items as item (item.id)}
				<li class="flex flex-col gap-0.5 py-1.5 first:pt-0">
					<span class="flex justify-between gap-3">
						<span>{item.qty} × {item.name}{item.variant_names.length ? ` (${item.variant_names.join(', ')})` : ''}</span>
						<span class="font-semibold">{formatRupiah(item.subtotal)}</span>
					</span>
					{#each item.extras as extra (extra.extra_id ?? extra.name)}
						<span class="text-slate-500">+ {extra.name}{extra.qty > 1 ? ` ×${extra.qty}` : ''}</span>
					{/each}
					{#if item.note}<span class="text-slate-500">{format(sessionDetailText.noteLabel, { note: item.note })}</span>{/if}
				</li>
			{/each}
		</ul>
		<div class="mt-1 flex flex-col gap-1 border-t border-slate-100 pt-2">
			{#if Number(order.discount) > 0}
				<p class="flex justify-between gap-3 text-xs text-slate-600"><span>{sessionDetailText.promoDiscount}</span><span>− {formatRupiah(order.discount)}</span></p>
			{/if}
			<p class="flex justify-between gap-3 text-sm font-semibold text-slate-800"><span>{termText.total}</span><span>{formatRupiah(order.total)}</span></p>
		</div>
	</Card>

	<Card>
		<CardHeader title={sessionDetailText.customerAndOrder} icon="user" />
		<dl class="mt-3 grid grid-cols-[6rem_1fr] gap-x-3 gap-y-1.5 text-xs">
			{#each facts as fact (fact.label)}
				<dt class="text-slate-500">{fact.label}</dt>
				<dd class="font-semibold text-slate-700 wrap-anywhere">{fact.value}</dd>
			{/each}
			<dt class="text-slate-500">{termText.status}</dt>
			<dd><Badge tone={order.voided ? 'danger' : 'success'}>{order.voided ? sessionDetailText.voided : sessionDetailText.valid}</Badge></dd>
		</dl>
	</Card>
</div>
