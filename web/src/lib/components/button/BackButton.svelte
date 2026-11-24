<script lang="ts">
	import Button from './Button.svelte';

	/** The way back from a detail page to its list: an arrow only, with the destination as its accessible name. */
	let { label, href }: { label: string; href: string } = $props();
</script>

<Button {label} {href} icon="arrow-left" variant="tertiary" small compact iconOnly />
