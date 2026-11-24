<script lang="ts">
	import { access } from '$lib/auth/access.svelte';
	import PageButton from '$lib/components/button/PageButton.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import Skeleton from '$lib/components/skeleton/Skeleton.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { dayLabel } from '$lib/date/range';
	import { EMPTY_VALUE, formatSigned, rupiahInput } from '$lib/format/currency';
	import { PAGES } from '$lib/nav/pages';
	import { qcColumns } from '../columns';
	import { rowKey } from '../qc.svelte';
	import type { OverviewState } from '../overview.svelte';
	import { financeText } from '$lib/text/finance';
	import { format } from '$lib/text/format';

	let { overview, onselectdate }: { overview: OverviewState; onselectdate: (date: string) => void } = $props();

	const qc = $derived(overview.qc);
	const report = $derived(qc.report);
	const allBranches = $derived(overview.filters.allBranches);
	// Only the non-cash methods open in the branches shown.
	const methods = $derived(report && report.methods.length > 0 ? ` (${report.methods.join(', ')})` : '');

	const columns = $derived(qcColumns(allBranches, methods));
</script>

<Card flush>
	<CardHeader
		divided
		title={format(financeText.qcTitle, { methods: methods })}
		description={format(financeText.qcDescription, { methods: methods })}
	>
		{#snippet actions()}
			<PageButton page={PAGES.overpayments} />
		{/snippet}
	</CardHeader>

	{#if qc.error}
		<div class="p-4 tablet:p-5">
			<Banner tone="danger" icon="alert-triangle">{qc.error}</Banner>
		</div>
	{/if}

	{#if !report}
		{#if qc.loading}<SkeletonList rows={5} label={financeText.qcLoading} />{/if}
	{:else}
		<div class="flex flex-wrap gap-x-4 gap-y-1 border-b border-slate-100 bg-slate-50 px-4 py-2 text-xs text-slate-600 tablet:px-5">
			<span><b class="text-success-700">{report.summary.balanced}</b> {financeText.qcBalancedLabel}</span>
			<span><b class="text-danger-700">{report.summary.mismatch}</b> {financeText.qcMismatchLabel}</span>
			<span><b class="text-slate-500">{report.summary.pending}</b> {financeText.qcPendingLabel}</span>
			<span class="ml-auto">
				{financeText.totalDifferenceLabel}
				<b class={Number(report.summary.total_difference) === 0 ? 'text-success-700' : 'text-danger-700'}>{formatSigned(report.summary.total_difference)}</b>
			</span>
		</div>

		{#if qc.loading}<Skeleton class="h-1 w-full rounded-none" />{/if}
		{#if report.rows.length === 0}
			<Notice text={financeText.noDatesWithStatus} />
		{:else}
			<DataTable sort={qc.sort} {columns} rows={report.rows} rowKey={(row) => rowKey(row)} trailing="balance" onopen={(row) => onselectdate(row.date)}>
				{#snippet first(row)}
					{@const label = dayLabel(row.date)}
					<span><span class={label.sunday ? 'text-danger-500' : ''}>{label.weekday}</span> {label.day}</span>
				{/snippet}
				{#snippet cell(row, column)}
					{#if column.key === 'nominal' && access.allows('validate_non_cash')}
						<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
						<div class="ml-auto w-32" onclick={(event) => event.stopPropagation()}>
							<MoneyField
								compact
								label={format(financeText.qcAmountLabel, { date: row.date, branch: allBranches ? ` ${row.outlet_name}` : '' })}
								value={rupiahInput(row.bank_amount)}
								placeholder={EMPTY_VALUE}
								disabled={qc.savingKey === rowKey(row)}
								oncommit={(digits) => void qc.save(row, digits)}
							/>
						</div>
					{:else}
						{column.value(row)}
					{/if}
				{/snippet}
			</DataTable>
		{/if}
		<p class="border-t border-slate-100 px-4 py-3 text-xs text-slate-500 tablet:px-5">
			{format(financeText.qcFootnote, { note: access.allows('validate_non_cash') ? financeText.qcCancelNote : '' })}
		</p>
	{/if}
</Card>
