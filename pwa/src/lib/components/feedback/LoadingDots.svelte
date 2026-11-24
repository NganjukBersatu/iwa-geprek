<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import { bgColor, type ColorToken } from '$lib/theme/colors';
	import { t } from '$lib/text/t';

	/** Tiga titik yang berdenyut bergantian, penanda proses yang sedang berjalan di dalam tombol. */
	let { color }: { color: ColorToken } = $props();
</script>

<span class="flex items-center gap-1" role="status" aria-label={t('common_loading')}>
	{#each [0, 1, 2] as index (index)}
		<span
			class="loading-dot size-2 rounded-full {bgColor[color]}"
			use:dynamicStyle={{ 'animation-delay': `${(index * 1400) / 6}ms` }}
		></span>
	{/each}
</span>
