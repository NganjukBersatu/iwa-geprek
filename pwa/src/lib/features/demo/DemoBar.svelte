<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { demoMode } from '$lib/platform/demo-mode.svelte';
	import { t } from '$lib/text/t';
</script>

{#if demoMode.active}
	<p class="flex shrink-0 items-center gap-2 bg-warning-container px-4 py-2 text-xs font-semibold text-warning" role="status">
		<AppIcon icon="Info" tint="warning" size={16} />
		{t('demo_mode_banner')}
	</p>
{/if}
