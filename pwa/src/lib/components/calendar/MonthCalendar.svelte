<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';
	import { dateOf, daysInMonth, firstDay, weekdayIndex, type YearMonth } from '$lib/format/datetime';
	import { luminance } from '$lib/theme/hex';
	import MonthPicker from './MonthPicker.svelte';

	const MAX_MARKERS = 3;
	/** Batas terang warna blok: di bawahnya teks tanggal putih, di atasnya gelap. */
	const LUMINANCE_SPLIT = 0.5;
	const DAYS_IN_WEEK = 7;

	/** Kalender satu bulan (minggu mulai Senin) dengan titik warna, warna kotak, kotak berdenyut, dan [weekdayLabels] berurutan Minggu sampai Sabtu. */
	let {
		month,
		monthLabel,
		weekdayLabels,
		selected,
		today,
		markers,
		fills,
		pulses = {},
		onSelect,
		onPrevious,
		onNext,
		nextEnabled,
		footer
	}: {
		month: YearMonth;
		monthLabel: string;
		weekdayLabels: readonly string[];
		selected: string;
		today: string;
		markers: Record<string, (string | null)[]>;
		fills: Record<string, string>;
		/** Tanggal yang berdenyut, dengan warna cincinnya; null memakai warna utama. */
		pulses?: Record<string, string | null>;
		onSelect: (date: string) => void;
		onPrevious: () => void;
		onNext: () => void;
		nextEnabled: boolean;
		footer?: Snippet;
	} = $props();

	const leading = $derived((weekdayIndex(firstDay(month)) + 6) % DAYS_IN_WEEK);
	const cells = $derived<(number | null)[]>([...Array.from({ length: leading }, () => null), ...Array.from({ length: daysInMonth(month) }, (_, index) => index + 1)]);
	const weeks = $derived(Array.from({ length: Math.ceil(cells.length / DAYS_IN_WEEK) }, (_, index) => cells.slice(index * DAYS_IN_WEEK, (index + 1) * DAYS_IN_WEEK)));
	const orderedLabels = $derived([...weekdayLabels.slice(1), ...weekdayLabels.slice(0, 1)]);

	function numberColor(isSelected: boolean, fill: string | undefined): string {
		if (isSelected) return 'text-on-primary';
		if (fill) return luminance(fill) < LUMINANCE_SPLIT ? 'text-on-primary' : 'text-content';
		return 'text-content';
	}
</script>

<div class="flex w-full flex-col gap-1 rounded-card border border-divider bg-surface p-2">
	<MonthPicker label={monthLabel} {onPrevious} {onNext} {nextEnabled} />
	<div class="flex w-full">
		{#each orderedLabels as label (label)}
			<span class="text-caption flex-1 text-center text-content-muted">{label}</span>
		{/each}
	</div>
	{#each weeks as week, weekIndex (weekIndex)}
		<div class="flex w-full">
			{#each { length: DAYS_IN_WEEK } as _, column (column)}
				{@const day = week[column]}
				{#if day == null}
					<span class="h-12 flex-1"></span>
				{:else}
					{@const date = dateOf(month, day)}
					{@const isSelected = date === selected}
					{@const fill = fills[date]}
					{@const pulse = date in pulses ? (pulses[date] ?? 'var(--color-primary)') : null}
					<div class="h-12 flex-1 p-[2px]">
						<button
							type="button"
							onclick={() => onSelect(date)}
							class="relative flex size-full flex-col items-center justify-center rounded-field {isSelected ? 'bg-primary' : ''} {date === today && !isSelected ? 'border-[1.5px] border-primary' : ''}"
							use:dynamicStyle={{ 'background-color': !isSelected && fill ? fill : undefined }}
						>
							{#if pulse && !isSelected}
								<span
									class="pulse-ring-loop pointer-events-none absolute inset-0 rounded-field border-2"
									use:dynamicStyle={{ 'border-color': pulse }}
								></span>
							{/if}
							<span class="text-body {numberColor(isSelected, fill)}">{day}</span>
							<span class="flex h-3 gap-1 pt-1">
								{#each (markers[date] ?? []).slice(0, MAX_MARKERS) as color, index (index)}
									<span class="size-2 rounded-full {color ? '' : isSelected ? 'bg-on-primary' : 'bg-content-muted'}" use:dynamicStyle={{ 'background-color': color }}></span>
								{/each}
							</span>
						</button>
					</div>
				{/if}
			{/each}
		</div>
	{/each}
	{#if footer}
		<div class="py-1"><Divider /></div>
		{@render footer()}
	{/if}
</div>
