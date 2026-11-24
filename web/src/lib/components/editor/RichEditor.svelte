<script lang="ts">
	import { userMessage } from '$lib/api/user-message';
	import { Editor } from '@tiptap/core';
	import './editor-base.css';
	import { onDestroy, onMount } from 'svelte';
	import { preparePhoto } from '$lib/image/shrink';
	import { toDoc, toMarkdown, tidyMarkdown } from './document';
	import EditorToolbar from './EditorToolbar.svelte';
	import { editorExtensions, type MediaKind, type UploadedMedia } from './extensions';
	import { controlText } from '$lib/text/controls';

	let {
		value = $bindable(''),
		label,
		placeholder = '',
		onupload
	}: {
		/** The stored Markdown; the editor shows it as finished text and writes it back on every change. */
		value?: string;
		label: string;
		placeholder?: string;
		/** Stores a photo or video and answers with its address and what it turned out to be. */
		onupload: (file: File) => Promise<UploadedMedia>;
	} = $props();

	const VIDEO_KIND = 'video';

	let element = $state<HTMLDivElement | null>(null);
	let picker = $state<HTMLInputElement | null>(null);
	let editor = $state<Editor | null>(null);
	let version = $state(0);
	let uploading = $state(0);
	let problem = $state('');
	let dragging = $state(false);
	// What the editor last wrote, so a value coming back from outside (a resumed draft) can be told from an echo.
	let written = '';

	const contentClass = [
		'min-h-72 px-3 py-2 text-sm leading-6 text-slate-800 focus:outline-none',
		'[&_h1]:text-2xl [&_h1]:font-semibold [&_h2]:text-xl [&_h2]:font-semibold [&_h3]:text-base [&_h3]:font-semibold',
		'[&_p]:my-1 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:my-0.5',
		'[&_ul[data-type=taskList]]:list-none [&_ul[data-type=taskList]]:pl-0 [&_li[data-type=taskItem]]:flex [&_li[data-type=taskItem]]:gap-2 [&_li[data-type=taskItem]>label]:mt-0.5',
		'[&_blockquote]:rounded-r-lg [&_blockquote]:border-l-4 [&_blockquote]:border-brand-line [&_blockquote]:bg-brand-page [&_blockquote]:px-3 [&_blockquote]:py-1',
		'[&_hr]:my-3 [&_hr]:border-slate-200 [&_.ProseMirror-selectednode]:ring-2 [&_.ProseMirror-selectednode]:ring-brand',
		'[&_.is-editor-empty:first-child]:before:pointer-events-none [&_.is-editor-empty:first-child]:before:float-left [&_.is-editor-empty:first-child]:before:h-0 [&_.is-editor-empty:first-child]:before:text-slate-500 [&_.is-editor-empty:first-child]:before:content-[attr(data-placeholder)]'
	].join(' ');

	async function send(files: File[], at?: number): Promise<void> {
		const media = files.filter((file) => file.type.startsWith('image/') || file.type.startsWith('video/'));
		if (media.length === 0) return;
		problem = '';
		for (const file of media) {
			uploading += 1;
			try {
				const stored = await onupload(await preparePhoto(file));
				const kind: MediaKind = stored.kind === VIDEO_KIND ? 'video' : 'image';
				const alt = file.name.replace(/\.[^.]+$/, '') || (kind === 'video' ? 'video' : 'gambar');
				const node = { type: kind, attrs: { src: stored.url, alt } };
				if (at === undefined) editor?.chain().focus().insertContent(node).run();
				else editor?.chain().focus().insertContentAt(at, node).run();
			} catch (error) {
				problem = userMessage(error, controlText.uploadFailed);
			} finally {
				uploading -= 1;
			}
		}
	}

	function pick(event: Event & { currentTarget: HTMLInputElement }): void {
		const files = [...(event.currentTarget.files ?? [])];
		event.currentTarget.value = '';
		void send(files);
	}

	function tidy(): void {
		if (!editor) return;
		editor.chain().focus().setContent(toDoc(tidyMarkdown(toMarkdown(editor.getJSON()))), true).run();
	}

	onMount(() => {
		if (!element) return;
		written = value;
		editor = new Editor({
			element,
			injectCSS: false,
			extensions: editorExtensions(placeholder),
			content: toDoc(value),
			editorProps: {
				attributes: { class: contentClass, 'aria-label': label, role: 'textbox', 'aria-multiline': 'true' },
				handlePaste: (_view, event) => {
					const files = [...(event.clipboardData?.files ?? [])];
					if (!files.some((file) => file.type.startsWith('image/') || file.type.startsWith('video/'))) return false;
					event.preventDefault();
					void send(files);
					return true;
				},
				handleDrop: (view, event) => {
					dragging = false;
					const files = [...(event.dataTransfer?.files ?? [])];
					if (files.length === 0) return false;
					event.preventDefault();
					void send(files, view.posAtCoords({ left: event.clientX, top: event.clientY })?.pos);
					return true;
				}
			},
			onUpdate: ({ editor: current }) => {
				written = toMarkdown(current.getJSON());
				value = written;
			},
			onTransaction: () => {
				version += 1;
			}
		});
	});

	$effect(() => {
		const incoming = value;
		if (!editor || incoming === written) return;
		written = incoming;
		editor.commands.setContent(toDoc(incoming), false);
	});

	onDestroy(() => editor?.destroy());
</script>

<div class="flex flex-col gap-1">
	<span class="text-xs font-semibold text-slate-600">{label}</span>
	<div
		role="group"
		aria-label={label}
		class="overflow-hidden rounded-lg border bg-white {dragging ? 'border-brand ring-2 ring-brand-line' : 'border-slate-200'}"
		ondragover={() => (dragging = true)}
		ondragleave={() => (dragging = false)}
	>
		{#if editor}
			<EditorToolbar {editor} {version} {uploading} onpick={() => picker?.click()} ontidy={tidy} />
		{/if}
		<div bind:this={element}></div>
		<input bind:this={picker} type="file" accept="image/*,video/*" multiple class="hidden" onchange={pick} />
	</div>
	<p class="text-xs text-slate-500">{controlText.editorHint}</p>
	{#if problem}
		<p class="rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{problem}</p>
	{/if}
</div>
