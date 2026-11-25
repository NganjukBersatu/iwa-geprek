import { api } from '$lib/api';
import type { MenuRoute, RouteState, StationRoute } from '$lib/api/types';
import { userMessage } from '$lib/api/user-message';
import type { Tone } from '$lib/components/card/tone';
import { Filters } from '$lib/components/filter/filters.svelte';
import { printerText as text } from '$lib/text/printers';
import { format } from '$lib/text/format';
import { ManageState } from '../manage/manage.svelte';

export type RouteLook = { label: string; tone: Tone; icon: string };

/** Satu tampilan untuk setiap keadaan stasiun, dipakai tabel stasiun, pratinjau rute, dan Kesiapan cabang. */
export const ROUTE_LOOKS: Record<RouteState, RouteLook> = {
	unused: { label: text.looks.unused, tone: 'neutral', icon: 'circle-minus' },
	printer_missing: { label: text.looks.printerMissing, tone: 'warning', icon: 'plug-x' },
	printer_disconnected: { label: text.looks.printerDisconnected, tone: 'danger', icon: 'plug-connected-x' },
	ready: { label: text.looks.ready, tone: 'success', icon: 'circle-check' }
};

/** Kalimat tempat struk stasiun dicetak, sama di tabel dan pratinjau. */
export function printedAt(route: StationRoute): string {
	if (route.state === 'unused') return text.looks.unused;
	if (route.kind === 'deliver') return text.notPrinting;
	if (!route.sender) return text.noSender;
	const printer = route.printer?.name ?? (route.kind === 'handover' ? text.receiptPrinter : format(text.stationPrinter, { station: route.station_name }));
	return format(route.kind === 'handover' ? text.handoverAt : text.sentFrom, { printer, sender: route.sender.name });
}

/** Siapa yang memegang layar stasiun ini; stasiun pembuat tanpa tablet tetap mencetak bila dikirim dari tablet kasir. */
export function shownOn(route: StationRoute): string {
	if (route.holders.length > 0) return route.holders.map((holder) => holder.name).join(', ');
	return route.state === 'unused' ? text.noTablet : text.printerOnly;
}

/** Halaman ini tidak berbaris; isinya keadaan stasiun satu cabang di `routes`. */
type NoRow = { id: string };

/** Tab Stasiun dan Printer di halaman detail cabang: semuanya dihitung dari tablet dan printer yang dilaporkan, tanpa setelan. */
export class PrintersState extends ManageState<NoRow> {
	override readonly tables = ['device_printers', 'device_stations', 'device_station_prints', 'devices', 'stations', 'category_stations', 'category_branch_stations', 'categories'];

	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: text.branchFilter, options: [] }]);

	routes = $state<StationRoute[] | null>(null);
	menuId = $state('');
	menuRoute = $state<MenuRoute | null>(null);
	menuProblem = $state('');
	menuLoading = $state(false);

	private menuToken = 0;

	get outletId(): string | null {
		const value = this.filters.get('cabang');
		return typeof value === 'string' ? value : null;
	}

	override get query(): string | null {
		return this.outletId;
	}

	/** Stasiun yang dipakai cabang ini dan sudah siap, dibanding semua yang dipakai. */
	get readiness(): { ready: number; used: number } {
		const used = (this.routes ?? []).filter((route) => route.state !== 'unused');
		return { ready: used.filter((route) => route.state === 'ready').length, used: used.length };
	}

	protected async fetch(): Promise<void> {
		const outletId = this.outletId;
		if (outletId === null) {
			this.routes = null;
			return;
		}
		const found = await api.printers.stations(outletId);
		if (this.outletId !== outletId) return;
		this.routes = found.stations;
		if (this.menuId) await this.preview(this.menuId);
	}

	protected label(): string {
		return this.outletId ?? '';
	}

	async preview(menuId: string): Promise<void> {
		const outletId = this.outletId;
		this.menuId = menuId;
		if (!outletId || !menuId) {
			this.menuRoute = null;
			return;
		}
		const token = ++this.menuToken;
		this.menuLoading = true;
		this.menuProblem = '';
		try {
			const found = await api.printers.menuRoute(outletId, menuId);
			if (token === this.menuToken) this.menuRoute = found;
		} catch (problem) {
			if (token === this.menuToken) this.menuProblem = userMessage(problem, text.previewFailed);
		} finally {
			if (token === this.menuToken) this.menuLoading = false;
		}
	}
}
