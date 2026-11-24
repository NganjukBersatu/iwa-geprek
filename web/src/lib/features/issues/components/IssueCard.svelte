<script lang="ts">
	import { access } from '$lib/auth/access.svelte';
	import PageButton from '$lib/components/button/PageButton.svelte';
	import TextButton from '$lib/components/button/TextButton.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import { tones, type Tone } from '$lib/components/card/tone';
	import Pager from '$lib/components/pager/Pager.svelte';
	import { pageSize } from '$lib/components/pager/size.svelte';
	import { PREVIEW_ROWS, type IssueGroup } from '../issues.svelte';
	import { issueText } from '$lib/text/issues';
	import { format } from '$lib/text/format';

	let { group, tone, onpage, onexpand }: { group: IssueGroup; tone: Tone; onpage: (page: number) => void; onexpand: () => void } = $props();

	const ROW = 'flex items-center justify-between gap-3 px-4 py-3 text-sm tablet:px-5';
</script>

<Card flush class="flex h-full flex-col">
	<CardHeader divided title={group.title} description={format(issueText.rowsInPeriod, { count: group.total })} {tone}>
		{#snippet actions()}
			<PageButton page={group.link} />
		{/snippet}
	</CardHeader>

	<ul class="flex-1 divide-y divide-slate-100">
		{#each group.rows as row, index (index)}
			<li>
				{#if access.opens(row.link.page.screen)}
					<a href={row.link.path} class="{ROW} hover:bg-brand-page focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand">
						{@render content(row)}
						<i class="ti ti-chevron-right shrink-0 text-slate-400" aria-hidden="true"></i>
					</a>
				{:else}
					<div class={ROW}>{@render content(row)}</div>
				{/if}
			</li>
		{/each}
	</ul>

	{#if group.total > PREVIEW_ROWS}
		<div class="flex flex-col gap-2 border-t border-slate-100 px-4 py-3 text-xs text-slate-500 tablet:px-5">
			{#if group.expanded && group.total > pageSize.value}
				<Pager page={group.page} total={group.total} unit="baris" list={group.kind} onchange={onpage} />
			{/if}
			<TextButton label={group.expanded ? issueText.showLess : format(issueText.viewAllRows, { count: group.total })} onclick={onexpand} />
		</div>
	{/if}
</Card>

{#snippet content(row: IssueGroup['rows'][number])}
	<span class="flex min-w-0 flex-1 flex-col">
		<span class="font-medium text-slate-800">{row.main}</span>
		{#if row.meta}
			<span class="text-xs text-slate-500">{row.meta}</span>
		{/if}
	</span>
	{#if row.figure}
		<span class="shrink-0 text-right font-semibold {tones[tone].ink}">{row.figure}</span>
	{/if}
{/snippet}