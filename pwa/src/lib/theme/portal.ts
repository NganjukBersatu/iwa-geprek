/** Memindahkan elemen ke <body> agar posisi tetapnya tidak ikut terpengaruh skala atau transformasi induknya. */
export function portal(node: HTMLElement): { destroy: () => void } {
	document.body.appendChild(node);
	return { destroy: () => node.remove() };
}
