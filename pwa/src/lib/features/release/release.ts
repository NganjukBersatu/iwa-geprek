import { RELEASE_NOTES } from './release-notes';

import type { StringKey } from '$lib/text/strings';
import type { IconName } from '$lib/theme/icons';

export type ReleaseNote = { icon: IconName; key: StringKey };

export const PWA_RELEASE: { version: string; notes: readonly ReleaseNote[] } = {
	version: __APP_VERSION__,
	notes: RELEASE_NOTES
};
