import { version } from '../../../../package.json';
import { releaseText } from '$lib/text/release';

export type ReleaseNote = { icon: string; text: string };

export type Release = { version: string; date: string; notes: ReleaseNote[] };

// Diganti setiap rilis web admin; versi mengikuti package.json, dan versi baru membuat ringkasan ini tampil sekali lagi untuk setiap akun.
export const WEB_RELEASE: Release = {
	version,
	date: '29 Oktober 2026',
	notes: [
		{ icon: 'layout-kanban', text: releaseText.stationMenu },
		{ icon: 'arrows-sort', text: releaseText.sortableColumns },
		{ icon: 'history', text: releaseText.moneyTrail },
		{ icon: 'alert-triangle', text: releaseText.depositedWarning },
		{ icon: 'report', text: releaseText.issuesOpenData },
		{ icon: 'chef-hat', text: releaseText.recipeToAllBranches }
	]
};
