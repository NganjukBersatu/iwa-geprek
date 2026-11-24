<script lang="ts">
	import { goto } from '$app/navigation';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import { PAGES } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
</script>

<Banner tone="info" icon="info-circle" title={emptyText.menuCategories.title}>
	{emptyText.menuCategories.text}
	{#snippet action()}
		<Button label={emptyText.menuCategories.open} icon="category" onclick={() => void goto(PAGES.menuCategories.path)} />
	{/snippet}
</Banner>
