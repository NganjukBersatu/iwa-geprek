import type { Ability, Screen } from '$lib/api/types';

export type NavLeaf = {
	href: string;
	label: string;
	/** The server screen whose gate decides whether the entry is shown. */
	screen: Screen;
	/** Bagian layar yang juga harus diizinkan, untuk entri yang hanya membuka bagian itu. */
	area?: Ability;
	exact?: boolean;
};

export type NavTop = NavLeaf & {
	icon: string;
};

export type NavGroup = {
	key: string;
	label: string;
	icon: string;
	items: NavLeaf[];
};

export type NavEntry = NavTop | NavGroup;

export type SidebarBrand = {
	logo: string;
	logoAlt: string;
	title: string;
	subtitle: string;
};

export type SidebarProfile = {
	href: string;
	label: string;
	subtitle?: string;
	photoUrl?: string | null;
	icon: string;
};

export function isGroup(entry: NavEntry): entry is NavGroup {
	return 'items' in entry;
}

const leavesOf = (entries: NavEntry[]): NavLeaf[] => entries.flatMap((entry) => (isGroup(entry) ? entry.items : [entry]));

/** Whether a page at this address belongs to the entry: the address itself, or a page inside it (never a sibling that only shares the first letters). */
const belongsTo = (leaf: NavLeaf, path: string): boolean => path === leaf.href || (!leaf.exact && path.startsWith(`${leaf.href}/`));

/**
 * The one entry shown as current. Several entries can contain the address (Daftar Bahan at /admin/ingredients holds /admin/ingredients/receipts),
 * so the most specific one, with the longest address, wins and the others stay quiet.
 */
export function activeHref(entries: NavEntry[], path: string): string | null {
	let found: string | null = null;
	for (const leaf of leavesOf(entries)) {
		if (belongsTo(leaf, path) && (found === null || leaf.href.length > found.length)) found = leaf.href;
	}
	return found;
}
