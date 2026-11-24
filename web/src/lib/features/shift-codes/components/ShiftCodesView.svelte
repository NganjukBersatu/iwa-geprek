<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import { goto } from '$app/navigation';
	import { shiftCodeNewPath, shiftCodePath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ShiftHoursBadge from '$lib/components/card/ShiftHoursBadge.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Notice from '$lib/components/card/Notice.svelte';
	import type { Field } from '$lib/components/form/types';
	import BulkActions from '$lib/components/table/BulkActions.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import ShiftCategoriesDialog from './ShiftCategoriesDialog.svelte';
	import type { ShiftCodesState } from '../shift-codes.svelte';
	import { shiftCodeColumns, twinCodes } from '../columns';
	import { termText } from '$lib/text/terms';
	import { shiftCodeText } from '$lib/text/shift-codes';
	import { format } from '$lib/text/format';

	let { shiftCodes }: { shiftCodes: ShiftCodesState } = $props();

	const columns = shiftCodeColumns;

	const twins = $derived(twinCodes(shiftCodes.items));
	const rows = $derived(shiftCodes.visible);
	const clockProblems = $derived(shiftCodes.items.filter((group) => group.clock_problem).length);

	const changeFields: Field[] = [
		{ key: 'category', label: termText.category },
		{ key: 'start_clock', label: shiftCodeText.startTimeFormat },
		{ key: 'end_clock', label: shiftCodeText.endTimeFormat },
		{ key: 'crosses_midnight', label: shiftCodeText.crossesMidnight, kind: 'toggle', yes: termText.yes, no: shiftCodeText.no },
		{ key: 'overtime_start_clock', label: shiftCodeText.overtimeStartFormat },
		{ key: 'overtime_end_clock', label: shiftCodeText.overtimeEndFormat },
		{ key: 'color', label: 'Warna (#RRGGBB)' },
		{ key: 'is_day_off', label: shiftCodeText.dayOff, kind: 'toggle', yes: termText.dayOff, no: shiftCodeText.notDayOff },
		{ key: 'sort_order', label: shiftCodeText.order, kind: 'number' }
	];

</script>

{#if clockProblems > 0}
	<Banner tone="warning" icon="alert-triangle">{format(shiftCodeText.clockProblemsNote, { count: clockProblems })}</Banner>
{/if}
{#if shiftCodes.mismatchedCodes > 0}
	<Banner tone="warning" icon="alert-triangle">{format(shiftCodeText.mismatchedCodesNote, { count: shiftCodes.mismatchedCodes })}</Banner>
{/if}
{#if shiftCodes.unsetCategories > 0}
	<Banner tone="info" icon="info-circle">{format(shiftCodeText.unsetCategoriesNote, { count: shiftCodes.unsetCategories })}</Banner>
{/if}
{#if shiftCodes.categoriesOpen}
	<ShiftCategoriesDialog {shiftCodes} />
{/if}
{#if twins.size > 0}
	<Banner tone="warning" icon="alert-triangle">{format(shiftCodeText.duplicateCodesNote, { codes: [...twins].join(', ') })}</Banner>
{/if}

<Card flush>
	<CardHeader divided title={shiftCodeText.listTitle} description={shiftCodeText.listDescription} />
	<ListSearch value={shiftCodes.search} placeholder={shiftCodeText.searchPlaceholder} label={shiftCodeText.search} onsearch={(query) => shiftCodes.setSearch(query)} />
	{#if shiftCodes.visible.length === 0}
		{@const noMatch = noMatchText('kode shift', shiftCodes.search !== '', shiftCodes.filters.count > 0)}
		{#if noMatch}
			<Notice text={noMatch} />
		{:else}
			<Notice title={emptyText.shiftCodes.title} text={emptyText.shiftCodes.text}/>
		{/if}
	{:else}
		<DataTable sort={shiftCodes.sort} {columns} {rows} rowKey={(row) => row.id} loading={shiftCodes.loading} selection={shiftCodes.selection} onopen={(row) => void goto(shiftCodePath(row.id))}>
			{#snippet first(row)}
				<span class="inline-flex items-center gap-2">
					<span class="size-3 rounded-full bg-slate-300" use:dynamicStyle={{ 'background-color': row.color }}></span>
					<span>{row.code}</span>
					{#if twins.has(row.code)}<Badge tone="warning">{shiftCodeText.sameCodeDifferentHours}</Badge>{/if}
				</span>
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'jam'}
					<span class="inline-flex flex-wrap items-center gap-1">
						<ShiftHoursBadge start={row.start_clock} end={row.end_clock} dayOff={row.is_day_off} />
						{#if row.clock_problem}<Badge tone="warning">{row.clock_problem === 'same_clock' ? shiftCodeText.clockProblemSame : shiftCodeText.clockProblemTooLong}</Badge>{/if}
					</span>
				{:else if column.key === 'lembur'}
					<ShiftHoursBadge start={row.overtime_start_clock} end={row.overtime_end_clock} overtime />
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
	{/if}
</Card>

<BulkActions
	selection={shiftCodes.selection}
	noun="kode shift"
	bind:removing={shiftCodes.bulkRemoveOpen}
	bind:changing={shiftCodes.changeOpen}
	fields={changeFields}
	onchange={(changes) => void shiftCodes.changeSelected(changes)}
	busy={shiftCodes.busy}
	error={shiftCodes.actionError}
	onremove={() => void shiftCodes.removeSelected()}
	oncancel={() => shiftCodes.closeDialogs()}
>
	{shiftCodeText.bulkRemoveNote}
</BulkActions>
