import { tick } from 'svelte';

/** The boxes that are marked as refused, in the order they stand on the page; a dropdown button cannot carry aria-invalid, so it carries data-invalid. */
function refusedBoxes(): HTMLElement[] {
	return [...document.querySelectorAll<HTMLElement>('[aria-invalid="true"], [data-invalid="true"]')];
}

/** Puts the cursor in the n-th refused box, after the page has been redrawn with the marks. */
export async function focusRefused(index = 0): Promise<void> {
	await tick();
	const box = refusedBoxes()[index];
	box?.focus();
	box?.scrollIntoView({ block: 'center', behavior: 'smooth' });
}

export type RefusedField = { field: string; label: string; message: string };

/**
 * What a form refuses, by field name, shown under each field: first what the form found by itself, then what the server refused.
 * `labels` lists the fields in the order they stand on the page; it is also the name each one gets in the summary.
 * A form with repeated rows gives a function, so the list follows the rows that stand on the page.
 */
export class FieldErrors {
	#found = $state<Record<string, string>>({});

	constructor(
		labels: Record<string, string> | (() => Record<string, string>),
		private readonly server: () => Record<string, string> = () => ({})
	) {
		this.labelsOf = typeof labels === 'function' ? labels : () => labels;
	}

	private readonly labelsOf: () => Record<string, string>;

	private get labels(): Record<string, string> {
		return this.labelsOf();
	}

	get(field: string): string | undefined {
		return this.#found[field] ?? this.server()[field];
	}

	/** The refused fields that stand on the page, in page order. */
	get refused(): RefusedField[] {
		return Object.keys(this.labels).flatMap((field) => {
			const message = this.get(field);
			return message ? [{ field, label: this.labels[field] ?? field, message }] : [];
		});
	}

	/** What the server refused about a field that is not on this form: shown as a sentence of its own, never lost. */
	get stray(): string[] {
		return Object.entries(this.server())
			.filter(([field]) => !(field in this.labels))
			.map(([, message]) => message);
	}

	get count(): number {
		return this.refused.length;
	}

	/** True when nothing was found; otherwise the marks are set and the cursor goes to the first refused box. */
	check(found: Record<string, string>): boolean {
		this.#found = found;
		if (Object.keys(found).length === 0) return true;
		void focusRefused();
		return false;
	}

	/** Replaces what was found without moving the cursor, for a form that checks again as its fields change after a refused send. */
	refresh(found: Record<string, string>): void {
		this.#found = found;
	}

	reset(): void {
		this.#found = {};
	}
}
