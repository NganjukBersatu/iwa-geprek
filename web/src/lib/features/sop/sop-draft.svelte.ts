import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { Sop, SopDraftContent, SopDraftSummary, SopInput, SopMedia } from '$lib/api/types';
import { getUser } from '$lib/auth/session';
import { sopText } from '$lib/text/sop';
import { format } from '$lib/text/format';

const MAX_TITLE = 120;
const FIRST_SLIDE_TITLE = '';
// Typing pauses this long before the draft is written; it is a debounce of edits, not a timer that asks the server.
const AUTOSAVE_PAUSE_MILLISECONDS = 2000;

export type SlideDraft = { uid: number; title: string; body: string };
export type AutosaveStatus = 'idle' | 'saving' | 'saved' | 'failed';
export type EditMode = 'one' | 'all';

/** One procedure being written: its details, its slides in order, which slide is open, and the draft kept on the server. */
export class SopDraftState {
	title = $state('');
	active = $state(true);
	outletId = $state('');
	slides = $state<SlideDraft[]>([]);
	selected = $state(0);
	mode = $state<EditMode>('one');
	loading = $state(true);
	saving = $state(false);
	error = $state('');
	problem = $state('');

	autosave = $state<AutosaveStatus>('idle');
	savedAt = $state<string | null>(null);
	/** A draft found on opening, waiting for the writer to continue it or throw it away. */
	pending = $state<SopDraftSummary | null>(null);
	/** True when the procedure was saved by someone after the pending draft was started. */
	conflict = $state(false);

	readonly canChooseEveryBranch = !getUser()?.outlet_id;

	private draftId: string | null;
	private version: number | null = null;
	private nextUid = 1;
	private snapshot = '';
	private drafted = '';
	private timer: ReturnType<typeof setTimeout> | undefined;

	constructor(
		readonly id: string | null,
		draftId: string | null = null,
		private readonly ondraft: (draftId: string) => void = () => {}
	) {
		this.draftId = draftId;
	}

	/** True once a draft of this new procedure was written. */
	get hasDraft(): boolean {
		return this.id === null && this.draftId !== null;
	}

	get current(): SlideDraft | null {
		return this.slides[Math.min(this.selected, this.slides.length - 1)] ?? null;
	}

	get dirty(): boolean {
		return this.snapshot !== this.state();
	}

	/** Something typed that is neither saved as the procedure nor yet written to the draft. */
	get unsaved(): boolean {
		return this.dirty && this.drafted !== this.state();
	}

	state(): string {
		return JSON.stringify([this.title, this.active, this.outletId, this.slides.map((slide) => [slide.title, slide.body])]);
	}

	private slide(title = FIRST_SLIDE_TITLE, body = ''): SlideDraft {
		return { uid: this.nextUid++, title, body };
	}

	async load(): Promise<void> {
		this.loading = true;
		this.error = '';
		try {
			if (this.id) {
				const [sop, drafts] = await Promise.all([api.sop.get(this.id), api.sop.drafts()]);
				this.fill(sop);
				this.pending = drafts.find((draft) => draft.sop_id === this.id) ?? null;
				this.conflict = this.pending !== null && this.pending.base_version !== sop.version;
			} else if (this.draftId) {
				const draft = await api.sop.draft(this.draftId);
				this.slides = [this.slide()];
				this.snapshot = this.state();
				this.fillContent(draft.content);
				this.drafted = this.state();
				this.savedAt = draft.updated_at;
				this.autosave = 'saved';
				return;
			} else {
				this.slides = [this.slide()];
			}
			this.snapshot = this.state();
			this.drafted = this.snapshot;
		} catch (error) {
			this.error = userMessage(error, sopText.openFailed);
		} finally {
			this.loading = false;
		}
	}

	private fill(sop: Sop): void {
		this.version = sop.version;
		this.title = sop.title;
		this.active = sop.active;
		this.outletId = sop.outlet_id ?? '';
		this.slides = sop.slides.map((slide) => this.slide(slide.title, slide.body));
	}

	private fillContent(content: SopDraftContent): void {
		this.title = content.title ?? '';
		this.active = content.active ?? true;
		this.outletId = content.outlet_id ?? '';
		const slides = (content.slides ?? []).map((slide) => this.slide(slide.title ?? '', slide.body ?? ''));
		this.slides = slides.length > 0 ? slides : [this.slide()];
		this.selected = 0;
	}

	async resume(): Promise<void> {
		const pending = this.pending;
		if (!pending) return;
		try {
			const draft = await api.sop.draft(pending.id);
			this.fillContent(draft.content);
			this.draftId = draft.id;
			this.drafted = this.state();
			this.savedAt = draft.updated_at;
			this.autosave = 'saved';
			this.pending = null;
		} catch (error) {
			this.problem = userMessage(error, sopText.draftOpenFailed);
		}
	}

	async discardPending(): Promise<void> {
		const pending = this.pending;
		if (!pending) return;
		try {
			await api.sop.discardDraft(pending.id);
			this.pending = null;
			this.conflict = false;
		} catch (error) {
			this.problem = userMessage(error, sopText.draftDiscardFailed);
		}
	}

	/** Called on every change; the draft is written once typing pauses, and never while an older draft awaits a decision. */
	changed(): void {
		clearTimeout(this.timer);
		if (this.loading || this.pending || !this.unsaved) return;
		this.timer = setTimeout(() => void this.writeDraft(), AUTOSAVE_PAUSE_MILLISECONDS);
	}

	private async writeDraft(): Promise<void> {
		const written = this.state();
		this.autosave = 'saving';
		try {
			const saved = await api.sop.saveDraft({
				id: this.draftId,
				sop_id: this.id,
				base_version: this.version,
				content: {
					title: this.title.slice(0, MAX_TITLE),
					active: this.active,
					outlet_id: this.outletId || null,
					slides: this.slides.map((slide) => ({ title: slide.title, body: slide.body }))
				}
			});
			if (!this.draftId && !this.id) this.ondraft(saved.id);
			this.draftId = saved.id;
			this.drafted = written;
			this.savedAt = saved.updated_at;
			this.autosave = 'saved';
		} catch {
			this.autosave = 'failed';
		}
		if (this.unsaved) this.changed();
	}

	select(index: number): void {
		this.selected = Math.max(0, Math.min(index, this.slides.length - 1));
	}

	add(): void {
		this.slides = [...this.slides, this.slide()];
		this.selected = this.slides.length - 1;
	}

	remove(index: number): void {
		if (this.slides.length <= 1) return;
		this.slides = this.slides.filter((_, at) => at !== index);
		this.select(index >= this.slides.length ? this.slides.length - 1 : index);
	}

	move(index: number, step: -1 | 1): void {
		const target = index + step;
		if (target < 0 || target >= this.slides.length) return;
		const copy = [...this.slides];
		[copy[index], copy[target]] = [copy[target]!, copy[index]!];
		this.slides = copy;
		this.selected = target;
	}

	/** The file goes to storage at once, so the editor can show it; the text holds only its address. */
	uploadMedia = (file: File): Promise<SopMedia> => api.sop.uploadMedia(file);

	private input(): SopInput | null {
		if (!this.title.trim()) return this.reject(sopText.titleRequired);
		if (this.title.trim().length > MAX_TITLE) return this.reject(format(sopText.titleTooLong, { max: MAX_TITLE }));
		const empty = this.slides.findIndex((slide) => !slide.title.trim());
		if (empty >= 0) {
			this.selected = empty;
			return this.reject(format(sopText.slideTitleMissing, { number: empty + 1 }));
		}
		this.problem = '';
		return {
			title: this.title.trim(),
			active: this.active,
			outlet_id: this.outletId || null,
			slides: this.slides.map((slide) => ({ title: slide.title.trim(), body: slide.body })),
			draft_id: this.draftId
		};
	}

	private reject(text: string): null {
		this.problem = text;
		return null;
	}

	/** True when saved; the problem, if any, stays in `problem`. Saving removes the draft. */
	async save(): Promise<boolean> {
		const body = this.input();
		if (!body) return false;
		clearTimeout(this.timer);
		this.saving = true;
		try {
			if (this.id) await api.sop.update(this.id, body);
			else await api.sop.create(body);
			this.snapshot = this.state();
			this.drafted = this.snapshot;
			this.draftId = null;
			return true;
		} catch (error) {
			this.problem = userMessage(error, sopText.saveFailed);
			return false;
		} finally {
			this.saving = false;
		}
	}

	/** Throws away the draft of a new procedure; nothing typed since is kept, so leaving the page asks nothing. */
	async discardDraft(): Promise<boolean> {
		const target = this.draftId;
		if (!target) return true;
		clearTimeout(this.timer);
		try {
			await api.sop.discardDraft(target);
			this.draftId = null;
			this.snapshot = this.state();
			this.drafted = this.snapshot;
			return true;
		} catch (error) {
			this.problem = userMessage(error, sopText.draftDiscardFailed);
			return false;
		}
	}

	dispose(): void {
		clearTimeout(this.timer);
	}
}
