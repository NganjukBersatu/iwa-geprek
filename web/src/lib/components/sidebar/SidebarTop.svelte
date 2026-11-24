<script lang="ts">
	import type { NavTop } from './types';

	let {
		entry,
		active,
		compact = false,
		mobile = false,
		onnavigate
	}: {
		entry: NavTop;
		active: boolean;
		compact?: boolean;
		mobile?: boolean;
		onnavigate?: () => void;
	} = $props();
</script>

<a
	href={entry.href}
	title={entry.label}
	onclick={onnavigate}
	aria-current={active ? 'page' : undefined}
	class="flex items-center gap-3 rounded-lg px-3 text-nav outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand/40 motion-reduce:transition-none {compact ? 'justify-center' : ''} {mobile ? 'py-2.5' : 'py-2'} {active ? 'bg-brand font-semibold text-brand-on' : 'text-brand-ink hover:bg-brand-tint'}"
>
	<i class="ti {entry.icon} text-xl" aria-hidden="true"></i>
	{#if !compact}
		<span class="whitespace-nowrap">{entry.label}</span>
	{/if}
</a>
