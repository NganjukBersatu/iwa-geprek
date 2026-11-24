<script lang="ts">
	import { untrack, type Snippet } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import LoadingState from './LoadingState.svelte';

	const MIN_SHOWN_MILLIS = 350;
	const ENTER_MILLIS = 280;
	const EXIT_MILLIS = 140;
	const SLIDE_DIVISOR = 28;

	/** Satu-satunya pintu keadaan memuat: kerangka berkilau sampai [children] siap (minimal sebentar agar tidak berkedip), lalu perpindahan halus. */
	let { loading, rows = 4, children }: { loading: boolean; rows?: number; children: Snippet } = $props();

	let showingSkeleton = $state(untrack(() => loading));
	let shownSince = Date.now();
	let timer: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		clearTimeout(timer);
		if (loading) {
			if (!showingSkeleton) shownSince = Date.now();
			showingSkeleton = true;
			return;
		}
		if (!showingSkeleton) return;
		const remaining = MIN_SHOWN_MILLIS - (Date.now() - shownSince);
		if (remaining > 0) timer = setTimeout(() => (showingSkeleton = false), remaining);
		else showingSkeleton = false;
		return () => clearTimeout(timer);
	});
</script>

{#if showingSkeleton}
	<div in:fly={{ y: 8, duration: ENTER_MILLIS }} out:fade={{ duration: EXIT_MILLIS }}>
		<LoadingState {rows} />
	</div>
{:else}
	<div in:fly={{ y: 8, duration: ENTER_MILLIS }} out:fade={{ duration: EXIT_MILLIS }}>
		{@render children()}
	</div>
{/if}
