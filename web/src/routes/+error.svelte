<script lang="ts">
	import { page } from '$app/state';
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import { PAGES } from '$lib/nav/pages';
	import { controlText } from '$lib/text/controls';
	import { errorPageText } from '$lib/text/error-page';
	import { format } from '$lib/text/format';

	const NOT_FOUND = 404;
	const FORBIDDEN = 403;
	const SERVER_ERROR = 500;

	const status = $derived(page.status);
	const copy = $derived(
		status === NOT_FOUND
			? { icon: 'map-off', title: errorPageText.notFoundTitle, body: errorPageText.notFoundBody }
			: status === FORBIDDEN
				? { icon: 'lock', title: errorPageText.forbiddenTitle, body: errorPageText.forbiddenBody }
				: status >= SERVER_ERROR
					? { icon: 'plug-connected-x', title: errorPageText.serverTitle, body: errorPageText.serverBody }
					: { icon: 'alert-circle', title: errorPageText.otherTitle, body: errorPageText.otherBody }
	);
</script>

<svelte:head><title>{format(controlText.pageTitleWithBrand, { title: copy.title })}</title></svelte:head>

<main class="mx-auto flex min-h-dvh max-w-lg flex-col justify-center gap-4 px-4 py-10">
	<Card>
		<div class="flex flex-col items-start gap-3">
			<i class="ti ti-{copy.icon} text-3xl text-slate-400" aria-hidden="true"></i>
			<h1 class="text-xl font-semibold text-brand-ink">{copy.title}</h1>
			<p class="text-sm leading-6 text-slate-600">{copy.body}</p>
			<p class="text-xs text-slate-500">{format(errorPageText.code, { status })}</p>
			<div class="flex flex-wrap gap-2">
				<Button label={errorPageText.back} icon="arrow-left" variant="primary" href={PAGES.dashboard.path} />
				{#if status >= SERVER_ERROR}
					<Button label={errorPageText.reload} icon="refresh" onclick={() => location.reload()} />
				{/if}
			</div>
		</div>
	</Card>
</main>
