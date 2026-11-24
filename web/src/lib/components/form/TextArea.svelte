<script lang="ts">
	import { formText } from '$lib/text/form';
	import FieldLabel from './FieldLabel.svelte';
	import FieldMessage from './FieldMessage.svelte';

	let {
		label,
		value = $bindable(''),
		placeholder = '',
		hint,
		error,
		rows = 4,
		maxlength,
		disabled = false,
		readonly = false,
		required = false,
		compact = false
	}: {
		label: string;
		value?: string;
		/** An example of the format only; it never stands in for the label. */
		placeholder?: string;
		hint?: string;
		/** Replaces the hint and marks the box; the message says what is wrong and how to fix it. */
		error?: string;
		rows?: number;
		/** With a limit the box counts the characters and stops taking more at the limit. */
		maxlength?: number;
		disabled?: boolean;
		/** Shown but not changed: it can still be focused and read by a screen reader. */
		readonly?: boolean;
		required?: boolean;
		compact?: boolean;
	} = $props();

	const id = $props.id();
	const messageId = `${id}-message`;
	const atLimit = $derived(maxlength !== undefined && value.length >= maxlength);
</script>

<div class="flex flex-col gap-1">
	<FieldLabel for={id} {label} {required} {compact} />
	<textarea
		{id}
		{rows}
		{maxlength}
		{placeholder}
		{disabled}
		{readonly}
		{required}
		aria-invalid={error ? true : undefined}
		aria-describedby={error || hint ? messageId : undefined}
		bind:value
		class="rounded-md border bg-white px-3 py-2 text-sm leading-6 text-slate-800 placeholder:text-slate-500 focus:outline-none focus:ring-2 disabled:bg-slate-50 disabled:text-slate-500 read-only:bg-slate-50 {error
			? 'border-danger-500 focus:border-danger-500 focus:ring-danger-200'
			: 'border-slate-200 focus:border-brand-focus focus:ring-brand-line'}"
	></textarea>
	<div class="flex items-start justify-between gap-3">
		<div class="min-w-0 flex-1"><FieldMessage id={messageId} {error} {hint} /></div>
		{#if maxlength !== undefined}
			<span class="shrink-0 text-xs {atLimit ? 'font-semibold text-danger-700' : 'text-slate-500'}" aria-live="polite">
				{value.length} / {maxlength}{atLimit ? ` · ${formText.characterLimit}` : ''}
			</span>
		{/if}
	</div>
</div>
