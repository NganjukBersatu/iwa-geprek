<script lang="ts">
	import Button from './Button.svelte';
	import { actionText } from '$lib/text/actions';

	/** The main save button of every form: filled brand, and while the request runs it shows a spinner and "Menyimpan..." at the same width. */
	let {
		label = actionText.save,
		icon,
		busy = false,
		disabled = false,
		hint,
		type = 'button',
		onclick
	}: {
		label?: string;
		icon?: string;
		/** A save is running. */
		busy?: boolean;
		/** Something else keeps the button from answering, such as a form that is still empty. */
		disabled?: boolean;
		hint?: string;
		type?: 'button' | 'submit';
		onclick?: () => void;
	} = $props();
</script>

<Button label={busy ? actionText.saving : label} {icon} loading={busy} {disabled} {hint} {type} variant="primary" {onclick} />
