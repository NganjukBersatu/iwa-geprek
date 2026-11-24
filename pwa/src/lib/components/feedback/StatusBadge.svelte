<script lang="ts">
	import type { BadgeTone } from './types';

	let { text, tone }: { text: string; tone: BadgeTone } = $props();

	const looks: Record<BadgeTone, string> = {
		positive: 'bg-selected text-primary',
		warning: 'bg-warning-container text-warning',
		danger: 'bg-danger-container text-on-danger-container',
		neutral: 'bg-divider text-content-muted',
		accent: 'bg-accent text-content',
		strong: 'bg-primary text-on-primary'
	};
</script>

<span class="text-label inline-block rounded-full px-3 py-1 {looks[tone]}">{text}</span>
