<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { bgColor, textColor, type ColorToken } from '$lib/theme/colors';
	import type { IconName } from '$lib/theme/icons';

	/** Pil kecil berisi ikon dan teks, untuk menandai jenis atau jumlah, misalnya "2 pribadi". */
	let { icon, text, container = 'selected', content = 'content' }: { icon: IconName; text: string; container?: ColorToken; content?: ColorToken } = $props();
</script>

<span class="text-label inline-flex items-center gap-1 whitespace-nowrap rounded-full px-3 py-1 {bgColor[container]} {textColor[content]}">
	<AppIcon {icon} tint={content} size={20} />
	{text}
</span>
