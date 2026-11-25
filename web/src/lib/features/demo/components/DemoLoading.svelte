<script lang="ts">
	import { onMount } from 'svelte';
	import logo from '$lib/assets/logo/brand-logo.png';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import { dynamicStyle } from '$lib/motion/actions';
	import { enter } from '$lib/motion/transitions';
	import { actionText } from '$lib/text/actions';
	import { authText } from '$lib/text/auth';
	import { demoText } from '$lib/text/demo';
	import { format } from '$lib/text/format';
	import { DEMO_STEPS, type DemoEntryState } from '../demo-entry.svelte';

	let { demo }: { demo: DemoEntryState } = $props();

	let heading = $state<HTMLHeadingElement>();
	// Tombol yang ditekan kini tertutup layar ini, jadi fokus dipindah ke judulnya supaya pembaca layar dan papan ketik ikut berpindah.
	onMount(() => heading?.focus());
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-brand-page p-4" role="dialog" aria-modal="true" aria-labelledby="demo-loading-title">
	<section in:enter class="flex w-full max-w-md flex-col gap-6 rounded-lg border border-brand-line bg-white p-6 shadow-xl tablet:p-8">
		<img src={logo} alt={authText.login.logoAlt} width="88" height="116" class="h-auto w-18" />
		<div class="flex flex-col gap-1">
			<h1 bind:this={heading} id="demo-loading-title" tabindex="-1" class="text-lg font-semibold text-brand-ink outline-none">{demo.error ? demoText.failedTitle : demoText.loadingTitle}</h1>
			<p class="text-sm text-slate-600">{demoText.loadingNote}</p>
		</div>

		<ol class="flex flex-col gap-4" aria-live="polite">
			{#each DEMO_STEPS as step (step)}
				{@const state = demo.stateOf(step)}
				<li class="flex items-start gap-3">
					{#if state === 'done'}
						<i class="ti ti-circle-check success-mark mt-0.5 text-xl text-success-700" aria-hidden="true"></i>
					{:else if state === 'current' && !demo.error}
						<i class="ti ti-loader-2 mt-0.5 animate-spin text-xl text-brand motion-reduce:animate-none" aria-hidden="true"></i>
					{:else}
						<i class="ti ti-circle mt-0.5 text-xl text-slate-400" aria-hidden="true"></i>
					{/if}
					<div class="flex min-w-0 flex-1 flex-col gap-2">
						<span class="text-sm {state === 'pending' ? 'text-slate-500' : 'font-medium text-slate-800'}">{demoText.steps[step]}</span>
						{#if step === 'loading' && state !== 'pending'}
							<div class="flex items-center gap-3">
								<div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-label={demoText.progressLabel} aria-valuemin={0} aria-valuemax={100} aria-valuenow={demo.percent}>
									<div class="progress-fill h-2 rounded-full bg-brand" use:dynamicStyle={{ width: `${demo.percent}%` }}></div>
								</div>
								<span class="w-10 text-right text-xs tabular-nums text-slate-600">{format(demoText.percent, { percent: demo.percent })}</span>
							</div>
						{/if}
					</div>
				</li>
			{/each}
		</ol>

		{#if demo.error}
			<div class="flex flex-col gap-4" role="alert">
				<Banner tone="danger" icon="alert-triangle">{demo.error}</Banner>
				<div class="flex flex-wrap gap-2">
					<Button label={actionText.retry} variant="primary" onclick={() => void demo.start()} />
					<Button label={demoText.backToSignIn} onclick={() => demo.cancel()} />
				</div>
			</div>
		{/if}
	</section>
</div>
