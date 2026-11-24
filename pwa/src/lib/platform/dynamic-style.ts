import type { Action } from 'svelte/action';

type StyleValue = string | number | null | undefined;

/** Memasang gaya lewat objek gaya, yang CSP ketat izinkan; atribut style dan arahan style: milik Svelte tidak. Nilai kosong menghapus propertinya. */
export const dynamicStyle: Action<HTMLElement | SVGElement, Record<string, StyleValue>> = (node, initial) => {
	let applied = new Set<string>();
	const paint = (values: Record<string, StyleValue>) => {
		const next = new Set<string>();
		for (const [name, value] of Object.entries(values)) {
			if (value === undefined || value === null || value === '') continue;
			node.style.setProperty(name, String(value));
			next.add(name);
		}
		for (const name of applied) {
			if (!next.has(name)) node.style.removeProperty(name);
		}
		applied = next;
	};
	paint(initial);
	return { update: paint };
};
