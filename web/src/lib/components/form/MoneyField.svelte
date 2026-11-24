<script lang="ts">
	import { rupiahDigits } from '$lib/format/currency';
	import FieldLabel from './FieldLabel.svelte';
	import FieldMessage from './FieldMessage.svelte';

	let {
		label,
		value = $bindable(''),
		placeholder = '',
		hint,
		error,
		maxlength = 13,
		disabled = false,
		readonly = false,
		required = false,
		compact = false,
		oncommit
	}: {
		label: string;
		value?: string;
		placeholder?: string;
		hint?: string;
		/** Replaces the hint and marks the box; the message says what is wrong and how to fix it. */
		error?: string;
		maxlength?: number;
		disabled?: boolean;
		/** Shown but not changed: it can still be focused and read by a screen reader. */
		readonly?: boolean;
		required?: boolean;
		/** A small box inside a table row; the label stays for screen readers only. */
		compact?: boolean;
		/** Called with the digits when the person leaves the box or presses Enter, for a figure saved straight from a list. */
		oncommit?: (digits: string) => void;
	} = $props();

	const id = $props.id();
	const messageId = `${id}-message`;
	const group = (digits: string) => digits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
	const shown = $derived(group(rupiahDigits(value).replace(/^0+(?=\d)/, '')));

	function type(event: Event & { currentTarget: HTMLInputElement }): void {
		const input = event.currentTarget;
		const before = rupiahDigits(input.value.slice(0, input.selectionStart ?? input.value.length)).length;
		const digits = rupiahDigits(input.value).replace(/^0+(?=\d)/, '').slice(0, maxlength);
		value = digits;
		input.value = group(digits);
		let caret = 0;
		for (let seen = 0; caret < input.value.length && seen < before; caret++) if (input.value[caret] !== '.') seen++;
		input.setSelectionRange(caret, caret);
	}
</script>

<div class="flex flex-col gap-1">
	<FieldLabel for={id} {label} {required} {compact} />
	<input
		{id}
		type="text"
		inputmode="numeric"
		autocomplete="off"
		{placeholder}
		{disabled}
		{readonly}
		aria-required={required ? true : undefined}
		aria-invalid={error ? true : undefined}
		aria-describedby={error || hint ? messageId : undefined}
		value={shown}
		oninput={type}
		onchange={oncommit ? () => oncommit(rupiahDigits(value)) : undefined}
		onkeydown={oncommit ? (event) => event.key === 'Enter' && event.currentTarget.blur() : undefined}
		class="w-full border bg-white text-slate-800 placeholder:text-slate-500 focus:outline-none focus:ring-2 disabled:bg-slate-50 disabled:text-slate-500 read-only:bg-slate-50 {error
			? 'border-danger-500 focus:border-danger-500 focus:ring-danger-200'
			: 'border-slate-200 focus:border-brand-focus focus:ring-brand-line'} {compact
			? 'rounded-md px-2 py-1 text-right text-xs'
			: 'h-10 rounded-md px-3 text-sm'}"
	/>
	<FieldMessage id={messageId} {error} {hint} />
</div>
