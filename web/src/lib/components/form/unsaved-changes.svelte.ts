/** Whether the person has typed into a form that is not saved yet; the layout reads it before it leaves a page. */
class UnsavedChanges {
	has = $state(false);

	touch = (): void => {
		this.has = true;
	};

	clear = (): void => {
		this.has = false;
	};

	/** Svelte action: an edit anywhere inside the element counts, and leaving the element counts as clean. */
	watch = (node: HTMLElement): { destroy: () => void } => {
		node.addEventListener('input', this.touch);
		node.addEventListener('change', this.touch);
		return {
			destroy: () => {
				node.removeEventListener('input', this.touch);
				node.removeEventListener('change', this.touch);
				this.clear();
			}
		};
	};
}

export const unsavedChanges = new UnsavedChanges();
