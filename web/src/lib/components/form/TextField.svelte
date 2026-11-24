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
		type = 'text',
		max,
		inputmode,
		maxlength,
		disabled = false,
		readonly = false,
		required = false,
		autocomplete,
		suggestions,
		compact = false,
		large = false,
		onblur,
		oninput
	}: {
		label: string;
		value?: string;
		placeholder?: string;
		hint?: string;
		/** Replaces the hint and marks the box; the message says what is wrong and how to fix it. */
		error?: string;
		type?: 'text' | 'password' | 'email' | 'tel' | 'number' | 'date' | 'time' | 'datetime-local';
		max?: string;
		inputmode?: 'text' | 'numeric' | 'decimal' | 'tel' | 'email';
		maxlength?: number;
		disabled?: boolean;
		/** Shown but not changed: it can still be focused and read by a screen reader. */
		readonly?: boolean;
		required?: boolean;
		autocomplete?: 'off' | 'new-password' | 'current-password' | 'username';
		suggestions?: string[];
		/** A small box inside a list row; the label stays for screen readers only, and figures line up on the right. */
		compact?: boolean;
		/** A main form's box at 48 px with larger text, level with the form's primary button. */
		large?: boolean;
		/** Called when the box is left, so a form can check this field on its own. */
		onblur?: () => void;
		/** Dipanggil setiap kali isi kotak berubah oleh ketikan. */
		oninput?: () => void;
	} = $props();

	const id = $props.id();
	const messageId = `${id}-message`;
	let revealed = $state(false);
	let input: HTMLInputElement | undefined = $state();

	export function focus(): void {
		input?.focus();
	}
</script>

<div class="flex flex-col gap-1">
	<FieldLabel for={id} {label} {required} {compact} {large} />
	<div class="relative">
		<input
		{id}
		bind:this={input}
		{onblur}
		{oninput}
		aria-invalid={error ? true : undefined}
		aria-describedby={error || hint ? messageId : undefined}
		type={type === 'password' && revealed ? 'text' : type}
		{max}
		{inputmode}
		{maxlength}
		{placeholder}
		{disabled}
		{readonly}
		aria-required={required ? true : undefined}
		{autocomplete}
		list={suggestions ? `${id}-list` : undefined}
		bind:value
		class="w-full border bg-white {large ? 'text-base font-normal text-brand-ink placeholder:text-brand-muted' : 'text-sm text-slate-800 placeholder:text-slate-500'} {error
			? 'border-danger-500 focus:border-danger-500 focus:ring-danger-200'
			: `${large ? 'border-brand-line' : 'border-slate-200'} focus:border-brand-focus focus:ring-brand-line`} focus:outline-none focus:ring-2 disabled:bg-slate-50 disabled:text-slate-500 read-only:bg-slate-50 {compact
			? `rounded-md px-2 py-1 ${inputmode === 'decimal' || inputmode === 'numeric' ? 'text-right' : ''}`
			: `${large ? 'h-12 rounded-md pl-3.5' : 'h-10 rounded-md pl-3'} ${type === 'password' ? (large ? 'pr-12' : 'pr-10') : 'pr-3'}`}"
		/>
		{#if type === 'password'}
			<button type="button" onclick={() => (revealed = !revealed)} aria-label={revealed ? formText.hidePassword : formText.showPassword} class="absolute inset-y-0 right-0 flex items-center justify-center text-slate-500 hover:text-slate-600 {large ? 'w-12 text-xl' : 'w-10'}">
				<i class="ti {revealed ? 'ti-eye-off' : 'ti-eye'}" aria-hidden="true"></i>
			</button>
		{/if}
	</div>
	{#if suggestions}
		<datalist id="{id}-list">
			{#each suggestions as suggestion (suggestion)}<option value={suggestion}></option>{/each}
		</datalist>
	{/if}
	<FieldMessage id={messageId} {error} {hint} {large} />
</div>
