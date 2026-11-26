<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { MoneyEvent, MutationDetail } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import FigureCards from '$lib/components/card/FigureCards.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { EMPTY_VALUE, formatRupiah, formatSigned } from '$lib/format/currency';
	import { formatDateTime, formatTime } from '$lib/format/datetime';
	import { SESSION_TABLES } from '$lib/live/tables';
	import { PAGES, sessionPath } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import { FUND_SOURCES } from '../../finance/fund-sources';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { termText } from '$lib/text/terms';
	import { mutationText } from '$lib/text/mutations';
	import { format } from '$lib/text/format';

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<MutationDetail>(untrack(() => id), {
		load: (sessionId) => api.mutations.detail(sessionId),
		name: (found) => found.session.cashier_username,
		text: recordText('mutasi sesi', PAGES.mutations.label)
	});

	type Part = { label: string; expected: string; counted: string | null; difference: string | null };

	const partsOf = (session: MutationDetail['session']): Part[] => [
		{ label: mutationText.float, expected: session.planned_float, counted: session.actual_float, difference: session.float_difference },
		{ label: termText.spendingFloat, expected: session.planned_shopping, counted: session.actual_shopping, difference: session.shopping_difference },
		{ label: mutationText.cashRevenue, expected: session.expected_revenue, counted: session.actual_revenue, difference: session.revenue_difference }
	];

	const columns: Column<Part>[] = [
		{ key: 'bagian', label: mutationText.part, align: 'left', value: (part) => part.label },
		{ key: 'seharusnya', label: mutationText.expected, value: (part) => formatRupiah(part.expected) },
		{ key: 'dihitung', label: mutationText.counted, value: (part) => (part.counted === null ? EMPTY_VALUE : formatRupiah(part.counted)) },
		{
			key: 'selisih',
			label: termText.difference,
			value: (part) => (part.difference === null ? EMPTY_VALUE : formatSigned(part.difference)),
			class: (part) => `font-semibold ${part.difference !== null && Number(part.difference) < 0 ? 'text-danger-700' : ''}`
		}
	];

	const describe = (event: MoneyEvent) =>
		event.kind === 'open' ? mutationText.sessionOpenedWithFloat : event.kind === 'close' ? mutationText.sessionClosedCounted : `${event.description ?? termText.purchase} · ${FUND_SOURCES[event.fund_source ?? ''] ?? event.fund_source}`;
</script>

<RecordDetailView
	{detail}
	back={PAGES.mutations}
	trail={(found) => [{ label: PAGES.mutations.label, href: PAGES.mutations.path }, { label: format(mutationText.sessionOf, { name: found.session.cashier_username }) }]}
	tables={SESSION_TABLES}
	title={(found) => format(mutationText.sessionMutationsTitle, { name: found.session.cashier_username })}
	description={(found) => format(mutationText.openedAtBy, { shift: found.session.shift_code ? format(mutationText.shiftPrefix, { code: found.session.shift_code }) : '', time: formatDateTime(found.session.opened_at), status: found.session.closed_at ? format(mutationText.closedAt, { time: formatDateTime(found.session.closed_at) }) : mutationText.stillRunning })}
>
	{#snippet badge(found)}
		<Badge tone={found.session.closed ? 'neutral' : 'success'}>{found.session.closed ? termText.closed : termText.running}</Badge>
	{/snippet}
	{#snippet extraActions(found)}
		<Button label={mutationText.openSession} icon="clock" variant="tertiary" href={sessionPath(found.session.session_id)} />
	{/snippet}
	{#snippet body(found)}
		{@const session = found.session}
		<FigureCards
			label={mutationText.summaryTitle}
			figures={[
				{ label: mutationText.cashRevenue, value: formatRupiah(session.cash_revenue) },
				{ label: termText.nonCash, value: formatRupiah(session.non_cash_revenue) },
				{ label: termText.purchase, value: formatRupiah(session.spending) },
				{ label: mutationText.revenueDifference, value: session.revenue_difference === null ? termText.running : formatSigned(session.revenue_difference) }
			]}
		/>
		<div class="flex flex-col gap-4 tablet:gap-6">
			<Card flush>
				<CardHeader divided title={mutationText.threePartsTitle} description={mutationText.threePartsDescription} />
				<DataTable {columns} rows={partsOf(session)} rowKey={(part) => part.label} trailing="selisih" />
			</Card>
			<Card flush>
				<CardHeader divided title={mutationText.eventsTitle} description={mutationText.eventsDescription} />
				{#if found.events.length === 0}
					<Notice text={mutationText.noEvents} />
				{:else}
					<ol class="flex flex-col divide-y divide-slate-100 px-4 py-1 text-xs text-slate-700 tablet:px-5">
						{#each found.events as event, index (index)}
							<li class="flex justify-between gap-3 py-2">
								<span><span class="text-slate-500">{formatTime(event.at)}</span> · {describe(event)}</span>
								<span class="shrink-0 font-semibold">{formatRupiah(event.amount)}</span>
							</li>
						{/each}
					</ol>
				{/if}
			</Card>
		</div>
	{/snippet}
</RecordDetailView>
