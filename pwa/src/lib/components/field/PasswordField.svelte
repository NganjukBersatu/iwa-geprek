<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import type { ColorToken } from '$lib/theme/colors';
	import TextField from './TextField.svelte';

	let {
		value = $bindable(''),
		label,
		showDescription,
		hideDescription,
		placeholder = '',
		enabled = true,
		isError = false,
		labelColor = 'content',
		focusColor = 'primary',
		autocomplete,
		onenter,
		oninput
	}: {
		value?: string;
		label: string;
		showDescription: string;
		hideDescription: string;
		placeholder?: string;
		enabled?: boolean;
		isError?: boolean;
		labelColor?: ColorToken;
		focusColor?: 'primary' | 'accent';
		autocomplete?: HTMLInputAttributes['autocomplete'];
		onenter?: () => void;
		oninput?: () => void;
	} = $props();

	let visible = $state(false);
	const description = $derived(visible ? hideDescription : showDescription);
</script>

<TextField bind:value {label} {placeholder} {enabled} {isError} {labelColor} {focusColor} {autocomplete} {onenter} {oninput} enterkeyhint="done" type={visible ? 'text' : 'password'}>
	{#snippet trailing()}
		<button
			type="button"
			disabled={!enabled}
			aria-label={description}
			onclick={() => (visible = !visible)}
			class="flex size-[var(--space-touch)] shrink-0 items-center justify-center rounded-full"
		>
			<AppIcon icon={visible ? 'EyeOff' : 'Eye'} tint="content" />
		</button>
	{/snippet}
</TextField>
