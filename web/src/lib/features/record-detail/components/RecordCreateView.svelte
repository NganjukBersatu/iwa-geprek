<script lang="ts" generics="T, U, C">
	import { goto } from '$app/navigation';
	import { onMount, type Snippet } from 'svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import type { Page } from '$lib/nav/pages';
	import type { RecordCreateState } from '../record-create.svelte';

	/** What a new-record form is handed: the same shape as an edit form, with no record yet. */
	type FormProps = {
		context: C | null;
		busy: boolean;
		error: string;
		fieldErrors: Record<string, string>;
		onsave: (body: U) => void;
		onclose: () => void;
	};

	let { create, back, form }: { create: RecordCreateState<T, U, C>; back: Page; form: Snippet<[FormProps]> } = $props();

	const text = $derived(create.config.text);

	onMount(() => void create.load());

	async function save(body: U): Promise<void> {
		const next = await create.save(body);
		if (next) void goto(next);
	}
</script>

{#if create.error}
	<Banner tone="danger" icon="alert-triangle" title={text.loadFailed}>
		{create.error}
		{#snippet action()}
			<Button label={text.retry} onclick={() => void create.load()} />
		{/snippet}
	</Banner>
{:else if create.loading}
	<Notice loading text={text.loading} />
{:else}
	{@render form({
		context: create.context,
		busy: create.busy,
		error: create.actionError,
		fieldErrors: create.fieldErrors,
		onsave: (value) => void save(value),
		onclose: () => void goto(back.path)
	})}
{/if}
