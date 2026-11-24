<script lang="ts">
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { traceScroll } from '$lib/motion/actions';
	import { enter } from '$lib/motion/transitions';
	import type { Guide } from '$lib/text/download-guide';
	import { downloadText as t } from '$lib/text/download';

	/** Satu panduan: pilihan topik, langkah-langkah topik terpilih, lalu bantuan untuk kesalahan yang sering terjadi. */
	let { guide }: { guide: Guide } = $props();

	// Kosong berarti topik pertama, supaya panduan lain yang dipasang di komponen ini tetap mulai dari awal.
	let topic = $state('');
	const tabs = $derived(guide.topics.map((item) => ({ key: item.key, icon: item.icon, label: item.title })));
	const current = $derived(guide.topics.find((item) => item.key === topic) ?? guide.topics[0]);
</script>

<section class="rounded-t-[2.25rem] bg-brand-deep px-4 py-12 text-white tablet:px-6 tablet:py-16 laptop:py-20">
	<div class="mx-auto flex max-w-6xl flex-col">
		<h2 class="text-3xl font-extrabold tracking-tight tablet:text-5xl">{guide.title}</h2>
		<p class="mt-4 max-w-2xl text-white/80">{guide.intro}</p>

		<div class="mt-8">
			<Tabs {tabs} bind:value={() => current?.key ?? '', (key) => (topic = key)} label={t.guideTopicLabel} variant="pill" />
		</div>

		{#if current}
			{#key current.key}
				<div class="mt-10" in:enter={{ y: 12 }}>
					<div class="flex flex-wrap items-baseline gap-3 border-b border-white/15 pb-3">
						<h3 class="text-xl font-bold">{current.title}</h3>
						<span class="text-sm font-semibold text-brand-accent">{current.who}</span>
					</div>
					<div class="guide-trace relative pt-6" use:traceScroll>
						<ol class="flex flex-col gap-5">
							{#each current.steps as step, index (step.title)}
								<li class="guide-step grid grid-cols-[2.75rem_minmax(0,1fr)] gap-4" data-trace-step>
									<span class="guide-dot relative z-10 flex size-11 items-center justify-center rounded-full border-2 border-white/15 bg-brand-deep text-lg text-brand-accent">
										<i class="ti ti-{step.icon}" aria-hidden="true"></i>
									</span>
									<div class="min-w-0 pb-2 pt-1">
										<h4 class="text-lg font-bold">
											<span class="mr-1 text-brand-accent">{index + 1}.</span>{step.title}
											{#if step.soon}<span class="ml-1 rounded-md bg-brand-accent px-2 py-0.5 align-middle text-[0.7rem] font-bold uppercase tracking-wide text-brand-deep">{t.soon}</span>{/if}
										</h4>
										<p class="mt-1 max-w-3xl text-white/80">{step.body}</p>
									</div>
								</li>
							{/each}
						</ol>
					</div>
				</div>
			{/key}
		{/if}

		<h3 class="mt-16 border-b border-white/15 pb-3 text-xl font-bold">{t.help}</h3>
		<div class="mt-6 grid grid-cols-1 gap-4 tablet:grid-cols-2">
			{#each guide.troubles as trouble (trouble.title)}
				<div class="rounded-2xl bg-white/10 p-5">
					<p class="flex items-center gap-2 font-bold"><i class="ti ti-{trouble.icon} text-brand-accent" aria-hidden="true"></i>{trouble.title}</p>
					<p class="mt-1.5 text-sm text-white/80">{trouble.body}</p>
				</div>
			{/each}
		</div>
	</div>
</section>
