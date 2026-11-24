import { ApiError } from '$lib/api/http';
import { userMessage } from '$lib/api/user-message';
import { toast } from '$lib/components/feedback/toast.svelte';
import { format } from '$lib/text/format';
import type { RecordText } from '$lib/text/record-detail';

/** What differs between one kind of record and another; everything else on a record page is shared. */
export type RecordDetailConfig<T, U, C> = {
	load: (id: string) => Promise<T>;
	/** What the edit form needs besides the record, such as the list of roles. */
	context?: () => Promise<C>;
	update?: (record: T, body: U) => Promise<T>;
	remove?: (record: T) => Promise<void>;
	name: (record: T) => string;
	text: RecordText;
};

/** One record on its own page: loaded by ID, edited or deleted from there, and the only place its row actions live. */
export class RecordDetailState<T, U = never, C = null> {
	record = $state<T | null>(null);
	context = $state<C | null>(null);
	loading = $state(true);
	error = $state('');
	busy = $state(false);
	actionError = $state('');
	fieldErrors = $state<Record<string, string>>({});
	removing = $state(false);
	private token = 0;

	constructor(
		readonly id: string,
		readonly config: RecordDetailConfig<T, U, C>
	) {}

	/** Reloads without dimming the screen: what is shown stays until the fresh data arrives. */
	refresh(): Promise<void> {
		return this.load(true);
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		try {
			const [record, context] = await Promise.all([this.config.load(this.id), this.config.context ? this.config.context() : Promise.resolve(null as C)]);
			if (token !== this.token) return;
			this.record = record;
			this.context = context;
			this.error = '';
		} catch (error) {
			if (token !== this.token) return;
			if (!quiet) {
				this.record = null;
				this.error = userMessage(error, this.config.text.loadFailed);
			}
		} finally {
			if (token === this.token) this.loading = false;
		}
	}

	/** Clears what a previous visit to the edit page left behind. */
	resetForm(): void {
		this.actionError = '';
		this.fieldErrors = {};
	}

	askRemove(): void {
		this.actionError = '';
		this.removing = true;
	}

	closeDialogs(): void {
		this.removing = false;
		this.actionError = '';
		this.fieldErrors = {};
	}

	/** True when the record was saved, so the edit page returns to the record. */
	async save(body: U): Promise<boolean> {
		const current = this.record;
		const update = this.config.update;
		if (!current || !update) return false;
		if (!(await this.attempt(async () => (this.record = await update(current, body)), this.config.text.saveFailed))) return false;
		toast.show(format(this.config.text.saved, { name: this.record ? this.config.name(this.record) : this.config.name(current) }));
		return true;
	}

	/** True when the record was deleted, so the page returns to the list. */
	async delete(): Promise<boolean> {
		const current = this.record;
		const remove = this.config.remove;
		if (!current || !remove) return false;
		return this.attempt(() => remove(current), this.config.text.removeFailed);
	}

	/** Runs an action that answers with the fresh record, such as switching a method off or replacing its picture, and shows that record. */
	async change(work: (record: T) => Promise<T>, fallback: string): Promise<boolean> {
		const current = this.record;
		if (!current) return false;
		return this.attempt(async () => (this.record = await work(current)), fallback);
	}

	/** Runs any other action of the page with the shared busy state and error, such as issuing a new device code. */
	run(work: () => Promise<unknown>, fallback: string): Promise<boolean> {
		return this.attempt(work, fallback);
	}

	private async attempt(work: () => Promise<unknown>, fallback: string): Promise<boolean> {
		this.busy = true;
		this.actionError = '';
		this.fieldErrors = {};
		try {
			await work();
			return true;
		} catch (error) {
			this.fieldErrors = error instanceof ApiError ? error.fieldErrors : {};
			this.actionError = userMessage(error, fallback);
			return false;
		} finally {
			this.busy = false;
		}
	}
}
