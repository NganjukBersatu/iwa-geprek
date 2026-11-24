<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import type { OrderNote } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { untrack } from 'svelte';
	import { orderNoteText } from '$lib/text/order-notes';
	import { format } from '$lib/text/format';

	const MAX_NAME_LENGTH = 100;

	let { note, busy, error, onsave, onclose }: { note: OrderNote; busy: boolean; error: string; onsave: (name: string) => void; onclose: () => void } = $props();

	let name = $state(untrack(() => note.name));
	let problem = $state('');

	function submit(): void {
		const tidy = name.trim();
		if (!tidy) return void (problem = orderNoteText.nameRequired);
		problem = '';
		onsave(tidy);
	}
</script>

<Modal open title={format(controlText.editName, { name: note.name })} size="sm" {busy} {onclose}>
	<TextField label={orderNoteText.noteName} bind:value={name} maxlength={MAX_NAME_LENGTH} required hint={orderNoteText.oldOrdersNote} />
	{#if problem || error}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{problem || error}</Banner></div>
	{/if}
	{#snippet footer()}
		<CancelButton disabled={busy} onclick={onclose} />
		<SaveButton busy={busy} onclick={submit} />
	{/snippet}
</Modal>
