import { listText } from '$lib/text/lists';
import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { Issue, IssueKind, IssueLevel, IssueReport } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageOf } from '$lib/components/pager/page-of';
import type { Page } from '$lib/nav/pages';
import { LEVELS, linkOf, textOf, type IssueLink, type IssueRow } from './kinds';
import { termText } from '$lib/text/terms';

export const PREVIEW_ROWS = 3;

export type IssueGroup = { kind: IssueKind; title: string; link: Page; total: number; rows: (IssueRow & { link: IssueLink })[]; page: number; expanded: boolean };
export type IssueSection = (typeof LEVELS)[number] & { count: number; groups: IssueGroup[] };

/** Laporan Masalah: one read of every finding; the page splits it by level, then by kind, and pages each kind on its own. */
export class IssuesState {
	filters = new Filters([{ kind: 'select', key: 'cabang', label: termText.branch, options: [] }]);

	loading = $state(true);
	error = $state('');
	data = $state<IssueReport | null>(null);
	collapsed = $state<Partial<Record<IssueLevel, boolean>>>({});
	pages = $state<Partial<Record<IssueKind, number>>>({});
	expanded = $state<Partial<Record<IssueKind, boolean>>>({});

	private token = 0;

	get branch(): string | null {
		return this.filters.get('cabang');
	}

	get sections(): IssueSection[] {
		const items = this.data?.items ?? [];
		return LEVELS.map((meta) => {
			const byKind = new Map<IssueKind, Issue[]>();
			for (const item of items) if (item.level === meta.level) byKind.set(item.kind, [...(byKind.get(item.kind) ?? []), item]);
			const groups = [...byKind].map(([kind, found]) => {
				const text = textOf(kind);
				const expanded = this.expanded[kind] ?? false;
				const { rows, page } = expanded ? pageOf(found, this.pages[kind] ?? 1) : { rows: found.slice(0, PREVIEW_ROWS), page: 1 };
				return { kind, title: text.title, link: text.link, total: found.length, rows: rows.map((issue) => ({ ...text.row(issue), link: linkOf(kind, issue) })), page, expanded };
			});
			return { ...meta, count: this.data ? this.data[meta.level] : 0, groups };
		});
	}

	setBranches(options: { value: string; label: string }[]): void {
		this.filters.setOptions('cabang', options);
	}

	// Bawaannya hanya tingkat pertama yang punya temuan yang terbuka, supaya halaman tidak memanjang.
	isCollapsed(level: IssueLevel, sections: IssueSection[]): boolean {
		return this.collapsed[level] ?? level !== sections.find((section) => section.groups.length > 0)?.level;
	}

	toggle(level: IssueLevel, sections: IssueSection[]): void {
		this.collapsed = { ...this.collapsed, [level]: !this.isCollapsed(level, sections) };
	}

	// Kartu menampilkan beberapa baris pertama; seluruhnya berhalaman setelah dibuka.
	expand(kind: IssueKind): void {
		this.expanded = { ...this.expanded, [kind]: !this.expanded[kind] };
		this.pages = { ...this.pages, [kind]: 1 };
	}

	setPage(kind: IssueKind, page: number): void {
		this.pages = { ...this.pages, [kind]: page };
	}

	/** Reloads without dimming or clearing: what the screen shows stays until the fresh data arrives. */
	refresh(): Promise<void> {
		return this.load(true);
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) {
			this.loading = true;
			this.error = '';
		}
		try {
			const data = await api.issues.list();
			if (token === this.token) this.data = data;
		} catch (error) {
			if (token !== this.token || quiet) return;
			this.data = null;
			this.error = userMessage(error, listText.reportLoadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}
}
