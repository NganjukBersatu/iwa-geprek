<script lang="ts">
	import { onMount } from 'svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import { WEB_RELEASE } from '../release';
	import { WhatsNewState } from '../whats-new.svelte';
	import { releaseText } from '$lib/text/release';
	import { format } from '$lib/text/format';

	const whatsNew = new WhatsNewState();

	onMount(() => void whatsNew.load());
</script>

<Modal open={whatsNew.open} size="sm" title={releaseText.title} description={format(releaseText.versionAndDate, { version: WEB_RELEASE.version, date: WEB_RELEASE.date })} onclose={() => whatsNew.close()}>
	<ul class="flex flex-col divide-y divide-slate-100">
		{#each WEB_RELEASE.notes as note (note.text)}
			<li class="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
				<span class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-brand">
					<i class="ti ti-{note.icon} text-xl" aria-hidden="true"></i>
				</span>
				<span class="text-sm text-slate-800">{note.text}</span>
			</li>
		{/each}
	</ul>
	{#snippet footer()}
		<p class="text-xs text-slate-500 tablet:mr-auto">{releaseText.shownOnce}</p>
		<Button label={releaseText.understood} variant="primary" onclick={() => whatsNew.close()} />
	{/snippet}
</Modal>
