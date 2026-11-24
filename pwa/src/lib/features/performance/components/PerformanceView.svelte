<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';
	import DetailRow from '$lib/components/card/DetailRow.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ColumnChart from '$lib/components/chart/ColumnChart.svelte';
	import DonutChart from '$lib/components/chart/DonutChart.svelte';
	import RatingCard from '$lib/components/chart/RatingCard.svelte';
	import SegmentedControl from '$lib/components/choice/SegmentedControl.svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import LoadingState from '$lib/components/feedback/LoadingState.svelte';
	import SectionTitle from '$lib/components/feedback/SectionTitle.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { dayOfMonth, monthIndex } from '$lib/format/datetime';
	import { durationLabel, longDateLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import { componentLabel, groupLabel, PERFORMANCE_RANGES, percentText, PerformanceState, starsText } from '../performance.svelte';

	const MINUTES_PER_HOUR = 60;

	/** Halaman Kinerja: pilihan rentang, tanggal rentang, lalu grafik; setiap angka hanya tampil satu kali. */
	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const performance = new PerformanceState(() => onSessionExpired());

	$effect(() => {
		void performance.load();
	});

	const data = $derived(performance.performance);
	const labels = $derived((data?.buckets ?? []).map((bucket) => `${dayOfMonth(bucket.start)}/${monthIndex(bucket.start) + 1}`));
	const stars = $derived(data?.rating.stars ?? null);
</script>

{#snippet chartCard(title: string, caption: string | null, chart: Snippet)}
	<div>
		<SectionTitle text={title} padded={false} class="pb-2" />
		<ListCard>
			<div class="flex w-full flex-col gap-2 p-3">
				{#if caption}<AppText role="caption" color="content-muted">{caption}</AppText>{/if}
				{@render chart()}
			</div>
		</ListCard>
	</div>
{/snippet}

<div class="flex size-full justify-center overflow-y-auto" use:dynamicStyle={{ 'padding-inline': 'var(--page-padding)' }}>
	<div class="flex w-full max-w-[var(--size-content-max)] flex-col gap-3" use:dynamicStyle={{ 'padding-bottom': '24px' }}>
		<SegmentedControl
			options={PERFORMANCE_RANGES.map((range) => t(range.label))}
			selectedIndex={PERFORMANCE_RANGES.indexOf(performance.range)}
			onselect={(index) => {
				const range = PERFORMANCE_RANGES[index];
				if (range) performance.select(range);
			}}
		/>
		{#if performance.failure}
			<ListCard><FailureState failure={performance.failure} onRetry={() => performance.retry()} /></ListCard>
		{:else if performance.loading || !data}
			<LoadingState />
		{:else}
			<AppText role="label">{t('performance_period', longDateLabel(data.start), longDateLabel(data.end))}</AppText>
			<AppText role="caption" color="content-muted">{t('performance_counted', String(data.countedDays))}</AppText>
			{#if data.countedDays === 0}
				<AppText role="body" color="content-muted">{t('performance_empty')}</AppText>
			{:else}
				<div>
					<SectionTitle text={t('performance_rating_title')} padded={false} class="pb-2" />
					<RatingCard
						stars={stars ?? 0}
						valueText={stars === null ? t('performance_rating_none') : t('performance_rating_value', starsText(stars))}
						starsDescription={t('performance_rating_stars_description', starsText(stars ?? 0))}
						openLabel={t('performance_rating_open')}
						closeLabel={t('performance_rating_close')}
						details={stars === null ? undefined : ratingDetails}
					/>
				</div>
				{@render chartCard(
					t('performance_ontime_title'),
					t('performance_ontime_caption'),
					ontime
				)}
				{@render chartCard(t('performance_composition_title'), null, composition)}
				{@render chartCard(t('performance_hours_title'), t('performance_hours_caption', durationLabel(data.workMinutes), durationLabel(data.overtimeMinutes)), hours)}
				{@render chartCard(t('performance_tasks_title'), t('performance_tasks_caption', String(data.tasksDone), String(data.tasksAssigned)), tasks)}
			{/if}
		{/if}
	</div>
</div>

{#snippet ratingDetails()}
	{#each data?.rating.groups ?? [] as group, index (group.key)}
		{#if index > 0}<Divider />{/if}
		<SectionTitle text={groupLabel(group.key)} padded={false} class="pl-3 pt-3" />
		{#each group.components as component (component.key)}
			<DetailRow label={componentLabel(component.key)} value={percentText(component.percent)} />
		{/each}
	{/each}
{/snippet}

{#snippet ontime()}
	<ColumnChart values={(data?.buckets ?? []).map((bucket) => bucket.onTimePercent ?? 0)} {labels} axisText={(value) => `${value}%`} />
{/snippet}

{#snippet composition()}
	<DonutChart
		slices={[
			{ label: t('performance_slice_on_time'), value: data?.composition.onTime ?? 0, color: 'var(--color-success)' },
			{ label: t('performance_slice_late'), value: data?.composition.late ?? 0, color: 'var(--color-warning)' },
			{ label: t('performance_slice_leave'), value: data?.composition.leave ?? 0, color: 'var(--color-info)' },
			{ label: t('performance_slice_absent'), value: data?.composition.absent ?? 0, color: 'var(--color-danger)' }
		]}
		valueText={(value) => String(value)}
	/>
{/snippet}

{#snippet hours()}
	<ColumnChart values={(data?.buckets ?? []).map((bucket) => Math.floor(bucket.workMinutes / MINUTES_PER_HOUR))} {labels} axisText={(value) => String(value)} />
{/snippet}

{#snippet tasks()}
	<ColumnChart values={(data?.buckets ?? []).map((bucket) => bucket.tasksDone)} {labels} axisText={(value) => String(value)} />
{/snippet}
