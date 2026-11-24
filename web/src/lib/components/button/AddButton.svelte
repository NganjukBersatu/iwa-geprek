<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import MenuButton from './MenuButton.svelte';

	let {
		label,
		onone,
		onmany,
		disabled = false,
		hint
	}: {
		label: string;
		onone: () => void;
		onmany: () => void;
		disabled?: boolean;
		hint?: string;
	} = $props();
</script>

<MenuButton
	{label}
	icon="plus"
	variant="primary"
	compact
	{disabled}
	{hint}
	items={[
		{ label: controlText.addOne, icon: 'plus', description: controlText.addOneHint, onclick: onone },
		{ label: controlText.addMany, icon: 'list-details', description: controlText.addManyHint, onclick: onmany }
	]}
/>
