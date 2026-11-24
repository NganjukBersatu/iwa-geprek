<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';
	import type { HTMLInputAttributes } from 'svelte/elements';
	import type { ColorToken } from '$lib/theme/colors';
	import { textColor } from '$lib/theme/colors';

	/** Kolom isian satu baris: label di atas, kotak putih berbingkai 1,5 px yang menebal 2 px saat fokus atau galat. */
	let {
		value = $bindable(''),
		label,
		placeholder = '',
		enabled = true,
		isError = false,
		type = 'text',
		inputmode,
		autocomplete,
		enterkeyhint,
		labelColor = 'content',
		focusColor = 'primary',
		onenter,
		oninput,
		trailing
	}: {
		value?: string;
		label: string;
		placeholder?: string;
		enabled?: boolean;
		isError?: boolean;
		type?: 'text' | 'password' | 'email' | 'tel' | 'number';
		inputmode?: 'text' | 'numeric' | 'decimal' | 'tel' | 'email';
		autocomplete?: HTMLInputAttributes['autocomplete'];
		enterkeyhint?: 'next' | 'done' | 'go' | 'search';
		labelColor?: ColorToken;
		focusColor?: 'primary' | 'accent';
		onenter?: () => void;
		oninput?: () => void;
		trailing?: Snippet;
	} = $props();

	const id = $props.id();
	let focused = $state(false);

	const border = $derived(isError ? 'border-danger' : focused ? (focusColor === 'accent' ? 'border-accent' : 'border-primary') : 'border-outline');
</script>

<div class="flex w-full flex-col gap-1">
	<label for={id} class="text-label {textColor[labelColor]}">{label}</label>
	<div class="flex min-h-[var(--space-touch)] w-full items-center gap-1 rounded-field bg-surface pl-3 {border}" use:dynamicStyle={{ 'border-width': `${focused || isError ? 2 : 1.5}px`, 'border-style': 'solid' }}>
		<input
			{id}
			{type}
			{inputmode}
			{autocomplete}
			{enterkeyhint}
			{placeholder}
			disabled={!enabled}
			bind:value
			oninput={() => oninput?.()}
			onfocus={() => (focused = true)}
			onblur={() => (focused = false)}
			onkeydown={(event) => event.key === 'Enter' && onenter?.()}
			class="text-body min-w-0 flex-1 bg-transparent py-2 text-content caret-primary outline-none placeholder:text-content-muted"
		/>
		{@render trailing?.()}
	</div>
</div>
