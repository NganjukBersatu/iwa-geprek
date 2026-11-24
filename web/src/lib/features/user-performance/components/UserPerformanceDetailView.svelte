<script lang="ts">
	import type { PerformanceRange } from '$lib/api/userPerformance';
	import BackButton from '$lib/components/button/BackButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import type { Tone } from '$lib/components/card/tone';
	import SeriesChart from '$lib/components/chart/SeriesChart.svelte';
	import ShareBar from '$lib/components/chart/ShareBar.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { chartSeries } from '$lib/charts/theme';
	import { formatDayMonth } from '$lib/date/range';
	import { formatNumber } from '$lib/format/currency';
	import { formatDuration } from '$lib/format/datetime';
	import { live } from '$lib/live/live';
	import { PERFORMANCE_TABLES } from '$lib/live/tables';
	import { PAGES } from '$lib/nav/pages';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { format } from '$lib/text/format';
	import { userPerformanceText as t } from '$lib/text/user-performance';
	import { onMount } from 'svelte';
	import { componentLabel, groupLabel, percentText, periodText, RANGE_LABELS, starsText } from '../labels';
	import type { UserPerformanceDetailState } from '../user-performance-detail.svelte';

	let { detail }: { detail: UserPerformanceDetailState } = $props();

	const RANGES: PerformanceRange[] = ['cycle', 'previous', 'all'];
	const tabs = RANGES.map((key) => ({ key, label: RANGE_LABELS[key] }));
	const MINUTES_PER_HOUR = 60;

	function pick(key: string): void {
		const found = RANGES.find((range) => range === key);
		if (found) detail.range = found;
	}

	whenChanged(() => detail.range, () => void detail.load());
	onMount(() => live.on(PERFORMANCE_TABLES, () => void detail.load(true)));

	const performance = $derived(detail.data?.performance ?? null);
	const labels = $derived(performance?.buckets.map((bucket) => formatDayMonth(bucket.start)) ?? []);
	const totalWork = $derived(performance?.buckets.reduce((sum, bucket) => sum + bucket.work_minutes, 0) ?? 0);
	const totalOvertime = $derived(performance?.buckets.reduce((sum, bucket) => sum + bucket.overtime_minutes, 0) ?? 0);
	const composition = $derived.by(() => {
		const parts = performance?.composition;
		if (!parts) return [];
		const total = parts.on_time + parts.late + parts.leave + parts.absent;
		const share = (count: number) => (total > 0 ? (count / total) * 100 : 0);
		const rows: { label: string; count: number; tone: Tone }[] = [
			{ label: t.status.onTime, count: parts.on_time, tone: 'success' },
			{ label: t.status.late, count: parts.late, tone: 'warning' },
			{ label: t.status.leave, count: parts.leave, tone: 'info' },
			{ label: t.status.absent, count: parts.absent, tone: 'danger' }
		];
		return rows.map((row) => ({ ...row, percent: share(row.count) }));
	});
	const subtitle = $derived([detail.data?.role_name, detail.data?.outlet_name ?? t.allBranches].filter(Boolean).join(' · '));
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader title={detail.data?.name ?? t.detailTitle} description={detail.data ? subtitle : undefined}>
		{#snippet leading()}
			<BackButton label={t.back} href={PAGES.userPerformance.path} />
		{/snippet}
	</PageHeader>

	<Tabs {tabs} bind:value={() => detail.range, pick} label={t.rangeLabel} variant="pill" />

	{#if detail.error}
		<Banner tone="danger" icon="alert-triangle" title={t.loadFailedTitle}>
			{detail.error}
			{#snippet action()}
				<Button label={t.retry} variant="danger" onclick={() => void detail.load()} />
			{/snippet}
		</Banner>
	{/if}

	{#if detail.loading && !performance}
		<Notice loading text={t.detailLoading} />
	{:else if performance}
		<p class="text-sm text-slate-600">
			<span class="font-semibold text-slate-800">{periodText(performance.start, performance.end)}</span> · {format(t.countedFrom, { days: formatNumber(performance.counted_days, 0) })}
		</p>

		{#if performance.counted_days === 0}
			<Notice text={t.noData} />
		{:else}
			<Card flush>
				<CardHeader divided title={t.ratingTitle} description={t.ratingDescription} />
				<div class="flex flex-col gap-4 p-4 tablet:p-5">
					<p class="flex items-center gap-2 text-2xl font-bold text-slate-800">
						<i class="ti ti-star" aria-hidden="true"></i>{starsText(performance.rating.stars)}
					</p>
					{#each performance.rating.groups as group (group.key)}
						<div class="flex flex-col gap-1">
							<p class="text-sm font-semibold text-slate-800">{groupLabel(group.key)} · {percentText(group.score)}</p>
							<ul class="flex flex-col divide-y divide-slate-100 rounded-xl border border-slate-200">
								{#each group.components as component (component.key)}
									<li class="flex items-center justify-between gap-3 px-3 py-2 text-sm">
										<span class="text-slate-600">{componentLabel(component.key)}</span>
										<span class="tabular-nums text-slate-800">{percentText(component.percent)} <span class="text-xs text-slate-500">{format(t.componentCounted, { counted: formatNumber(component.counted, 0), of: formatNumber(component.of, 0) })}</span></span>
									</li>
								{/each}
							</ul>
						</div>
					{/each}
				</div>
			</Card>

			<div class="grid gap-4 laptop:grid-cols-2">
				<Card>
					<CardHeader class="mb-4" title={t.onTimeTitle} description={t.onTimeDescription} />
					<SeriesChart
						{labels}
						series={[{ name: t.onTimeTitle, values: performance.buckets.map((bucket) => bucket.on_time_percent ?? 0), color: chartSeries[0] }]}
						format={(value) => `${formatNumber(value, 0)}%`}
						label={t.onTimeChartLabel}
					/>
				</Card>

				<Card>
					<CardHeader class="mb-4" title={t.compositionTitle} />
					<ul class="flex flex-col gap-3">
						{#each composition as row (row.label)}
							<li class="flex flex-col gap-1">
								<div class="flex items-center justify-between text-sm">
									<span class="text-slate-600">{row.label}</span>
									<span class="tabular-nums font-semibold text-slate-800">{format(t.days, { count: formatNumber(row.count, 0) })}</span>
								</div>
								<ShareBar value={row.percent} tone={row.tone} />
							</li>
						{/each}
					</ul>
				</Card>

				<Card>
					<CardHeader class="mb-4" title={t.workHoursTitle} description={format(t.workHoursDescription, { work: formatDuration(totalWork), overtime: formatDuration(totalOvertime) })} />
					<SeriesChart
						{labels}
						series={[{ name: t.workHoursSeries, values: performance.buckets.map((bucket) => Math.floor(bucket.work_minutes / MINUTES_PER_HOUR)), color: chartSeries[0] }]}
						format={(value) => format(t.hoursValue, { count: formatNumber(value, 0) })}
						label={t.workHoursChartLabel}
					/>
				</Card>

				<Card>
					<CardHeader class="mb-4" title={t.tasksTitle} description={format(t.tasksDescription, { done: formatNumber(performance.tasks_done, 0), assigned: formatNumber(performance.tasks_assigned, 0) })} />
					<SeriesChart
						{labels}
						series={[{ name: t.tasksSeries, values: performance.buckets.map((bucket) => bucket.tasks_done), color: chartSeries[0] }]}
						format={(value) => formatNumber(value, 0)}
						label={t.tasksChartLabel}
					/>
				</Card>
			</div>
		{/if}
	{/if}
</div>
