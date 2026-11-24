<script lang="ts">
	import type { IconName } from '$lib/theme/icons';
	import type { ColorToken } from '$lib/theme/colors';
	import { textColor } from '$lib/theme/colors';
	import CenteredStat from './CenteredStat.svelte';
	import IconBadge from './IconBadge.svelte';

	/** Kartu angka: dengan [icon] ikon sejajar label, dengan [iconBeside] ikon di kiri dan label serta angka bertumpuk di kanannya, dengan [centered] semuanya bertumpuk rata tengah. */
	let {
		label,
		value,
		valueColor = 'content',
		icon,
		iconBeside = false,
		centered = false,
		fill = false
	}: { label: string; value: string; valueColor?: ColorToken; icon?: IconName; iconBeside?: boolean; centered?: boolean; fill?: boolean } = $props();
</script>

<div class="flex w-full flex-col overflow-hidden rounded-field {fill ? 'h-full' : ''} border border-divider bg-surface p-3"><div class="my-auto w-full">
	{#if centered}
		<CenteredStat {label} {value} {icon} {valueColor} />
	{:else if icon && iconBeside}
		<div class="flex items-center gap-3">
			<IconBadge {icon} />
			<div class="min-w-0">
				<p class="text-caption m-0 text-content-muted">{label}</p>
				<p class="text-title m-0 truncate {textColor[valueColor]}">{value}</p>
			</div>
		</div>
	{:else if icon}
		<div class="flex flex-col gap-2">
			<div class="flex items-center gap-2">
				<IconBadge {icon} />
				<p class="text-caption m-0 text-content-muted">{label}</p>
			</div>
			<p class="text-title m-0 {textColor[valueColor]}">{value}</p>
		</div>
	{:else}
		<p class="text-caption m-0 text-content-muted">{label}</p>
		<p class="text-title m-0 {textColor[valueColor]}">{value}</p>
	{/if}
</div>
</div>
