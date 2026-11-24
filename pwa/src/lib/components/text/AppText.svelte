<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';
	import { textColor, type ColorToken } from '$lib/theme/colors';

	/** Peran teks (AppTypography): halaman memilih peran, bukan gaya sendiri. */
	type Role = 'display' | 'headline' | 'title' | 'body' | 'label' | 'button' | 'caption';

	let {
		role = 'body',
		color = 'content',
		align,
		maxLines,
		class: className = '',
		children
	}: {
		role?: Role;
		color?: ColorToken;
		align?: 'center' | 'end';
		maxLines?: number;
		class?: string;
		children: Snippet;
	} = $props();

	const roleClass: Record<Role, string> = {
		display: 'text-display',
		headline: 'text-headline',
		title: 'text-title',
		body: 'text-body',
		label: 'text-label',
		button: 'text-button',
		caption: 'text-caption'
	};
</script>

<p
	class="m-0 {roleClass[role]} {textColor[color]} {align === 'center' ? 'text-center' : align === 'end' ? 'text-end' : ''} {className}"
	use:dynamicStyle={maxLines ? { display: '-webkit-box', '-webkit-box-orient': 'vertical', '-webkit-line-clamp': maxLines, overflow: 'hidden' } : {}}
>
	{@render children()}
</p>
