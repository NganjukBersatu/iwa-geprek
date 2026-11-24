<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { downloadText as t } from '$lib/text/download';
	import { WELCOME_FADE_MILLISECONDS, WELCOME_SCENES, WELCOME_SEEN_KEY, type WelcomeMood, type WelcomeScene } from '../welcome';

	/** The full-screen thanks shown before the download page, like the first start of Windows; it plays to the end once per device. */
	let { logo, playing = $bindable(false) }: { logo: string; playing?: boolean } = $props();

	function seen(): boolean {
		try {
			return localStorage.getItem(WELCOME_SEEN_KEY) === '1';
		} catch {
			return false;
		}
	}

	function remember(): void {
		try {
			localStorage.setItem(WELCOME_SEEN_KEY, '1');
		} catch {
			// Without storage the welcome simply plays again next time.
		}
	}

	let gone = $state(seen());
	let mood = $state<WelcomeMood>('dim');
	let current = $state<WelcomeScene | null>(null);
	let shown = $state(false);
	let run = 0;

	const wait = (milliseconds: number) => new Promise<void>((resolve) => setTimeout(resolve, milliseconds));
	const nextFrame = () => new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));

	async function play(): Promise<void> {
		const mine = ++run;
		gone = false;
		playing = true;
		for (const scene of WELCOME_SCENES) {
			mood = scene.mood;
			if (scene.silence > 0) await wait(scene.silence);
			if (mine !== run) return;
			current = scene;
			await nextFrame();
			shown = true;
			await wait(scene.hold);
			if (mine !== run) return;
			shown = false;
			await wait(WELCOME_FADE_MILLISECONDS);
		}
		if (mine !== run) return;
		gone = true;
		playing = false;
		remember();
	}

	onMount(() => {
		if (!gone) void play();
	});

	// The page behind stays still, without a scrollbar, while the welcome plays.
	$effect(() => {
		document.documentElement.classList.toggle('welcome-lock', !gone);
	});

	onDestroy(() => {
		run++;
		document.documentElement.classList.remove('welcome-lock');
	});
</script>

<div class="welcome" class:welcome-gone={gone} data-mood={mood} role="dialog" aria-modal="true" aria-label={t.welcomeLabel} aria-hidden={gone}>
	<span class="welcome-blob welcome-blob-1"></span>
	<span class="welcome-blob welcome-blob-2"></span>
	<span class="welcome-blob welcome-blob-3"></span>
	<div class="welcome-stage" aria-live="polite">
		{#if current?.logo}
			<img src={logo} alt={t.logoAlt} class="welcome-logo" class:welcome-show={shown} />
		{/if}
		<p class="welcome-line" class:welcome-big={current?.big} class:welcome-show={shown}>{current?.text ?? ''}</p>
		<span class="welcome-spinner" class:welcome-show={shown && current?.spinner} aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span>
		<p class="welcome-sub">{shown ? (current?.sub ?? '') : ''}</p>
	</div>
</div>
