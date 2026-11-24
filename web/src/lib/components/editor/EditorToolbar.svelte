<script lang="ts">
	import type { Editor } from '@tiptap/core';
	import { controlText } from '$lib/text/controls';

	let {
		editor,
		version,
		uploading,
		onpick,
		ontidy
	}: {
		editor: Editor;
		/** Changes on every edit or cursor move, so the pressed state of each button follows the text. */
		version: number;
		uploading: number;
		onpick: () => void;
		ontidy: () => void;
	} = $props();

	type Tool = { icon: string; label: string; active?: () => boolean; run: () => void; disabled?: () => boolean };

	const chain = () => editor.chain().focus();

	const groups: { name: string; tools: Tool[] }[] = [
		{
			name: controlText.history,
			tools: [
				{ icon: 'arrow-back-up', label: controlText.undo, run: () => chain().undo().run(), disabled: () => !editor.can().undo() },
				{ icon: 'arrow-forward-up', label: controlText.redo, run: () => chain().redo().run(), disabled: () => !editor.can().redo() }
			]
		},
		{
			name: controlText.heading,
			tools: [
				{ icon: 'h-1', label: controlText.headingLarge, active: () => editor.isActive('heading', { level: 1 }), run: () => chain().toggleHeading({ level: 1 }).run() },
				{ icon: 'h-2', label: controlText.headingMedium, active: () => editor.isActive('heading', { level: 2 }), run: () => chain().toggleHeading({ level: 2 }).run() },
				{ icon: 'h-3', label: controlText.headingSmall, active: () => editor.isActive('heading', { level: 3 }), run: () => chain().toggleHeading({ level: 3 }).run() }
			]
		},
		{
			name: controlText.paragraph,
			tools: [
				{ icon: 'bold', label: controlText.bold, active: () => editor.isActive('bold'), run: () => chain().toggleBold().run() },
				{ icon: 'italic', label: controlText.italic, active: () => editor.isActive('italic'), run: () => chain().toggleItalic().run() }
			]
		},
		{
			name: controlText.list,
			tools: [
				{ icon: 'list', label: controlText.bulletList, active: () => editor.isActive('bulletList'), run: () => chain().toggleBulletList().run() },
				{ icon: 'list-numbers', label: controlText.numberedList, active: () => editor.isActive('orderedList'), run: () => chain().toggleOrderedList().run() },
				{ icon: 'checklist', label: controlText.taskList, active: () => editor.isActive('taskList'), run: () => chain().toggleTaskList().run() },
				{ icon: 'quote', label: controlText.quote, active: () => editor.isActive('blockquote'), run: () => chain().toggleBlockquote().run() }
			]
		},
		{
			name: controlText.insert,
			tools: [
				{ icon: 'separator-horizontal', label: controlText.divider, run: () => chain().setHorizontalRule().run() },
				{ icon: 'photo-video', label: controlText.insertMedia, run: () => onpick(), disabled: () => uploading > 0 }
			]
		}
	];

	const base = 'flex size-9 min-h-0 min-w-0 items-center justify-center rounded-lg focus-visible:outline-2 focus-visible:outline-brand disabled:opacity-40 disabled:hover:bg-transparent';
	const look = (pressed: boolean) => (pressed ? `${base} bg-brand-soft text-brand` : `${base} text-slate-600 hover:bg-brand-soft hover:text-brand`);
</script>

<div role="toolbar" aria-label={controlText.textFormat} class="flex flex-wrap items-center gap-x-1 gap-y-0.5 border-b border-slate-100 bg-slate-50 px-2 py-1">
	{#key version}
		{#each groups as group, index (group.name)}
			{#if index > 0}<span class="mx-1 h-5 w-px bg-slate-200" aria-hidden="true"></span>{/if}
			{#each group.tools as item (item.icon)}
				{@const pressed = item.active?.() ?? false}
				<button type="button" class={look(pressed)} title={item.label} aria-label={item.label} aria-pressed={item.active ? pressed : undefined} disabled={item.disabled?.() ?? false} onclick={item.run}>
					<i class="ti ti-{item.icon} text-xl" aria-hidden="true"></i>
				</button>
			{/each}
		{/each}
	{/key}
	<span class="mx-1 h-5 w-px bg-slate-200" aria-hidden="true"></span>
	<button type="button" class="flex min-h-9 items-center gap-1.5 rounded-lg px-2 text-xs font-semibold text-slate-600 hover:bg-brand-soft hover:text-brand focus-visible:outline-2 focus-visible:outline-brand" title={controlText.tidyDescription} onclick={ontidy}>
		<i class="ti ti-wand text-xl" aria-hidden="true"></i>{controlText.tidy}
	</button>
	{#if uploading > 0}
		<span class="ml-auto flex items-center gap-1.5 pr-2 text-xs text-slate-500"><i class="ti ti-loader-2 animate-spin" aria-hidden="true"></i>{controlText.uploading}</span>
	{/if}
</div>
