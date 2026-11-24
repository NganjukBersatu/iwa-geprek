<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import { batchRunText } from '$lib/text/batch-runs';
	import { batchText } from '$lib/text/batches';

	let { open, onclose }: { open: boolean; onclose: () => void } = $props();
</script>

<Modal {open} title={batchRunText.guideTitle} size="md" {onclose}>
	<p class="mb-3 text-xs text-slate-500">{batchRunText.guideDescription}</p>
	<ol class="flex flex-col gap-3">
		{#each batchRunText.guideSteps as [icon, step] (step)}
			<li class="flex items-start gap-3 text-sm text-slate-700">
				<span class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-brand"><i class="ti ti-{icon} text-base" aria-hidden="true"></i></span>
				<span class="pt-1">{step}</span>
			</li>
		{/each}
	</ol>
	<p class="mt-4 text-xs text-slate-500">{batchRunText.guideFootnote}</p>
	{#snippet footer()}
		<Button label={batchText.close} variant="primary" onclick={onclose} />
	{/snippet}
</Modal>
