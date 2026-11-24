import type { IconName } from '$lib/theme/icons';

export type BottomBarItem = { label: string; icon: IconName; selected: boolean; href: string; prominent?: boolean };
