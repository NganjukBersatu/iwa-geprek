<script lang="ts">
	import { untrack } from 'svelte';
	import { DatePicker } from '@skeletonlabs/skeleton-svelte';
	import { parseDate, type DateValue } from '@internationalized/date';
	import { lastPickable, type DateRange, type DateReach } from '$lib/date/range';
	import { controlText } from '$lib/text/controls';

	let {
		value = null,
		reach,
		onselect
	}: {
		value?: DateRange | null;
		reach: DateReach;
		onselect: (range: DateRange) => void;
	} = $props();

	const last = $derived(lastPickable(reach));

	const initial: DateValue[] = untrack(() => (value ? [parseDate(value.from), parseDate(value.to)] : []));

	function handleChange(details: { value: DateValue[] }): void {
		const [from, to] = details.value;
		if (from && to) onselect({ from: from.toString(), to: to.toString() });
	}

	const navButton =
		'flex size-8 min-h-0 min-w-0 items-center justify-center rounded-md p-0 text-slate-500 hover:bg-brand-soft data-disabled:opacity-30';
	const dayButton =
		'mx-auto flex size-9 min-h-0 min-w-0 items-center justify-center rounded-lg p-0 text-sm text-slate-700 hover:bg-brand-soft data-in-range:bg-brand-soft data-in-range:text-slate-700 data-selected:bg-brand data-selected:font-semibold data-selected:text-white data-today:no-underline data-today:ring-1 data-today:ring-slate-400 data-disabled:text-slate-300 data-disabled:opacity-100 data-outside-range:text-slate-300';
</script>

<DatePicker
	inline
	selectionMode="range"
	locale="id-ID"
	startOfWeek={1}
	max={last !== null ? parseDate(last) : undefined}
	defaultValue={initial}
	onValueChange={handleChange}
>
	<DatePicker.Content class="w-full gap-0 rounded-none border-0 bg-transparent p-0 shadow-none">
		<DatePicker.View view="day" class="gap-1">
			<DatePicker.Context>
				{#snippet children(datePicker)}
					<DatePicker.ViewControl class="items-center">
						<DatePicker.ViewTrigger class="min-h-0 px-2 py-1 text-sm font-semibold text-brand">
							<DatePicker.RangeText />
						</DatePicker.ViewTrigger>
						<div class="flex gap-1">
							<DatePicker.PrevTrigger class={navButton} aria-label={controlText.previousMonth}>
								<i class="ti ti-chevron-left" aria-hidden="true"></i>
							</DatePicker.PrevTrigger>
							<DatePicker.NextTrigger class={navButton} aria-label={controlText.nextMonth}>
								<i class="ti ti-chevron-right" aria-hidden="true"></i>
							</DatePicker.NextTrigger>
						</div>
					</DatePicker.ViewControl>

					<DatePicker.Table class="w-full table-fixed border-separate border-spacing-x-0 border-spacing-y-0.5">
						<DatePicker.TableHead>
							<DatePicker.TableRow>
								{#each datePicker().weekDays as weekDay (weekDay.long)}
									<DatePicker.TableHeader class="h-8 w-auto text-center text-xs font-medium text-slate-500">{weekDay.short}</DatePicker.TableHeader>
								{/each}
							</DatePicker.TableRow>
						</DatePicker.TableHead>
						<DatePicker.TableBody>
							{#each datePicker().weeks as week, index (index)}
								<DatePicker.TableRow>
									{#each week as day (day.toString())}
										<DatePicker.TableCell value={day} visibleRange={datePicker().visibleRange} class="h-9 w-auto p-0 text-center">
											<DatePicker.TableCellTrigger class={dayButton}>{day.day}</DatePicker.TableCellTrigger>
										</DatePicker.TableCell>
									{/each}
								</DatePicker.TableRow>
							{/each}
						</DatePicker.TableBody>
					</DatePicker.Table>
				{/snippet}
			</DatePicker.Context>
		</DatePicker.View>
	</DatePicker.Content>
</DatePicker>
