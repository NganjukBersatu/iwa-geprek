import { mergeAttributes, Node, type Extensions } from '@tiptap/core';
import Placeholder from '@tiptap/extension-placeholder';
import TaskItem from '@tiptap/extension-task-item';
import TaskList from '@tiptap/extension-task-list';
import StarterKit from '@tiptap/starter-kit';

export type MediaKind = 'image' | 'video';

/** What an upload answers: the address to place, and whether the server judged it a photo or a video. */
export type UploadedMedia = { url: string; kind: string };

const MEDIA_CLASS = 'my-2 max-h-80 w-full rounded-xl border border-slate-100 object-contain';

function mediaNode(name: MediaKind, tag: 'img' | 'video', extra: Record<string, string>) {
	return Node.create({
		name,
		group: 'block',
		atom: true,
		draggable: true,
		addAttributes() {
			return { src: { default: null }, alt: { default: '' } };
		},
		parseHTML() {
			return [{ tag: `${tag}[src]` }];
		},
		renderHTML({ HTMLAttributes }) {
			return [tag, mergeAttributes(HTMLAttributes, extra, { class: MEDIA_CLASS })];
		}
	});
}

/** Only what the stored Markdown can hold: headings 1–3, bold, italic, lists, checklist, quote, divider, picture, video. */
export function editorExtensions(placeholder: string): Extensions {
	return [
		StarterKit.configure({ code: false, codeBlock: false, strike: false, heading: { levels: [1, 2, 3] } }),
		Placeholder.configure({ placeholder }),
		TaskList,
		TaskItem.configure({ nested: false }),
		mediaNode('image', 'img', { loading: 'lazy' }),
		mediaNode('video', 'video', { controls: 'true', preload: 'metadata', playsinline: 'true' })
	];
}
