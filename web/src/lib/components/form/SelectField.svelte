<script lang="ts">
	import Dropdown from './Dropdown.svelte';
	import FieldLabel from './FieldLabel.svelte';
	import FieldMessage from './FieldMessage.svelte';

	let {
		label,
		value = $bindable(''),
		options,
		empty,
		hint,
		error,
		required = false,
		disabled = false,
		compact = false,
		onchange,
		onsearch,
		onmore,
		searching = false,
		loadingMore = false
	}: {
		label: string;
		value?: string;
		options: { value: string; label: string }[];
		empty?: string;
		hint?: string;
		/** Replaces the hint and marks the box; the message says what is wrong and how to fix it. */
		error?: string;
		required?: boolean;
		disabled?: boolean;
		compact?: boolean;
		onchange?: (value: string) => void;
		onsearch?: (text: string) => void;
		onmore?: () => void;
		searching?: boolean;
		loadingMore?: boolean;
	} = $props();

	const id = $props.id();
	const messageId = `${id}-message`;
</script>

<div class="flex flex-col gap-1">
	<FieldLabel for={id} {label} {required} {compact} />
	<Dropdown {id} {disabled} bind:value {options} {empty} {onchange} {onsearch} {onmore} {searching} {loadingMore} invalid={!!error} describedby={error || hint ? messageId : undefined} size={compact ? 'sm' : 'md'} />
	<FieldMessage id={messageId} {error} {hint} />
</div>
