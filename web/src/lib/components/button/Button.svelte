<script lang="ts">
	import { controlSize, dangerOutlineStyle, dangerSoftStyle, dangerStyle, infoSoftStyle, primaryStyle, secondaryStyle, selectedStyle, smallSize, successSoftStyle, tertiaryStyle, warningSoftStyle } from './button-style';
	import type { ButtonVariant } from './types';

	let {
		label,
		icon,
		variant = 'secondary',
		compact = false,
		small = false,
		iconOnly = false,
		active = false,
		disabled = false,
		loading = false,
		hint,
		type = 'button',
		href,
		onclick,
		class: className = ''
	}: {
		label: string;
		icon?: string;
		variant?: ButtonVariant;
		compact?: boolean;
		/** The 28 px size for a button inside a table row. */
		small?: boolean;
		/** Shows the icon alone; the label stays as the accessible name and the hover hint. */
		iconOnly?: boolean;
		active?: boolean;
		disabled?: boolean;
		/** A request is running: the icon turns into a spinner and the button does not answer presses; the width stays. */
		loading?: boolean;
		hint?: string;
		type?: 'button' | 'submit' | 'reset';
		href?: string;
		onclick?: () => void;
		class?: string;
	} = $props();

	const style = $derived(
		variant === 'primary'
			? primaryStyle
			: variant === 'tertiary'
				? tertiaryStyle
				: variant === 'dangerSoft'
					? dangerSoftStyle
					: variant === 'successSoft'
						? successSoftStyle
						: variant === 'infoSoft'
							? infoSoftStyle
							: variant === 'warningSoft'
								? warningSoftStyle
					: variant === 'danger'
						? dangerStyle
					: variant === 'dangerOutline'
						? dangerOutlineStyle
						: active
							? selectedStyle
							: secondaryStyle
	);
</script>

<svelte:element
	this={href ? 'a' : 'button'}
	role={href ? 'link' : 'button'}
	href={href && !disabled ? href : undefined}
	type={href ? undefined : type}
	{onclick}
	disabled={href ? undefined : disabled || loading}
	aria-disabled={href && (disabled || loading) ? true : undefined}
	aria-busy={loading ? true : undefined}
	title={disabled && hint ? hint : label}
	aria-label={label}
	aria-pressed={!href && variant === 'secondary' ? active : undefined}
	class="btn btn-sm shrink-0 font-semibold hover:brightness-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400 aria-disabled:pointer-events-none aria-disabled:border-slate-200 aria-disabled:bg-slate-100 aria-disabled:text-slate-400 {small ? smallSize : controlSize} {iconOnly ? 'aspect-square px-0!' : ''} {style} {className}"
>
	{#if loading}
		<i class="ti ti-loader-2 animate-spin text-sm motion-reduce:animate-none" aria-hidden="true"></i>
	{:else if icon}
		<i class="ti ti-{icon} text-sm" aria-hidden="true"></i>
	{:else if active && variant === 'secondary' && !iconOnly}
		<i class="ti ti-check text-sm" aria-hidden="true"></i>
	{/if}
	{#if !iconOnly}
		<span class={compact ? 'hidden tablet:inline' : ''}>{label}</span>
	{/if}
</svelte:element>
