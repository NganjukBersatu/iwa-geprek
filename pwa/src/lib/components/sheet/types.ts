import type { BadgeTone } from '$lib/components/feedback/types';
import type { IconName } from '$lib/theme/icons';

export type NoticeSheetItem = { title: string; caption: string | null; icon?: IconName };

export type PermissionGateItem = { title: string; description: string; statusText: string; tone: BadgeTone; onclick: (() => void) | null };
