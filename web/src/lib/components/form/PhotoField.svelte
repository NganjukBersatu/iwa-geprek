<script lang="ts">
	import { preparePhoto } from '$lib/image/shrink';
	import { formText } from '$lib/text/form';
	import type { Snippet } from 'svelte';

	let {
		label,
		current,
		alt,
		file = $bindable(null),
		disabled = false,
		onpick,
		actions,
		variant = 'drop'
	}: {
		label: string;
		current: string | null;
		alt: string;
		file?: File | null;
		disabled?: boolean;
		onpick?: (file: File) => void;
		actions?: Snippet;
		/** drop: a picture with a drop area. chooser: one line, a button and the name of the chosen file. */
		variant?: 'drop' | 'chooser';
	} = $props();

	let preparing = $state(false);
	let dragging = $state(false);
	let unreadable = $state(false);
	let preview = $state<string | null>(null);

	$effect(() => {
		const url = file ? URL.createObjectURL(file) : null;
		preview = url;
		unreadable = false;
		return () => {
			if (url) URL.revokeObjectURL(url);
		};
	});

	const shown = $derived(preview ?? current);
	const locked = $derived(disabled || preparing);

	async function take(chosen: File | undefined): Promise<void> {
		if (!chosen || locked) return;
		preparing = true;
		try {
			const prepared = await preparePhoto(chosen);
			if (onpick) onpick(prepared);
			else file = prepared;
		} finally {
			preparing = false;
		}
	}

	function pick(event: Event & { currentTarget: HTMLInputElement }): void {
		const chosen = event.currentTarget.files?.[0];
		event.currentTarget.value = '';
		void take(chosen);
	}

	function drop(event: DragEvent): void {
		event.preventDefault();
		dragging = false;
		void take(event.dataTransfer?.files[0]);
	}

	function dragover(event: DragEvent): void {
		event.preventDefault();
		if (!locked) dragging = true;
	}

	// An image pasted anywhere while this field is shown lands in it; pasted text is left alone.
	function paste(event: ClipboardEvent): void {
		const chosen = event.clipboardData?.files[0];
		if (!chosen || locked) return;
		event.preventDefault();
		void take(chosen);
	}
</script>

<svelte:document onpaste={paste} />

<section class="flex flex-col gap-2">
	<h3 class="text-xs font-semibold text-slate-600">{label}</h3>
	{#if variant === 'chooser'}
		<label class="flex h-10 w-full max-w-md overflow-hidden rounded-md border border-slate-200 bg-white focus-within:border-brand-focus focus-within:ring-2 focus-within:ring-brand-line {locked ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}" ondragover={dragover} ondragleave={() => (dragging = false)} ondrop={drop}>
			<span class="flex items-center border-r border-slate-200 bg-brand-page px-4 text-sm font-semibold whitespace-nowrap text-brand transition-colors duration-(--duration-instant) hover:bg-brand-tint motion-reduce:transition-none">{preparing ? formText.preparingPhoto : formText.chooseFile}</span>
			<span class="flex min-w-0 flex-1 items-center truncate px-3 text-sm {file ? 'text-slate-800' : 'text-slate-500'} {dragging ? 'bg-brand-soft' : ''}" title={file?.name}>{file ? file.name : current ? formText.savedPhoto : formText.noFile}</span>
			<input type="file" accept="image/*" class="sr-only" disabled={locked} onchange={pick} />
		</label>
		<p class="text-xs text-slate-500">{formText.photoHint}</p>
	{:else}
	<label
		class="flex cursor-pointer items-center rounded-lg border border-brand-line transition-colors motion-reduce:transition-none {shown && !unreadable
			? 'gap-3 bg-white p-2'
			: 'flex-col justify-center gap-1 border-dashed px-4 py-5 text-center'} {dragging ? 'border-brand bg-brand-soft' : shown && !unreadable ? 'hover:border-brand' : 'bg-brand-soft hover:border-brand'} {locked ? 'cursor-not-allowed opacity-60' : ''}"
		ondragover={dragover}
		ondragleave={() => (dragging = false)}
		ondrop={drop}
	>
		{#if shown && !unreadable}
			<img src={shown} {alt} class="h-20 w-28 shrink-0 rounded-md border border-brand-tint bg-brand-soft object-contain" onerror={() => (unreadable = true)} />
			<span class="flex min-w-0 flex-1 flex-col gap-0.5">
				<span class="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-ink">
					<i class="ti {preparing ? 'ti-loader-2 animate-spin' : 'ti-replace'} text-base text-brand" aria-hidden="true"></i>
					{preparing ? formText.preparingPhoto : formText.changePhoto}
				</span>
				<span class="truncate text-xs text-brand-muted">{file ? file.name : formText.savedPhotoHint}</span>
			</span>
		{:else}
			<i class="ti {preparing ? 'ti-loader-2 animate-spin' : 'ti-photo-up'} text-2xl text-brand" aria-hidden="true"></i>
			<span class="text-sm font-semibold text-brand-ink">{preparing ? formText.preparingPhoto : formText.dropPhoto}</span>
			<span class="text-xs text-brand-muted">{unreadable ? formText.previewUnavailable : formText.pasteHint}</span>
		{/if}
		<input type="file" accept="image/*" class="sr-only" disabled={locked} onchange={pick} />
	</label>
	{/if}
	{#if actions}
		<div class="flex flex-wrap items-center gap-2">{@render actions()}</div>
	{/if}
</section>
