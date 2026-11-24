<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { CodeGroup, CodeGroupUpdate } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { formatClockRange, formatClockSpan } from '$lib/format/datetime';
	import { PAGES } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import ShiftCodeForm from './ShiftCodeForm.svelte';
	import { termText } from '$lib/text/terms';
	import { shiftCodeText } from '$lib/text/shift-codes';
	import RichText from '$lib/components/text/RichText.svelte';
	import { format } from '$lib/text/format';

	type ShiftContext = { outlets: { id: string; name: string }[]; categories: string[] };

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<CodeGroup, CodeGroupUpdate, ShiftContext>(untrack(() => id), {
		load: (groupId) => api.shiftCodes.detail(groupId),
		context: async () => {
			const [outlets, categories] = await Promise.all([branchList(), api.shiftCodes.categories()]);
			return { outlets, categories };
		},
		update: (group, body) => api.shiftCodes.update(group.id, body),
		remove: (group) => api.shiftCodes.remove(group.id),
		name: (group) => group.code,
		text: recordText('kode shift', PAGES.shiftCodes.label)
	});
</script>

<RecordDetailView
	{detail}
	back={PAGES.shiftCodes}
	trail={(group) => [{ label: PAGES.shiftCodes.label, href: PAGES.shiftCodes.path }, { label: group.code }]}
	tables={['shift_codes']}
	title={(group) => group.code}
	description={(group) => group.category}
>
	{#snippet badge(group)}
		{#if group.is_day_off}<Badge tone="info">{termText.dayOff}</Badge>{/if}
	{/snippet}
	{#snippet body(group)}
		<Card flush class="grid laptop:grid-cols-2">
			<div class="flex flex-col gap-4 border-b border-slate-100 p-4 tablet:p-5 laptop:border-b-0 laptop:border-r">
				<div class="flex items-center justify-between gap-3">
					<div>
						{#if group.is_day_off}
							<p class="text-2xl font-semibold text-brand-ink">{termText.dayOff}</p>
							<p class="mt-0.5 text-xs text-slate-500">{shiftCodeText.noWorkHours}</p>
						{:else}
							<p class="text-2xl font-semibold text-brand-ink">{formatClockRange(group.start_clock, group.end_clock)}</p>
							<p class="mt-0.5 text-xs text-slate-500">{group.start_clock && group.end_clock ? formatClockSpan(group.start_clock, group.end_clock) : EMPTY_VALUE}</p>
						{/if}
					</div>
					<span class="size-6 shrink-0 rounded-full border border-slate-200 bg-slate-300" use:dynamicStyle={{ 'background-color': group.color }} title={shiftCodeText.codeColor}></span>
				</div>
				<div class="border-t border-slate-100 pt-4">
					<FigureList
						figures={[
							{ label: termText.code, value: group.code },
							{ label: termText.category, value: group.category },
							{ label: shiftCodeText.sortOrder, value: formatNumber(group.sort_order, 0) }
						]}
					/>
				</div>
			</div>
			<div class="flex flex-col gap-4 p-4 tablet:p-5">
				<FigureList
					figures={[
						{ label: shiftCodeText.overtime, value: group.overtime_start_clock && group.overtime_end_clock ? formatClockRange(group.overtime_start_clock, group.overtime_end_clock) : EMPTY_VALUE },
						{ label: shiftCodeText.assignmentsUsing, value: group.assignments > 0 ? format(shiftCodeText.assignmentsCount, { count: formatNumber(group.assignments, 0) }) : EMPTY_VALUE }
					]}
				/>
				<div class="flex flex-col gap-2 border-t border-slate-100 pt-4">
					<h3 class="text-sm font-semibold text-slate-800">{format(shiftCodeText.usedInBranchesCount, { count: formatNumber(group.branches.length, 0) })}</h3>
					<ul class="flex flex-wrap gap-1.5">
						{#each group.branches as branch (branch.id)}
							<li><Badge tone="neutral">{branch.name}</Badge></li>
						{/each}
					</ul>
				</div>
			</div>
		</Card>
	{/snippet}
	{#snippet form(props)}
		<ShiftCodeForm group={props.record} outlets={props.context?.outlets ?? []} categories={props.context?.categories ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as CodeGroupUpdate)} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote(group)}
		<RichText template={shiftCodeText.shiftCodeRemoveNote} values={{ code: group.code, count: group.branches.length }} />
		{#if group.assignments > 0}
			<span class="mt-2 block"><RichText template={shiftCodeText.shiftCodeAssignmentsNote} values={{ count: formatNumber(group.assignments, 0) }} /></span>
		{/if}
	{/snippet}
</RecordDetailView>
