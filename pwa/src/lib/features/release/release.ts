import { version } from '../../../../package.json';

import type { StringKey } from '$lib/text/strings';
import type { IconName } from '$lib/theme/icons';

export type ReleaseNote = { icon: IconName; key: StringKey };

// Diganti setiap rilis PWA dan dibaca juga oleh halaman Unduhan lewat generate-release.mjs, jadi bentuk barisnya dijaga tetap.
export const PWA_RELEASE = {
	version,
	notes: [
		{ icon: 'CalendarCheck', key: 'release_employee_routine_tasks' },
		{ icon: 'Checklist', key: 'release_employee_task_sections' },
		{ icon: 'Refresh', key: 'release_employee_fix_submission' },
		{ icon: 'ClipboardCheck', key: 'release_employee_follow_up_source' }
	] satisfies ReleaseNote[]
};
