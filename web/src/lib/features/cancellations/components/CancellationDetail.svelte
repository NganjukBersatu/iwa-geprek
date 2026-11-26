<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Cancellation } from '$lib/api/types';
	import { access } from '$lib/auth/access.svelte';
	import { getUser } from '$lib/auth/session';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { formatDate } from '$lib/date/range';
	import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { PAGES } from '$lib/nav/pages';
	import { cancellationText } from '$lib/text/cancellations';
	import { format } from '$lib/text/format';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import DepositedDayWarning from '../../deposits/components/DepositedDayWarning.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import { CancellationDecisionState, DECISION_NOTE_MAX } from '../cancellation-decision.svelte';

	/** One request to cancel an order, waiting or already decided, on its own address; the decision is made here. */
	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<Cancellation>(untrack(() => id), {
		load: (requestId) => api.cancellations.detail(requestId),
		name: (request) => request.receipt_number ?? request.order_id,
		text: recordText(cancellationText.noun, PAGES.cancellations.label)
	});
	const decision = new CancellationDecisionState(() => detail.refresh());
	const canDecide = $derived(access.allows('decide_cancellations'));
	// Server menolak pengaju yang memutuskan pengajuannya sendiri; tombolnya dinonaktifkan sejak awal dengan alasannya.
	const ownRequest = (request: Cancellation): boolean => request.requested_by_id === getUser()?.id;
	const STATUS = {
		approved: { tone: 'danger', label: cancellationText.statusApproved },
		rejected: { tone: 'neutral', label: cancellationText.statusRejected },
		waiting: { tone: 'warning', label: cancellationText.statusWaiting }
	} as const;
</script>

<RecordDetailView
	{detail}
	back={PAGES.cancellations}
	tables={['cancellation_requests', 'orders']}
	title={(request) => format(cancellationText.detailTitle, { order: request.receipt_number ?? '' })}
	trail={(request) => [
		{ label: PAGES.sessionHistory.label, href: PAGES.sessionHistory.path },
		{ label: PAGES.cancellations.label, href: PAGES.cancellations.path },
		{ label: request.receipt_number ?? cancellationText.noun }
	]}
	description={(request) => format(cancellationText.pageDescription, { branch: request.outlet_name, amount: formatRupiah(request.order_total), time: formatDateTime(request.created_at) })}
>
	{#snippet badge(request)}
		{@const status = STATUS[request.decision ?? 'waiting']}
		<Badge tone={status.tone}>{status.label}</Badge>
	{/snippet}
	{#snippet extraActions(request)}
		{#if request.decision === null && canDecide}
			<Button label={cancellationText.reject} icon="x" disabled={decision.busy || ownRequest(request)} hint={cancellationText.ownRequest} onclick={() => decision.ask(request, 'reject')} />
			<Button label={cancellationText.approve} icon="check" variant="danger" disabled={decision.busy || ownRequest(request)} hint={cancellationText.ownRequest} onclick={() => decision.ask(request, 'approve')} />
		{/if}
	{/snippet}
	{#snippet body(request)}
		{#if decision.error && !decision.confirming}
			<Banner tone="danger" icon="alert-triangle">{decision.error}</Banner>
		{/if}
		{#if request.decision === null}
			<Banner tone="info" icon="lock">{cancellationText.waitingNote}</Banner>
			{#if canDecide && ownRequest(request)}
				<Banner tone="warning" icon="user-exclamation">{cancellationText.ownRequest}</Banner>
			{/if}
		{/if}
		<Card>
			<FigureList
				title={cancellationText.orderSection}
				figures={[
					{ label: cancellationText.receipt, value: request.receipt_number ?? EMPTY_VALUE },
					{ label: cancellationText.value, value: formatRupiah(request.order_total), emphasis: 'total' },
					{ label: cancellationText.customer, value: request.customer_name ?? EMPTY_VALUE },
					{ label: cancellationText.table, value: request.table_no ?? EMPTY_VALUE },
					{ label: cancellationText.day, value: formatDate(request.order_business_day) },
					{ label: cancellationText.orderItems, value: request.items_summary || EMPTY_VALUE }
				]}
			/>
		</Card>
		<Card>
			<FigureList
				title={cancellationText.requestSection}
				figures={[
					{ label: cancellationText.cashier, value: request.cashier || EMPTY_VALUE },
					{ label: cancellationText.requested, value: format(cancellationText.requestedAt, { requester: request.requested_by, time: formatDateTime(request.created_at) }) },
					{ label: cancellationText.reason, value: request.reason ?? cancellationText.noReason },
					...(request.decision
						? [
								{ label: cancellationText.decidedBy, value: request.decided_by ?? EMPTY_VALUE },
								{ label: cancellationText.decidedAt, value: request.decided_at ? formatDateTime(request.decided_at) : EMPTY_VALUE },
								{ label: cancellationText.managerNote, value: request.manager_note ?? EMPTY_VALUE }
							]
						: [])
				]}
			/>
		</Card>
		{#if decision.confirming}
			{@const approving = decision.confirming === 'approve'}
			<ConfirmDialog
				open
				title={format(approving ? cancellationText.approveTitleNamed : cancellationText.rejectTitleNamed, { order: request.receipt_number ?? '' })}
				confirmLabel={approving ? cancellationText.approveConfirm : cancellationText.rejectConfirm}
				danger={approving}
				busy={decision.busy || decision.warning.checking}
				error={decision.error}
				onconfirm={() => void decision.confirm(request)}
				oncancel={() => decision.close()}
			>
				{approving
					? format(cancellationText.approveCancelNote, { order: request.receipt_number ?? '', amount: formatRupiah(request.order_total) })
					: format(cancellationText.rejectNote, { order: request.receipt_number ?? '' })}
				{#if approving}<DepositedDayWarning warning={decision.warning} />{/if}
				<div class="mt-3">
					<TextArea label={cancellationText.decisionNote} bind:value={decision.note} maxlength={DECISION_NOTE_MAX} hint={cancellationText.decisionNoteHint} />
				</div>
			</ConfirmDialog>
		{/if}
	{/snippet}
</RecordDetailView>
