<script lang="ts">
	import { issueText } from '$lib/text/issues';
	import Badge from '$lib/components/card/Badge.svelte';
	import { tones } from '$lib/components/card/tone';
	import type { IssueKind } from '$lib/api/types';
	import type { IssueSection } from '../issues.svelte';
	import IssueCard from './IssueCard.svelte';

	let {
		section,
		collapsed,
		ontoggle,
		onpage,
		onexpand
	}: {
		section: IssueSection;
		collapsed: boolean;
		ontoggle: () => void;
		onpage: (kind: IssueKind, page: number) => void;
		onexpand: (kind: IssueKind) => void;
	} = $props();
</script>

<section class="flex flex-col gap-3">
	<button
		type="button"
		onclick={ontoggle}
		aria-expanded={!collapsed}
		class="flex min-h-12 w-full items-center justify-between gap-3 rounded-lg border px-4 text-left {tones[section.tone].banner}"
	>
		<span class="flex items-center gap-2.5">
			<i class="ti ti-{section.icon} text-xl" aria-hidden="true"></i>
			<span class="font-semibold">{section.label}</span>
			<Badge tone={section.tone}>{section.count}</Badge>
		</span>
		<span class="flex items-center gap-1 text-xs font-semibold">
			{collapsed ? issueText.show : issueText.hide}
			<i class="ti ti-chevron-down transition-transform duration-200 motion-reduce:transition-none {collapsed ? '' : 'rotate-180'}" aria-hidden="true"></i>
		</span>
	</button>

	{#if !collapsed}
		<div class="grid grid-cols-1 items-stretch gap-4 laptop:grid-cols-2">
			{#each section.groups as group (group.kind)}
				<IssueCard {group} tone={section.tone} onpage={(page) => onpage(group.kind, page)} onexpand={() => onexpand(group.kind)} />
			{/each}
		</div>
	{/if}
</section>
