<script lang="ts">
	import type { Snippet } from 'svelte';
	import { motionReduced } from '$lib/motion/reduced';

	/** One way to install the app: what it is on the left, a phone acting out the steps on the right; a step can be tapped to show its screen. */
	let {
		tone,
		steps,
		screens,
		note,
		children
	}: {
		/** `brand` is the green card, `light` the white one. */
		tone: 'brand' | 'light';
		steps: string[];
		/** One phone screen per step, in the same order. */
		screens: Snippet[];
		/** The small line under the steps, left out when the card has nothing to add. */
		note?: { icon: string; text: string };
		children: Snippet;
	} = $props();

	const STEP_MILLISECONDS = 3200;

	let active = $state(0);
	let onScreen = $state(false);
	let tabShown = $state(document.visibilityState === 'visible');
	let round = $state(0);
	let card = $state<HTMLElement | null>(null);

	/** Shows a step's screen and restarts the round from there. */
	function show(index: number): void {
		active = index;
		round++;
	}

	$effect(() => {
		if (!card) return;
		const watcher = new IntersectionObserver(([entry]) => (onScreen = entry?.isIntersecting ?? false));
		watcher.observe(card);
		return () => watcher.disconnect();
	});

	// The demo only plays while someone can see it, so an idle open tab costs no timer or battery.
	$effect(() => {
		void round;
		if (!onScreen || !tabShown || motionReduced()) return;
		const timer = setInterval(() => (active = (active + 1) % screens.length), STEP_MILLISECONDS);
		return () => clearInterval(timer);
	});

	const brand = $derived(tone === 'brand');

	function follow(event: PointerEvent): void {
		if (!card) return;
		const box = card.getBoundingClientRect();
		card.style.setProperty('--glow-x', `${event.clientX - box.left}px`);
		card.style.setProperty('--glow-y', `${event.clientY - box.top}px`);
	}
</script>

<svelte:document onvisibilitychange={() => (tabShown = document.visibilityState === 'visible')} />

<article
	bind:this={card}
	onpointermove={follow}
	class="platform-card group relative grid items-center gap-8 overflow-hidden rounded-3xl p-5 hp-besar:p-6 laptop:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)] laptop:p-10 {brand ? 'platform-card-brand bg-brand text-white' : 'border border-brand-line bg-white text-slate-800'}"
>
	<div class="relative flex min-w-0 flex-col">
		{@render children()}
		<ol class="mt-6 flex flex-col gap-1">
			{#each steps as step, index (step)}
				{@const on = index === active}
				<li>
					<button
						type="button"
						onclick={() => show(index)}
						aria-current={on ? 'step' : undefined}
						class="grid w-full grid-cols-[2rem_minmax(0,1fr)] items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition-colors motion-reduce:transition-none {on ? (brand ? 'bg-white/15' : 'bg-brand-soft') : brand ? 'hover:bg-white/10' : 'hover:bg-brand-page'}"
					>
						<span class="flex size-8 items-center justify-center rounded-full text-sm font-bold transition-colors motion-reduce:transition-none {on ? (brand ? 'bg-brand-accent text-brand-deep' : 'bg-brand text-white') : brand ? 'bg-white/15' : 'bg-brand-tint text-brand-deep'}">{index + 1}</span>
						<span class="min-w-0 font-semibold">{step}</span>
					</button>
				</li>
			{/each}
		</ol>
		{#if note}
			<p class="mt-4 flex items-center gap-2 text-sm {brand ? 'text-white/80' : 'text-slate-500'}"><i class="ti ti-{note.icon}" aria-hidden="true"></i>{note.text}</p>
		{/if}
	</div>

	<div class="phone-demo relative mx-auto aspect-[9/18.5] w-full max-w-56 rounded-[2.6rem] bg-brand-deep p-2.5 shadow-2xl laptop:max-w-64 {brand ? 'phone-demo-left' : 'phone-demo-right'}" aria-hidden="true">
		<div class="relative h-full overflow-hidden rounded-[2rem] bg-brand-page text-slate-800">
			{#each screens as screen, index (index)}
				<div class="phone-screen" class:phone-screen-on={index === active} class:phone-screen-out={index === (active - 1 + screens.length) % screens.length && index !== active}>
					{@render screen()}
				</div>
			{/each}
		</div>
	</div>
</article>
