import type { Schemas } from '../contract';

export type Task = Schemas['TaskOut'];
export type TaskPage = Schemas['TaskPageOut'];
export type TaskOptions = Schemas['OptionsOut'];
export type TaskPerson = Schemas['PersonOut'];
export type TaskAttachment = Schemas['AttachmentOut'];
export type TaskUpdate = Schemas['TaskUpdateIn'];

/** What a new task is made of; the files travel beside it. */
export type TaskInput = {
	title: string;
	description: string;
	assignee_id: string | null;
	due_at: string | null;
	complete: boolean;
	/** The filling of a routine or outlet task this task follows up; null for an ordinary task. */
	source_run_id: string | null;
};
