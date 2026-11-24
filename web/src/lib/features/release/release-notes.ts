import type { ReleaseNote } from './release';
import { adminReleaseText } from '$lib/text/admin-release';

// Milik klien dan diganti setiap rilis web admin; ikon memakai nama kelas Tabler tanpa awalan ti-.
export const RELEASE_NOTES: readonly ReleaseNote[] = [
	{ icon: 'chart-line', text: adminReleaseText.reports },
	{ icon: 'tools-kitchen-2', text: adminReleaseText.menuAndRecipes },
	{ icon: 'packages', text: adminReleaseText.stock },
	{ icon: 'users', text: adminReleaseText.employees },
	{ icon: 'building-store', text: adminReleaseText.branches }
];
