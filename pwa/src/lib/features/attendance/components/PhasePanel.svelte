<script lang="ts">
	import { onMount } from 'svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import Chip from '$lib/components/choice/Chip.svelte';
	import SegmentBar from '$lib/components/chart/SegmentBar.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { activeSegment, type DaySegment, type SegmentKind } from '$lib/features/dayplan/dayplan.svelte';
	import { durationLabel, timeRange } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import { ServerClock } from '$lib/time/server-clock';

	const TICK_MILLIS = 1000;
	const SECONDS_PER_MINUTE = 60;

	/** Rentang jam yang ditampilkan: hanya kerja, semuanya, atau hanya lembur. */
	type PhaseFilter = 'work' | 'all' | 'overtime';

	/** Bilah seluruh rentang hari ini dengan rincian rentang yang aktif atau yang diketuk di bawahnya. */
	let { segments, clockedIn }: { segments: readonly DaySegment[]; clockedIn: boolean } = $props();

	let now = $state(ServerClock.nowEpochSeconds());
	let filter = $state<PhaseFilter>('all');
	let selectedIndex = $state<number | null>(null);

	onMount(() => {
		const timer = setInterval(() => (now = ServerClock.nowEpochSeconds()), TICK_MILLIS);
		return () => clearInterval(timer);
	});

	// Pilihan bagian dilepas bila daftar atau penyaringnya berganti.
	$effect(() => {
		void segments;
		void filter;
		selectedIndex = null;
	});

	const visible = $derived(filter === 'work' ? segments.filter((segment) => !segment.isOvertime) : filter === 'overtime' ? segments.filter((segment) => segment.isOvertime) : segments);
	const active = $derived(activeSegment(segments, now, clockedIn));
	const shown = $derived((selectedIndex !== null ? visible[selectedIndex] : undefined) ?? (active && visible.includes(active) ? active : null));

	const labels = $derived<[PhaseFilter, string][]>([
		['work', t('phase_filter_work')],
		['all', t('phase_filter_all')],
		['overtime', t('phase_filter_overtime')]
	]);

	const phaseLabel = (kind: SegmentKind): string => (kind === 'work' ? t('phase_work') : kind === 'scheduled-overtime' ? t('phase_overtime') : t('phase_overtime_unplanned'));

	const title = $derived(shown ? t('phase_title', phaseLabel(shown.kind), timeRange(shown.start.time, shown.end.time)) : t('phase_none'));
	const detail = $derived.by(() => {
		if (!shown) return t('phase_hint');
		if (shown === active) {
			const left = Math.max(0, Math.floor((shown.endEpoch - now) / SECONDS_PER_MINUTE));
			return t('phase_duration_remaining', durationLabel(shown.minutes), durationLabel(left));
		}
		return t('phase_duration', durationLabel(shown.minutes));
	});
</script>

<ListCard>
	<div class="flex w-full flex-col items-center gap-3 p-3">
		<div class="flex flex-wrap justify-center gap-2">
			{#each labels as [option, label] (option)}
				<Chip {label} selected={filter === option} onclick={() => (filter = option)} />
			{/each}
		</div>
		{#if visible.length > 0}
			<SegmentBar
				segments={visible.map((segment) => ({
					weight: segment.minutes,
					progress: (now - segment.startEpoch) / (segment.endEpoch - segment.startEpoch),
					tone: segment.isOvertime ? 'accent' : 'primary'
				}))}
				onselect={(index) => (selectedIndex = selectedIndex === index ? null : index)}
			/>
		{/if}
		<AppText role="title" align="center">{title}</AppText>
		<AppText role="caption" color="content-muted" align="center">{detail}</AppText>
	</div>
</ListCard>
