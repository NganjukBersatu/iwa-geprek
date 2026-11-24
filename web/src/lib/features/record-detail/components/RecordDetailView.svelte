<script lang="ts" generics="T, U, C">
	import { goto } from '$app/navigation';
	import { onMount, type Snippet } from 'svelte';
	import BackButton from '$lib/components/button/BackButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import { live } from '$lib/live/live';
	import type { Page } from '$lib/nav/pages';
	import { editAddress } from '../edit-address.svelte';
	import type { RecordDetailState } from '../record-detail.svelte';

	/** What an edit form is handed: the record, what it needs besides, and how to report back. */
	type FormProps = {
		record: T;
		context: C | null;
		busy: boolean;
		error: string;
		fieldErrors: Record<string, string>;
		onsave: (body: U) => void;
		onclose: () => void;
	};

	let {
		detail,
		back,
		tables,
		title,
		description,
		badge: badgeOf,
		extraActions,
		trail,
		body,
		form,
		removeNote,
		editable = () => true,
		removable = () => true,
		removeBusy = false
	}: {
		detail: RecordDetailState<T, U, C>;
		/** The list this page returns to. */
		back: Page;
		/** The tables whose changes reload this page. */
		tables: string[];
		title: (record: T) => string;
		description?: (record: T, context: C | null) => string;
		badge?: Snippet<[T]>;
		/** The trail to this page; with it the top is the trail, title and explanation, and there is no back arrow. */
		trail?: (record: T) => { label: string; href?: string }[];
		extraActions?: Snippet<[T]>;
		body: Snippet<[T, C | null]>;
		form?: Snippet<[FormProps]>;
		removeNote?: Snippet<[T]>;
		/** False greys out Ubah with the reason from the page text; the server still decides. */
		editable?: (record: T) => boolean;
		removable?: (record: T) => boolean;
		/** True while something the confirmation depends on is still being read; the confirm waits for it. */
		removeBusy?: boolean;
	} = $props();

	const text = $derived(detail.config.text);
	const address = editAddress();
	const record = $derived(detail.record);

	onMount(() => {
		detail.resetForm();
		void detail.load();
		return live.on(tables, () => void detail.refresh());
	});

	async function saveAndReturn(value: U): Promise<void> {
		if (await detail.save(value)) void goto(address.recordPath);
	}

	async function remove(): Promise<void> {
		if (await detail.delete()) void goto(back.path);
	}
</script>

{#if detail.error}
	<Banner tone="danger" icon="alert-triangle" title={text.loadFailed}>
		{detail.error}
		{#snippet action()}
			<Button label={text.retry} onclick={() => void detail.load()} />
		{/snippet}
	</Banner>
{:else if record && address.editing && form && detail.config.update && editable(record)}
	{@render form({
		record,
		context: detail.context,
		busy: detail.busy,
		error: detail.actionError,
		fieldErrors: detail.fieldErrors,
		onsave: (value) => void saveAndReturn(value),
		onclose: () => void goto(address.recordPath)
	})}
{:else if record}
	<div class="flex flex-col gap-4 tablet:gap-6">
		{#snippet controls()}
			{#if extraActions}{@render extraActions(record)}{/if}
			{#if detail.config.update}
				<Button label={text.edit} icon="pencil" variant="primary" disabled={detail.busy || !editable(record)} hint={text.locked} onclick={() => void goto(address.editPath)} />
			{/if}
			{#if detail.config.remove}
				<Button label={text.remove} icon="trash" variant="danger" disabled={detail.busy || !removable(record)} hint={text.locked} onclick={() => detail.askRemove()} />
			{/if}
		{/snippet}
		{#if trail}
			<PageIntro title={title(record)} description={description?.(record, detail.context)} items={trail(record)}>
				{#snippet badge()}
					{#if badgeOf}{@render badgeOf(record)}{/if}
				{/snippet}
				{#snippet actions()}
					{@render controls()}
				{/snippet}
			</PageIntro>
		{:else}
			<PageHeader title={title(record)} description={description?.(record, detail.context)}>
				{#snippet leading()}
					<BackButton label={text.back} href={back.path} />
				{/snippet}
				{#snippet actions()}
					{#if badgeOf}{@render badgeOf(record)}{/if}
					{@render controls()}
				{/snippet}
			</PageHeader>
		{/if}

		{#if detail.actionError && !detail.removing}
			<Banner tone="danger" icon="alert-triangle">{detail.actionError}</Banner>
		{/if}

		{@render body(record, detail.context)}
	</div>

	{#if detail.config.remove}
		<ConfirmDialog open={detail.removing} title={text.removeTitle} confirmLabel={text.remove} danger busy={detail.busy || removeBusy} error={detail.actionError} onconfirm={() => void remove()} oncancel={() => detail.closeDialogs()}>
			{#if removeNote}{@render removeNote(record)}{/if}
		</ConfirmDialog>
	{/if}
{:else}
	<Notice loading text={text.loading} />
{/if}
