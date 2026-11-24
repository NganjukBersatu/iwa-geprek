import { SvelteSet } from 'svelte/reactivity';

export class Selection {
	private chosen = new SvelteSet<string>();
	/** The checkboxes stay hidden until the person asks to pick several rows. */
	enabled = $state(false);

	setMode(on: boolean): void {
		this.enabled = on;
		if (!on) this.chosen.clear();
	}

	toggleMode(): void {
		this.setMode(!this.enabled);
	}

	stop(): void {
		this.enabled = false;
		this.chosen.clear();
	}

	get count(): number {
		return this.chosen.size;
	}

	get ids(): string[] {
		return [...this.chosen];
	}

	has(id: string): boolean {
		return this.chosen.has(id);
	}

	toggle(id: string): void {
		if (this.chosen.has(id)) this.chosen.delete(id);
		else this.chosen.add(id);
	}

	remove(id: string): void {
		this.chosen.delete(id);
	}

	allIn(ids: string[]): boolean {
		return ids.length > 0 && ids.every((id) => this.chosen.has(id));
	}

	setAll(ids: string[], on: boolean): void {
		for (const id of ids) {
			if (on) this.chosen.add(id);
			else this.chosen.delete(id);
		}
	}

	clear(): void {
		this.chosen.clear();
	}
}
