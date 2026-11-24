<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { untrack } from 'svelte';
	import type { MenuCategoryRecord } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { formatNumber } from '$lib/format/currency';
	import { actionText } from '$lib/text/actions';
	import { menuCategoryText } from '$lib/text/menu-categories';
	import { format } from '$lib/text/format';

	let {
		category,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onremove,
		onclose
	}: {
		/** The category being renamed; empty when a new one is added. */
		category: MenuCategoryRecord | null;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (name: string) => void;
		onremove: (category: MenuCategoryRecord) => void;
		onclose: () => void;
	} = $props();

	let name = $state(untrack(() => category?.name ?? ''));
	const errors = new FieldErrors({ name: menuCategoryText.categoryName }, () => fieldErrors);

	// A refusal from the server puts the cursor in the refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	function submit(): void {
		const found: Record<string, string> = {};
		if (!name.trim()) found.name = menuCategoryText.nameRequired;
		if (!errors.check(found)) return;
		onsave(name.trim());
	}
</script>

<Modal
	open
	title={category ? format(controlText.editName, { name: category.name }) : menuCategoryText.addCategory}
	description={menuCategoryText.dialogDescription}
	size="sm"
	{busy}
	{onclose}
>
	<form
		onsubmit={(event) => {
			event.preventDefault();
			submit();
		}}
	>
		<TextField label={menuCategoryText.categoryName} bind:value={name} maxlength={100} placeholder={menuCategoryText.nameExample} required error={errors.get('name')} />
		{#if category && category.menu_count > 0}
			<p class="mt-2 text-xs text-slate-500">{format(menuCategoryText.categoryInUse, { count: formatNumber(category.menu_count, 0) })}</p>
		{/if}
		{#if error && errors.count === 0}
			<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
		{/if}
	</form>

	{#snippet footer()}
		{#if category && category.menu_count === 0}
			<Button label={actionText.remove} icon="trash" variant="dangerSoft" disabled={busy} onclick={() => onremove(category)} />
		{/if}
		<CancelButton disabled={busy} onclick={onclose} />
		<SaveButton {busy} onclick={submit} />
	{/snippet}
</Modal>
