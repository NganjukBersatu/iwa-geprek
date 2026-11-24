<script lang="ts">
	import type { IconName } from '$lib/theme/icons';
	import type { ColorToken } from '$lib/theme/colors';
	import { textColor } from '$lib/theme/colors';
	import IconBadge from './IconBadge.svelte';

	/** Ikon, label, angka, dan keterangan opsional yang bertumpuk dan rata tengah; dipakai di dalam kartu. */
	let { label, value, icon, caption, valueColor = 'content' }: { label: string; value: string; icon?: IconName; caption?: string | null; valueColor?: ColorToken } = $props();
</script>

<div class="flex w-full flex-col items-center gap-1">
	{#if icon}<IconBadge {icon} />{/if}
	<p class="text-caption m-0 text-center text-content-muted">{label}</p>
	<p class="text-title m-0 max-w-full truncate text-center {textColor[valueColor]}">{value}</p>
	{#if caption}<p class="text-caption m-0 max-w-full truncate text-center text-content-muted">{caption}</p>{/if}
</div>
