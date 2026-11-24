<script lang="ts" generics="Q extends ReportQuery, D extends { start: string; end: string }">
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { syncBranchPeriod } from './branch-period.svelte';
	import { onMount, type Snippet } from 'svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import FilterButton from '$lib/components/filter/FilterButton.svelte';
	import FilterChips from '$lib/components/filter/FilterChips.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import { live } from '$lib/live/live';
	import Reveal from '$lib/components/motion/Reveal.svelte';
	import { loadBranchOptions } from '$lib/stores/branch';
	import type { ReportQuery, ReportState } from './report.svelte';
	import { actionText } from '$lib/text/actions';
	import { listText } from '$lib/text/lists';
	import { format } from '$lib/text/format';

	let {
		report,
		title,
		description,
		extra,
		children
	}: {
		report: ReportState<Q, D>;
		title: string;
		description: string;
		extra?: Snippet;
		children: Snippet<[D]>;
	} = $props();

	syncBranchPeriod(() => report.filters);
	whenChanged(() => report.query, (query) => void report.queryChanged(query));

	onMount(() => {
		void loadBranchOptions().then((options) => report.setBranches(options));
		return live.on(report.tables, () => void report.refresh());
	});
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader {title} {description}>
		{#snippet actions()}
			<FilterButton filters={report.filters} />
			{@render extra?.()}
		{/snippet}
	</PageHeader>

	<FilterChips filters={report.filters} />

	{#if report.error}
		<Banner tone="danger" icon="alert-triangle" title={listText.reportLoadFailedTitle}>
			{report.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void report.load()} />
			{/snippet}
		</Banner>
	{:else if report.loading && !report.data}
		<SkeletonPage label={format(listText.reportLoadingPeriod, { period: report.periodLabel })} />
	{:else if report.data}
		<Reveal>
			{@render children(report.data)}
		</Reveal>
	{/if}
</div>
