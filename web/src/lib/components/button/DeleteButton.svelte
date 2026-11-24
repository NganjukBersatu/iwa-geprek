<script lang="ts">
	import Button from './Button.svelte';
	import { actionText } from '$lib/text/actions';

	/** The delete button: filled red on a page or in a dialog, and a small tinted one when it removes a line inside a form. */
	let {
		label = actionText.remove,
		small = false,
		disabled = false,
		hint,
		onclick
	}: {
		label?: string;
		/** Removes one line inside a form instead of a whole record. */
		small?: boolean;
		disabled?: boolean;
		hint?: string;
		onclick: () => void;
	} = $props();
</script>

<Button {label} icon="trash" variant={small ? 'dangerSoft' : 'danger'} {small} compact={small} {disabled} {hint} {onclick} />
