<script lang="ts">
	import type { Snippet } from 'svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import { formPageText } from '$lib/text/form';
	import { unsavedChanges } from './unsaved-changes.svelte';

	/** A form on a page of its own: back arrow and title above, groups of fields (FormSection) in one card that uses the width, and the actions in a bar that stays at the bottom edge. */
	let {
		title,
		description,
		busy = false,
		stacked = false,
		wide = false,
		trail,
		onclose,
		children,
		footer
	}: {
		title: string;
		description?: string;
		busy?: boolean;
		/** Each group is a card of its own (FormSection with an icon) instead of all groups sharing one card. */
		stacked?: boolean;
		/** The card and the action bar use the whole width instead of stopping at the form width. */
		wide?: boolean;
		/** The trail to this page; with it the top is the trail, the title and the explanation, and there is no back arrow. */
		trail?: { label: string; href?: string }[];
		/** Kept so the forms moved from dialogs read the same; a page is as wide as the screen allows. */
		size?: 'sm' | 'md' | 'lg';
		onclose: () => void;
		children: Snippet;
		footer?: Snippet;
	} = $props();

	// A save in progress ends the question about unsaved changes; a refused save is edited again, which marks the form again.
	$effect(() => {
		if (busy) unsavedChanges.clear();
	});
</script>

<div class="flex flex-col gap-3 tablet:gap-4" use:unsavedChanges.watch>
	{#if trail}
		<PageIntro {title} {description} items={trail} />
	{:else}
		<PageHeader {title} {description}>
			{#snippet leading()}
				<Button label={formPageText.back} icon="arrow-left" variant="tertiary" small compact iconOnly disabled={busy} onclick={onclose} />
			{/snippet}
		</PageHeader>
	{/if}

	{#if stacked}
		<div class="flex flex-col gap-3 tablet:gap-4">{@render children()}</div>
	{:else}
		<Card class="{wide ? '' : 'max-w-6xl'} divide-y divide-slate-100 tablet:p-6">{@render children()}</Card>
	{/if}

	{#if footer}
		<div class="sticky bottom-0 z-10 -mx-4 flex {stacked || wide ? '' : 'max-w-6xl'} flex-row flex-wrap items-center gap-2 border-t border-slate-100 bg-white px-4 py-3 tablet:mx-0 tablet:rounded-xl tablet:border">{@render footer()}</div>
	{/if}
</div>
