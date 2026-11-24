import { ApiError } from '$lib/api/http';
import { userMessage } from '$lib/api/user-message';
import { toast } from '$lib/components/feedback/toast.svelte';
import { format } from '$lib/text/format';
import type { CreateText } from '$lib/text/record-detail';

export type RecordCreateConfig<T, U, C> = {
	/** What the form needs besides its fields, such as the list of roles. */
	context?: () => Promise<C>;
	create: (body: U) => Promise<T>;
	name: (created: T) => string;
	/** Replaces the standard saved sentence, such as when one save made records in several branches. */
	message?: (created: T) => string;
	/** The address to open once the record exists. */
	after: (created: T) => string;
	text: CreateText;
};

/** A new record on a page of its own: loads what the form needs, saves, and says where to go next. */
export class RecordCreateState<T, U, C = null> {
	context = $state<C | null>(null);
	loading = $state(true);
	error = $state('');
	busy = $state(false);
	actionError = $state('');
	fieldErrors = $state<Record<string, string>>({});

	constructor(readonly config: RecordCreateConfig<T, U, C>) {}

	async load(): Promise<void> {
		this.loading = true;
		try {
			this.context = this.config.context ? await this.config.context() : null;
			this.error = '';
		} catch (error) {
			this.error = userMessage(error, this.config.text.loadFailed);
		} finally {
			this.loading = false;
		}
	}

	/** The address of the new record when it was saved, otherwise null. */
	async save(body: U): Promise<string | null> {
		this.busy = true;
		this.actionError = '';
		this.fieldErrors = {};
		try {
			const created = await this.config.create(body);
			toast.show(this.config.message ? this.config.message(created) : format(this.config.text.created, { name: this.config.name(created) }));
			return this.config.after(created);
		} catch (error) {
			this.fieldErrors = error instanceof ApiError ? error.fieldErrors : {};
			this.actionError = userMessage(error, this.config.text.createFailed);
			return null;
		} finally {
			this.busy = false;
		}
	}
}
