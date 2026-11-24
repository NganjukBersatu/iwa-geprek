<script lang="ts">
	import { access } from '$lib/auth/access.svelte';
	import type { Page } from '$lib/nav/pages';
	import Button from './Button.svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	/** A link to another screen, named after it and left out for an account that may not open it. */
	let { page, icon }: { page: Page; icon?: string } = $props();
</script>

{#if access.opens(page.screen)}
	<Button href={page.path} label={format(controlText.openPage, { name: page.label })} {icon} variant="primary" compact />
{/if}
