<script lang="ts">
	import { tones } from '$lib/components/card/tone';
	import { roleTone } from '../person-tone';
	import { goto } from '$app/navigation';
	import { assignmentNewPath, assignmentPath } from '$lib/nav/pages';
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import { dayLabel, formatDayMonth, todayIso } from '$lib/date/range';
	import type { Drag } from '../drag.svelte';
	import type { ScheduleState } from '../schedule.svelte';
	import AttendanceMark from './AttendanceMark.svelte';
	import ShiftCodeBadge from '$lib/components/card/ShiftCodeBadge.svelte';
	import { termText } from '$lib/text/terms';
	import { scheduleText } from '$lib/text/schedule';
	import { format } from '$lib/text/format';

	let { schedule, drag }: { schedule: ScheduleState; drag: Drag } = $props();

	const today = todayIso();
	const draggable = $derived(schedule.canArrange);
</script>

<div class="flex flex-col gap-4">
	{#if schedule.canArrange}
		<Card>
			<div>
				<h3 class="text-sm font-semibold text-slate-800">{termText.employee}</h3>
				<p class="mt-1 text-xs text-slate-500">{scheduleText.boardHelp}</p>
			</div>
			<div class="mt-3 flex min-h-12 flex-wrap gap-2 rounded-lg border border-dashed p-2 {drag.over?.kind === 'pool' ? 'border-brand bg-brand-page' : 'border-brand-line bg-brand-soft'}" data-drop="pool">
				{#each schedule.pool as person (person.id)}
					<button type="button" onpointerdown={(event) => drag.start(event, { kind: 'pool', userId: person.id, label: person.name || person.username })} class="touch-none cursor-grab rounded-lg border px-3 py-1.5 text-xs font-semibold shadow-sm hover:brightness-95 {tones[roleTone(person.role_name)].pill}" aria-label={format(scheduleText.dragName, { name: person.name || person.username })}>
						{person.name || person.username}<span class="font-normal opacity-80">{' · '}{person.role_name}</span>
					</button>
				{:else}
					<p class="self-center px-1 text-xs text-slate-500">{scheduleText.noActiveEmployees}</p>
				{/each}
			</div>
		</Card>
	{/if}

	<div class="grid grid-cols-2 gap-2 tablet:grid-cols-4 laptop:grid-cols-7" role="list" data-drag-scroll>
		{#each schedule.dates as date (date)}
			{@const label = dayLabel(date)}
			{@const dropping = drag.over?.kind === 'date' && drag.over.date === date}
			<section class="flex min-w-0 flex-col rounded-xl border {dropping ? 'border-brand bg-brand-page' : date === today ? 'border-brand bg-white' : 'border-slate-200 bg-white'}" data-drop="date" data-date={date} role="listitem" aria-label={format(scheduleText.scheduleOf, { date: date })}>
				<header class="flex flex-wrap items-baseline justify-between gap-x-2 border-b border-slate-100 px-2 py-2">
					<span class="text-xs font-semibold {label.sunday ? 'text-danger-700' : 'text-slate-800'}">{label.weekday} {formatDayMonth(date)}</span>
					{#if date === today}<span class="text-xs font-semibold text-brand">{scheduleText.today}</span>{/if}
				</header>
				<div class="flex min-h-24 flex-1 flex-col gap-1.5 p-1.5">
					{#each schedule.itemsOn(date) as item (item.id)}
						{@const over = drag.over?.kind === 'assignment' && drag.over.id === item.id}
						<div
							class="rounded-lg border bg-white p-2 text-left shadow-sm {draggable ? 'touch-none cursor-grab' : ''} {over ? 'border-brand ring-2 ring-brand-line' : 'border-slate-200'} {drag.item?.kind === 'assignment' && drag.item.id === item.id ? 'opacity-40' : ''}"
							data-drop="assignment"
							data-id={item.id}
							role="button"
							tabindex="0"
							onpointerdown={(event) => (draggable ? drag.start(event, { kind: 'assignment', id: item.id, label: item.user_username }) : undefined)}
							onclick={() => (draggable ? undefined : void goto(assignmentPath(item.id)))}
							onkeydown={(event) => event.key === 'Enter' && void goto(assignmentPath(item.id))}
						>
							<p class="text-sm font-semibold text-slate-800 wrap-break-word">{item.user_username}</p>
							<div class="mt-1 flex flex-wrap items-center gap-1">
								<ShiftCodeBadge code={schedule.codeOf(item.shift_code_id)} showTime />
								{#if item.role_name}<span class="text-xs text-slate-500">{item.role_name}</span>{/if}
							</div>
							<div class="mt-1"><AttendanceMark record={schedule.attendanceFor(item)} /></div>
						</div>
					{/each}
					{#each schedule.daysOffOn(date) as off (off.id)}
						{#if schedule.canArrange}
							<button type="button" class="w-full truncate rounded-lg border border-dashed border-slate-200 bg-slate-50 px-2 py-1.5 text-left text-xs text-slate-500 hover:bg-brand-soft" aria-label={format(scheduleText.unassignDayOffOf, { name: off.user_username })} onclick={() => (schedule.releasingOff = off)}>
								<span class="font-semibold text-slate-600">{off.user_username}</span> {scheduleText.dayOffSuffix}
							</button>
						{:else}
							<div class="truncate rounded-lg border border-dashed border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-500">
								<span class="font-semibold text-slate-600">{off.user_username}</span> {scheduleText.dayOffSuffix}
							</div>
						{/if}
					{/each}
					{#if schedule.canArrange}
						<div class="mt-auto"><Button label={scheduleText.add} icon="plus" class="w-full" onclick={() => void goto(assignmentNewPath(date))} /></div>
					{/if}
				</div>
			</section>
		{/each}
	</div>
</div>
