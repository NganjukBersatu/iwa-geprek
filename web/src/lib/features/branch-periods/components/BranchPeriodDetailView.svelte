<script lang="ts">
	import { onMount } from 'svelte';
	import { access } from '$lib/auth/access.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import { formatDate } from '$lib/date/range';
	import { BRANCH_TABS, PAGES, branchPath } from '$lib/nav/pages';
	import { actionText } from '$lib/text/actions';
	import { branchPeriodText as text } from '$lib/text/branch-periods';
	import { format } from '$lib/text/format';
	import type { BranchPeriodDetailState } from '../branch-period-detail.svelte';
	import { periodSource } from '../columns';
	import { periodLabel } from '../period-label';
	import PeriodEditDialog from './PeriodEditDialog.svelte';

	let { detail }: { detail: BranchPeriodDetailState } = $props();

	onMount(() => void detail.load());

	const period = $derived(detail.data);
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageIntro
		title={period ? format(text.pageTitle, { period: periodLabel(period) }) : text.pageFallbackTitle}
		description={period?.outlet_name}
		items={[
			{ label: PAGES.branches.label, href: PAGES.branches.path },
			{ label: period?.outlet_name ?? text.back, href: branchPath(detail.outletId, BRANCH_TABS.periods) },
			{ label: period ? periodLabel(period) : text.pageFallbackTitle }
		]}
	>
		{#snippet actions()}
			{#if period && access.allows('manage_branches')}
				<Button label={actionText.edit} icon="pencil" variant="primary" onclick={() => detail.openEdit()} />
				{#if period.adjusted && !period.sets_pattern}
					<Button label={text.reset} icon="restore" onclick={() => detail.askReset()} />
				{/if}
			{/if}
		{/snippet}
	</PageIntro>

	{#if detail.error}
		<Banner tone="danger" icon="alert-triangle" title={text.loadFailedTitle}>
			{detail.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void detail.load()} />
			{/snippet}
		</Banner>
	{/if}

	{#if detail.loading && !period}
		<Notice loading text={text.loading} />
	{:else if period}
		<Card flush>
			<CardHeader divided title={text.rangeTitle} description={text.rangeDescription} />
			<div class="flex flex-col gap-4 p-4 tablet:p-5">
				<span class="inline-flex flex-wrap items-center gap-1">
					<Badge tone={period.running ? 'success' : 'neutral'}>{period.running ? text.running : text.past}</Badge>
					<Badge tone={periodSource(period).tone}>{periodSource(period).label}</Badge>
				</span>
				{#if period.sets_pattern}
					<p class="text-xs text-slate-500">{text.patternNote}</p>
				{/if}
				<dl class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm tablet:grid-cols-4">
					<div>
						<dt class="text-xs text-slate-500">{text.start}</dt>
						<dd class="font-semibold text-slate-800">{formatDate(period.start)}</dd>
					</div>
					<div>
						<dt class="text-xs text-slate-500">{text.end}</dt>
						<dd class="font-semibold text-slate-800">{formatDate(period.end)}</dd>
					</div>
				</dl>
			</div>
		</Card>
	{/if}
</div>

{#if period && detail.editing}
	<PeriodEditDialog {period} busy={detail.busy} error={detail.actionError} onsave={(change) => void detail.save(change)} onclose={() => detail.closeDialogs()} />
{/if}

<ConfirmDialog
	open={detail.resetting}
	title={text.resetTitle}
	confirmLabel={text.resetConfirm}
	busy={detail.busy}
	error={detail.actionError}
	onconfirm={() => void detail.reset()}
	oncancel={() => detail.closeDialogs()}
>
	<strong class="text-slate-800">{period ? periodLabel(period) : ''}</strong>
	{text.resetNote}
</ConfirmDialog>
