<script lang="ts">
	import { onMount } from 'svelte';
	import Button from '$lib/components/button/Button.svelte';
	import { demoText } from '$lib/text/demo';
	import { DemoEntryState } from '../demo-entry.svelte';
	import DemoLoading from './DemoLoading.svelte';

	const demo = new DemoEntryState();

	onMount(() => {
		void demo.check();
		return () => demo.cancel();
	});
</script>

{#if demo.available}
	<div class="flex flex-col gap-3">
		<div class="flex items-center gap-3 text-xs text-brand-muted" aria-hidden="true">
			<span class="h-px flex-1 bg-brand-line"></span>
			{demoText.or}
			<span class="h-px flex-1 bg-brand-line"></span>
		</div>
		<Button label={demoText.tryDemo} icon="player-play" disabled={demo.running} onclick={() => void demo.start()} class="h-12! w-full justify-center rounded-full text-base!" />
		<p class="text-center text-xs text-brand-muted">{demoText.tryDemoHint}</p>
	</div>
{/if}

{#if demo.running}
	<DemoLoading {demo} />
{/if}
