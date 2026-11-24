import { errorText } from '$lib/text/errors';
import { format } from '$lib/text/format';
import { ApiError } from './http';

const SERVER_ERROR_FROM = 500;
const CLIENT_ERROR_FROM = 400;
const SECONDS_PER_MINUTE = 60;

/** The one place an error becomes a sentence for the person; a screen shows this, never `error.message`. */
export function userMessage(error: unknown, fallback: string = errorText.unknown): string {
	if (!(error instanceof ApiError)) return fallback;

	const template = error.code ? errorText.codes[error.code] : undefined;
	if (template) {
		const minutes = error.retryAfterSeconds === null ? null : Math.max(1, Math.ceil(error.retryAfterSeconds / SECONDS_PER_MINUTE));
		// A wait that the server did not state cannot be told, so the server's own sentence is used instead.
		if (minutes !== null || !template.includes('{minutes}')) return format(template, { minutes: minutes ?? '' });
	}

	if (error.status >= SERVER_ERROR_FROM) {
		return error.requestId ? format(errorText.serverWithReference, { requestId: error.requestId }) : errorText.server;
	}
	// Until every rule has a code of its own, a sentence the server wrote for a refused request is shown as written.
	if (error.status >= CLIENT_ERROR_FROM && error.serverMessage) return error.serverMessage;
	return errorText.statuses[error.status] ?? fallback;
}
