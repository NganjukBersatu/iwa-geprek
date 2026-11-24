<script lang="ts">
	import { untrack } from 'svelte';
	import type { BranchPeriod, BranchPeriodChange } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { actionText } from '$lib/text/actions';
	import { branchPeriodText as text } from '$lib/text/branch-periods';
	import { format } from '$lib/text/format';
	import { periodLabel } from '../period-label';

	let {
		period,
		busy,
		error,
		onsave,
		onclose
	}: {
		period: BranchPeriod;
		busy: boolean;
		error: string;
		onsave: (change: BranchPeriodChange) => void;
		onclose: () => void;
	} = $props();

	const original = untrack(() => period);
	let start = $state(original.start);
	let end = $state(original.end);
	let problem = $state('');

	function submit(): void {
		if (!start || !end) return void (problem = text.datesRequired);
		if (end < start) return void (problem = text.endBeforeStart);
		problem = '';
		onsave({ start, end });
	}
</script>

<Modal open title={format(text.editTitle, { period: periodLabel(original) })} description={text.editDescription} size="sm" {busy} {onclose}>
	<div class="flex flex-col gap-4">
		<TextField label={text.startDate} type="date" bind:value={start} required />
		<TextField label={text.endDate} type="date" bind:value={end} required />
	</div>

	{#if problem || error}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{problem || error}</Banner></div>
	{/if}

	{#snippet footer()}
		<Button label={actionText.cancel} disabled={busy} onclick={onclose} />
		<Button label={busy ? actionText.saving : actionText.save} variant="primary" disabled={busy} onclick={submit} />
	{/snippet}
</Modal>
