<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { OrderCatalog, OrderCorrection, SessionOrderDetail } from '$lib/api/types';
	import { access } from '$lib/auth/access.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { SALES_TABLES } from '$lib/live/tables';
	import { PAGES, sessionPath } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import DepositedDayWarning from '../../deposits/components/DepositedDayWarning.svelte';
	import { DayWarning } from '../../deposits/day-warning.svelte';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { formatDateTime } from '$lib/format/datetime';
	import OrderDetail from './OrderDetail.svelte';
	import OrderForm from './OrderForm.svelte';
	import { termText } from '$lib/text/terms';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { format } from '$lib/text/format';

	let { sessionId, id }: { sessionId: string; id: string } = $props();

	const warning = new DayWarning();

	const detail = new RecordDetailState<SessionOrderDetail, OrderCorrection, OrderCatalog>(untrack(() => id), {
		load: (orderId) => api.sessions.order(orderId),
		context: () => api.sessions.catalog(untrack(() => id)),
		update: async (order, body) => {
			await api.sessions.correctOrder(order.id, body);
			return api.sessions.order(order.id);
		},
		remove: (order) => api.sessions.removeOrder(order.id),
		name: (order) => order.receipt_number ?? termText.transaction,
		text: recordText('transaksi', PAGES.sessionHistory.label)
	});

	// The days a deletion would touch are read when the question opens, and the confirm waits for the answer.
	$effect(() => {
		if (!detail.removing) {
			warning.clear();
			return;
		}
		const order = untrack(() => detail.record);
		if (order) void warning.read([{ outlet_id: order.outlet_id, day: order.business_day }]);
	});
</script>

<RecordDetailView
	{detail}
	back={{ ...PAGES.sessionHistory, path: sessionPath(sessionId) }}
	trail={(order) => [
		{ label: PAGES.sessionHistory.label, href: PAGES.sessionHistory.path },
		{ label: format(sessionDetailText.sessionOf, { name: order.cashier_username ?? '' }).trim(), href: sessionPath(order.session_id) },
		{ label: format(sessionDetailText.transactionOf, { number: order.receipt_number ?? '' }).trim() }
	]}
	tables={SALES_TABLES}
	title={(order) => format(sessionDetailText.orderTitle, { number: order.receipt_number ?? '' }).trim()}
	description={(order) => `${formatDateTime(order.created_at)} · ${formatRupiah(order.total)}`}
	editable={(order) => !order.voided}
	removeBusy={warning.checking}
>
	{#snippet badge(order)}
		<Badge tone={order.voided ? 'danger' : 'success'}>{order.voided ? sessionDetailText.voided : sessionDetailText.valid}</Badge>
	{/snippet}
	{#snippet body(order)}
		{#if !order.voided}
			<Banner tone="info" icon="info-circle" title={sessionDetailText.cancelNoteTitle}>
				{sessionDetailText.cancelNote}
				{#snippet action()}
					{#if access.allows('decide_cancellations')}
						<Button label={sessionDetailText.cancelNoteOpen} variant="tertiary" href={PAGES.cancellations.path} />
					{/if}
				{/snippet}
			</Banner>
		{/if}
		<OrderDetail {order} />
	{/snippet}
	{#snippet form(props)}
		{#if props.context}
			<OrderForm order={props.record} catalog={props.context} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={props.onsave} onclose={props.onclose} />
		{/if}
	{/snippet}
	{#snippet removeNote(order)}
		{format(sessionDetailText.orderRemoveNote, { amount: formatRupiah(order.total) })}
		<DepositedDayWarning {warning} />
	{/snippet}
</RecordDetailView>
