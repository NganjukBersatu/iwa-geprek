<script lang="ts">
	import TextButton from '$lib/components/button/TextButton.svelte';
	import { live, liveConnected, liveGaveUp } from '$lib/live/live';
	import { unfold } from '$lib/motion/transitions';
	import { liveText } from '$lib/text/live';

	// A blip shorter than this is not worth a strip.
	const GRACE_MILLISECONDS = 2000;

	let shown = $state(false);

	$effect(() => {
		if ($liveConnected) {
			shown = false;
			return;
		}
		const timer = setTimeout(() => (shown = true), GRACE_MILLISECONDS);
		return () => clearTimeout(timer);
	});
</script>

{#if shown}
	<div transition:unfold class="shrink-0 border-b border-warning-200 bg-warning-50" role="status">
		<p class="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-warning-700 tablet:px-6">
			<i class="ti ti-wifi-off text-base" aria-hidden="true"></i>
			{$liveGaveUp ? liveText.gaveUp : liveText.reconnecting}
			{#if $liveGaveUp}
				<TextButton label={liveText.retry} onclick={() => live.reconnect()} />
			{/if}
		</p>
	</div>
{/if}
