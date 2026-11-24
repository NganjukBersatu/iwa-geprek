<script lang="ts">
	import Button from './Button.svelte';
	import { actionText } from '$lib/text/actions';

	/** The cancel button of every dialog and form: secondary button, so Batal always looks the same and red stays for danger. */
	let {
		label = actionText.cancel,
		disabled = false,
		small = false,
		compact = false,
		href,
		onclick
	}: {
		label?: string;
		disabled?: boolean;
		small?: boolean;
		compact?: boolean;
		href?: string;
		onclick?: () => void;
	} = $props();
</script>

<Button {label} variant="secondary" {disabled} {small} {compact} {href} {onclick} />
