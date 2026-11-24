<script lang="ts" generics="T extends { id: string }">
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import BackButton from '$lib/components/button/BackButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import BulkResultDialog from '$lib/components/dialog/BulkResultDialog.svelte';
	import FilterButton from '$lib/components/filter/FilterButton.svelte';
	import FilterChips from '$lib/components/filter/FilterChips.svelte';
	import type { Filters } from '$lib/components/filter/filters.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import { live } from '$lib/live/live';
	import Reveal from '$lib/components/motion/Reveal.svelte';
	import { syncBranchPeriod } from '../report/branch-period.svelte';
	import type { ManageState } from './manage.svelte';
	import { actionText } from '$lib/text/actions';
	import { listText } from '$lib/text/lists';

	let {
		manage,
		title,
		description,
		loadingText,
		filters,
		back,
		actions: extra,
		children
	}: {
		manage: ManageState<T>;
		title: string;
		description: string;
		loadingText: string;
		filters?: Filters;
		/** A list that sits under another page returns to it; the label names that page. */
		back?: { label: string; path: string };
		actions?: Snippet;
		children: Snippet;
	} = $props();

	syncBranchPeriod(
		() => filters,
		(branchId) => manage.branchPeriod?.(branchId) ?? Promise.resolve(null)
	);
	whenChanged(() => manage.query, () => void manage.queryChanged());
	onMount(() => (manage.tables.length > 0 ? live.on(manage.tables, () => void manage.refresh()) : undefined));
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader {title} {description}>
		{#snippet leading()}
			{#if back}<BackButton label={back.label} href={back.path} />{/if}
		{/snippet}
		{#snippet actions()}
			{#if filters}<FilterButton {filters} />{/if}
			{@render extra?.()}
		{/snippet}
	</PageHeader>

	{#if filters}<FilterChips {filters} />{/if}

	{#if manage.error}
		<Banner tone="danger" icon="alert-triangle" title={listText.loadFailedTitle}>
			{manage.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void manage.load()} />
			{/snippet}
		</Banner>
	{:else if manage.loading && !manage.loaded}
		<SkeletonPage stats={0} label={loadingText} />
	{:else}
		<Reveal>
			{@render children()}
		</Reveal>
	{/if}
</div>

<BulkResultDialog result={manage.outcome?.result ?? null} names={manage.outcome?.names ?? []} verb={manage.outcome?.verb ?? ''} onclose={() => (manage.outcome = null)} />
