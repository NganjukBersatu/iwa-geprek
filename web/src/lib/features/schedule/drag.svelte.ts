export type DragItem = { kind: 'pool'; userId: string; label: string } | { kind: 'assignment'; id: string; label: string };
export type DropTarget = { kind: 'date'; date: string } | { kind: 'assignment'; id: string; date: string | null } | { kind: 'pool' };

const MOVE_THRESHOLD = 6;
const EDGE_PIXELS = 72;
const SCROLL_STEP = 14;

/**
 * Drag with pointer events, so it works the same with a mouse and a finger; no library.
 * Drop targets mark themselves with data-drop="date|assignment|pool" and the matching data-date or data-id.
 */
export class Drag {
	item = $state<DragItem | null>(null);
	x = $state(0);
	y = $state(0);
	over = $state<DropTarget | null>(null);

	private pending: DragItem | null = null;
	private frame = 0;
	private startX = 0;
	private startY = 0;

	constructor(
		private readonly ondrop: (item: DragItem, target: DropTarget) => void,
		private readonly onclick: (item: DragItem) => void
	) {}

	start = (event: PointerEvent, item: DragItem): void => {
		if (event.button !== 0) return;
		this.pending = item;
		this.startX = event.clientX;
		this.startY = event.clientY;
		window.addEventListener('pointermove', this.move);
		window.addEventListener('pointerup', this.end);
		window.addEventListener('pointercancel', this.cancel);
	};

	private target(x: number, y: number): DropTarget | null {
		const element = document.elementFromPoint(x, y)?.closest<HTMLElement>('[data-drop]');
		if (!element) return null;
		const { drop, date, id } = element.dataset;
		if (drop === 'date' && date) return { kind: 'date', date };
		if (drop === 'assignment' && id) return { kind: 'assignment', id, date: element.closest<HTMLElement>('[data-drop="date"]')?.dataset.date ?? null };
		if (drop === 'pool') return { kind: 'pool' };
		return null;
	}

	private move = (event: PointerEvent): void => {
		if (!this.pending) return;
		if (!this.item) {
			if (Math.hypot(event.clientX - this.startX, event.clientY - this.startY) < MOVE_THRESHOLD) return;
			this.item = this.pending;
			this.frame = requestAnimationFrame(this.scroll);
		}
		this.x = event.clientX;
		this.y = event.clientY;
		this.over = this.target(event.clientX, event.clientY);
	};

	/** Di dekat tepi papan dan halaman, keduanya ikut bergulir mengikuti jari, supaya kotak di luar layar tetap terjangkau. */
	private scroll = (): void => {
		const board = document.querySelector<HTMLElement>('[data-drag-scroll]');
		const page = document.querySelector<HTMLElement>('[data-page-scroll]');
		if (this.item) {
			if (board) {
				const box = board.getBoundingClientRect();
				if (this.x > box.right - EDGE_PIXELS) {
					board.scrollLeft += SCROLL_STEP;
				} else if (this.x < box.left + EDGE_PIXELS) {
					board.scrollLeft -= SCROLL_STEP;
				}
			}
			if (page) {
				const box = page.getBoundingClientRect();
				if (this.y > box.bottom - EDGE_PIXELS) {
					page.scrollTop += SCROLL_STEP;
				} else if (this.y < box.top + EDGE_PIXELS) {
					page.scrollTop -= SCROLL_STEP;
				}
			}
			this.over = this.target(this.x, this.y);
		}
		this.frame = requestAnimationFrame(this.scroll);
	};

	private end = (event: PointerEvent): void => {
		const pending = this.pending;
		const dragging = this.item;
		const target = dragging ? this.target(event.clientX, event.clientY) : null;
		this.cancel();
		if (!pending) return;
		if (dragging) {
			if (target) this.ondrop(dragging, target);
		} else {
			this.onclick(pending);
		}
	};

	private cancel = (): void => {
		cancelAnimationFrame(this.frame);
		window.removeEventListener('pointermove', this.move);
		window.removeEventListener('pointerup', this.end);
		window.removeEventListener('pointercancel', this.cancel);
		this.pending = null;
		this.item = null;
		this.over = null;
	};
}
