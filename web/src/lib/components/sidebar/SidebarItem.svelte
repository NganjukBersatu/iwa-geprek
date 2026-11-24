<script lang="ts">
	import type { NavLeaf } from './types';

	let {
		leaf,
		active,
		mobile = false,
		onnavigate
	}: {
		leaf: NavLeaf;
		active: boolean;
		mobile?: boolean;
		onnavigate?: () => void;
	} = $props();
</script>

<a
	href={leaf.href}
	onclick={onnavigate}
	aria-current={active ? 'page' : undefined}
	class="group relative flex items-center gap-2.5 rounded-lg pl-4 pr-3 text-nav outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand/40 motion-reduce:transition-none {mobile ? 'py-2.5' : 'py-1.5'} {active ? 'bg-brand font-semibold text-brand-on' : 'text-brand-ink hover:bg-brand-tint'}"
>
	<span class="size-1.5 shrink-0 rounded-full transition-colors motion-reduce:transition-none {active ? 'bg-brand-on' : 'bg-brand-ink/50 group-hover:bg-brand-ink'}"></span>
	<span class="min-w-0">{leaf.label}</span>
</a>
