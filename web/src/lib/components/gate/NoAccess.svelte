<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import type { Page } from '$lib/nav/pages';
	import { authText } from '$lib/text/auth';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	/** Hanya tampil untuk akun yang membuka alamat yang tidak boleh dibukanya; menu tidak pernah memuat halaman seperti itu. */
	let { back }: { back: Page | undefined } = $props();
</script>

<svelte:head><title>{format(controlText.pageTitleWithBrand, { title: authText.noAccessTitle })}</title></svelte:head>

<div class="mx-auto flex max-w-lg flex-col gap-4 py-10">
	<Card>
		<div class="flex flex-col items-start gap-3">
			<i class="ti ti-lock text-3xl text-slate-400" aria-hidden="true"></i>
			<h1 class="text-xl font-semibold text-brand-ink">{authText.noAccessTitle}</h1>
			<p class="text-sm leading-6 text-slate-600">{authText.noAccessBody}</p>
			{#if back}
				<Button label={format(authText.noAccessBack, { page: back.label })} icon="arrow-left" href={back.path} />
			{/if}
		</div>
	</Card>
</div>
