import type { ReleaseNote } from './release';

// Milik klien dan diganti setiap rilis PWA; dibaca juga oleh halaman Unduhan lewat generate-release.mjs, jadi bentuk barisnya dijaga tetap.
export const RELEASE_NOTES: readonly ReleaseNote[] = [
	{ icon: 'UserCheck', key: 'release_employee_attendance' },
	{ icon: 'Calendar', key: 'release_employee_schedule' },
	{ icon: 'Checklist', key: 'release_employee_tasks' },
	{ icon: 'Book', key: 'release_employee_guides' }
];
