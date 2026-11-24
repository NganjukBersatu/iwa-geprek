<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import { tones, type Tone } from '../card/tone';

	let { value, tone = 'brand', class: className = '' }: { value: number; tone?: Tone; class?: string } = $props();

	const width = $derived(Math.min(100, Math.max(0, value)));
</script>

<div class="h-2 w-full rounded-full bg-slate-100 {className}" role="presentation">
	<div class="h-2 rounded-full bg-current {tones[tone].line}" use:dynamicStyle={{ width: `${width}%` }}></div>
</div>
