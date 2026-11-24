<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import { formatDate } from '$lib/date/range';
	import { ingredientCountText } from '$lib/text/ingredient-counts';
	import { format } from '$lib/text/format';

	let { open, start, end, nextStart, onclose }: { open: boolean; start: string; end: string; nextStart: string; onclose: () => void } = $props();

	const steps = $derived([
		{ icon: 'calendar', text: format(ingredientCountText.closeGuidePeriodRange, { start: formatDate(start), end: formatDate(end), next: formatDate(nextStart) }) },
		{ icon: 'cash-register', text: format(ingredientCountText.closeGuideSessions, { end: formatDate(end) }) },
		{ icon: 'pencil', text: ingredientCountText.guideStepFill },
		{ icon: 'lock', text: ingredientCountText.guideStepClose }
	]);
</script>

<Modal {open} size="sm" title={ingredientCountText.guideTitle} description={ingredientCountText.guideDescription} {onclose}>
	<ul class="flex flex-col divide-y divide-slate-100">
		{#each steps as step (step.icon)}
			<li class="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
				<span class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-brand">
					<i class="ti ti-{step.icon} text-lg" aria-hidden="true"></i>
				</span>
				<span class="text-sm text-slate-800">{step.text}</span>
			</li>
		{/each}
	</ul>
	{#snippet footer()}
		<p class="text-xs text-slate-500 tablet:mr-auto">{ingredientCountText.guideShownOnce}</p>
		<Button label={ingredientCountText.understood} variant="primary" onclick={onclose} />
	{/snippet}
</Modal>
