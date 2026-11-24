<script lang="ts">
	import { preparePhoto } from '$lib/image/shrink';
	import { formText } from '$lib/text/form';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		label,
		files = $bindable([]),
		hint,
		disabled = false
	}: {
		label: string;
		files?: File[];
		hint?: string;
		disabled?: boolean;
	} = $props();

	const previews = $derived(files.map((file) => ({ file, url: file.type.startsWith('image/') ? URL.createObjectURL(file) : null })));

	$effect(() => {
		const urls = previews.flatMap((preview) => (preview.url ? [preview.url] : []));
		return () => urls.forEach((url) => URL.revokeObjectURL(url));
	});

	let preparing = $state(false);

	async function pick(event: Event & { currentTarget: HTMLInputElement }): Promise<void> {
		const chosen = Array.from(event.currentTarget.files ?? []);
		event.currentTarget.value = '';
		preparing = true;
		try {
			files = [...files, ...(await Promise.all(chosen.map(preparePhoto)))];
		} finally {
			preparing = false;
		}
	}
</script>

<section class="flex flex-col gap-2">
	<h3 class="text-xs font-semibold text-slate-600">{label}</h3>

	<label class="flex h-10 w-full max-w-md overflow-hidden rounded-md border border-slate-200 bg-white focus-within:border-brand-focus focus-within:ring-2 focus-within:ring-brand-line {disabled || preparing ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}">
		<span class="flex items-center border-r border-slate-200 bg-brand-page px-4 text-sm font-semibold whitespace-nowrap text-brand transition-colors duration-(--duration-instant) hover:bg-brand-tint motion-reduce:transition-none">{preparing ? formText.preparingPhoto : files.length > 0 ? formText.addFiles : formText.chooseFile}</span>
		<span class="flex min-w-0 flex-1 items-center truncate px-3 text-sm {files.length > 0 ? 'text-slate-800' : 'text-slate-500'}">{files.length > 0 ? format(formText.filesChosen, { count: files.length }) : formText.noFile}</span>
		<input type="file" accept="image/*,video/*" multiple class="sr-only" disabled={disabled || preparing} onchange={(event) => void pick(event)} />
	</label>
	{#if previews.length > 0}
		<ul class="flex flex-wrap gap-2">
			{#each previews as preview, index (index)}
				<li class="relative size-20 overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
					{#if preview.url}
						<img src={preview.url} alt={preview.file.name} class="size-full object-cover" />
					{:else}
						<span class="flex size-full flex-col items-center justify-center gap-1 px-1 text-center text-xs text-slate-500">
							<i class="ti ti-video text-xl" aria-hidden="true"></i>
							<span class="line-clamp-2 break-all">{preview.file.name}</span>
						</span>
					{/if}
					<button
						type="button"
						{disabled}
						aria-label={format(controlText.discardFile, { name: preview.file.name })}
						onclick={() => (files = files.filter((_, at) => at !== index))}
						class="absolute right-1 top-1 flex size-5 items-center justify-center rounded-full bg-slate-800/70 text-white hover:bg-slate-800 disabled:opacity-50"
					>
						<i class="ti ti-x text-xs" aria-hidden="true"></i>
					</button>
				</li>
			{/each}
		</ul>
	{/if}
	{#if hint}
		<p class="text-xs text-slate-500">{hint}</p>
	{/if}
</section>
