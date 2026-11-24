<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import { icons, type IconName } from '$lib/theme/icons';
	import { textColor, type ColorToken } from '$lib/theme/colors';

	let {
		icon,
		tint = 'content',
		size = 24,
		label,
		class: className = ''
	}: {
		icon: IconName;
		tint?: ColorToken;
		/** Sisi ikon dalam px; bawaannya 24 (AppSizes.icon). */
		size?: number;
		label?: string;
		class?: string;
	} = $props();
</script>

<i
	class="ti {icons[icon]} inline-flex shrink-0 items-center justify-center leading-none {textColor[tint]} {className}"
	use:dynamicStyle={{ width: `${size}px`, height: `${size}px`, 'font-size': `${size}px` }}
	role={label ? 'img' : undefined}
	aria-label={label}
	aria-hidden={label ? undefined : 'true'}
></i>
