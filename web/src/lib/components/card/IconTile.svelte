<script lang="ts">
	import { tones, type Tone } from './tone';

	let {
		icon,
		tone = 'brand',
		size = 'md'
	}: {
		icon: string;
		tone?: Tone;
		size?: 'sm' | 'md';
	} = $props();
</script>

<span class="flex shrink-0 items-center justify-center rounded-lg {size === 'sm' ? 'size-9' : 'size-10'} {tones[tone].tile}">
	<i class="ti ti-{icon} text-xl" aria-hidden="true"></i>
</span>
