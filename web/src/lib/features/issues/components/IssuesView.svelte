<script lang="ts">
	import { listText } from '$lib/text/lists';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { onMount } from 'svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import FilterButton from '$lib/components/filter/FilterButton.svelte';
	import FilterChips from '$lib/components/filter/FilterChips.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import Reveal from '$lib/components/motion/Reveal.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import { live } from '$lib/live/live';
	import { ISSUE_TABLES } from '$lib/live/tables';
	import { loadBranchOptions } from '$lib/stores/branch';
	import { IssuesState } from '../issues.svelte';
	import IssueSection from './IssueSection.svelte';
	import { actionText } from '$lib/text/actions';
	import { issueText } from '$lib/text/issues';

	const issues = new IssuesState();
	const sections = $derived(issues.sections);
	const shown = $derived(sections.filter((section) => section.groups.length > 0));

	whenChanged(() => issues.branch, () => void issues.load());

	onMount(() => {
		void loadBranchOptions().then((options) => issues.setBranches(options));
		return live.on(ISSUE_TABLES, () => void issues.refresh());
	});
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader title={issueText.title} description={issueText.description}>
		{#snippet actions()}
			<FilterButton filters={issues.filters} />
		{/snippet}
	</PageHeader>

	<FilterChips filters={issues.filters} />

	{#if issues.error}
		<Banner tone="danger" icon="alert-triangle" title={listText.reportLoadFailedTitle}>
			{issues.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void issues.load()} />
			{/snippet}
		</Banner>
	{:else if issues.loading && !issues.data}
		<SkeletonPage label={issueText.loading} />
	{:else if issues.data}
		<Reveal>
			<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
				{#each sections as section (section.level)}
					<SummaryCard label={section.label} caption={section.caption} value={String(section.count)} icon={section.icon} accent={section.accent} expanded={section.groups.length > 0 ? !issues.isCollapsed(section.level, sections) : undefined} onclick={section.groups.length > 0 ? () => issues.toggle(section.level, sections) : undefined} />
				{/each}
			</div>

			{#if shown.length === 0}
				<Banner tone="success" icon="circle-check" title={issueText.noIssues} />
			{/if}

			{#each shown as section (section.level)}
				<IssueSection
					{section}
					collapsed={issues.isCollapsed(section.level, sections)}
					ontoggle={() => issues.toggle(section.level, sections)}
					onpage={(kind, page) => issues.setPage(kind, page)}
					onexpand={(kind) => issues.expand(kind)}
				/>
			{/each}
		</Reveal>
	{/if}
</div>
