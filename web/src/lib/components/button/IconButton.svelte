<script lang="ts">
	type IconTone = 'neutral' | 'danger' | 'category';

	/** A button that is only an icon; the label is what screen readers and the hover hint say. */
	let {
		icon,
		label,
		onclick,
		disabled = false,
		size = 'md',
		tone = 'neutral'
	}: {
		icon: string;
		label: string;
		onclick: () => void;
		disabled?: boolean;
		/** sm sits inside a line of text or a table cell; md stands on its own. */
		size?: 'sm' | 'md';
		tone?: IconTone;
	} = $props();

	const TONES: Record<IconTone, string> = {
		neutral: 'text-slate-500 hover:bg-slate-100 hover:text-slate-700',
		danger: 'text-slate-500 hover:bg-danger-50 hover:text-danger-700',
		category: 'bg-category-50 text-category-500 hover:bg-category-200'
	};
</script>

<button
	type="button"
	{onclick}
	{disabled}
	aria-label={label}
	title={label}
	class="relative flex min-h-0 min-w-0 shrink-0 items-center justify-center after:absolute after:-inset-2 after:content-[''] pointer-fine:after:hidden disabled:opacity-30 disabled:hover:bg-transparent {size === 'sm' ? 'size-7 rounded-md' : 'size-9 rounded-md'} {TONES[tone]}"
>
	<i class="ti ti-{icon}" aria-hidden="true"></i>
</button>
