import { t } from '$lib/text/t';

/** Sebab kamera tidak bisa dibuka; satu daftar untuk gerbang izin dan pemindai QR. */
export type CameraProblem = 'denied' | 'missing' | 'busy' | 'unsupported' | 'failed';

const DENIED_ERRORS = ['NotAllowedError', 'SecurityError', 'PermissionDeniedError'];
const MISSING_ERRORS = ['NotFoundError', 'DevicesNotFoundError', 'OverconstrainedError'];
const BUSY_ERRORS = ['NotReadableError', 'TrackStartError', 'AbortError'];

/** Menggolongkan galat getUserMedia; TypeError berarti browser tidak menyediakan kamera (mis. bukan HTTPS). */
export function cameraProblemOf(error: unknown): CameraProblem {
	if (error instanceof TypeError) return 'unsupported';
	const name = error instanceof Error ? error.name : '';
	if (DENIED_ERRORS.includes(name)) return 'denied';
	if (MISSING_ERRORS.includes(name)) return 'missing';
	if (BUSY_ERRORS.includes(name)) return 'busy';
	return 'failed';
}

export function cameraProblemText(problem: CameraProblem): string {
	switch (problem) {
		case 'denied':
			return t('web_permission_camera_blocked');
		case 'missing':
			return t('web_permission_camera_missing');
		case 'busy':
			return t('web_permission_camera_busy');
		case 'unsupported':
			return t('web_permission_unsupported');
		case 'failed':
			return t('web_permission_camera_failed');
	}
}
