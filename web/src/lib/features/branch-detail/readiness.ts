import type { BranchReadiness } from '$lib/api/types';
import { ROUTE_LOOKS } from '$lib/features/printers/printers.svelte';
import { BRANCH_TABS, PAGES, branchPath, type Page } from '$lib/nav/pages';
import { branchDetailText } from '$lib/text/branch-detail';
import { format } from '$lib/text/format';

export type ReadinessTone = 'success' | 'warning' | 'danger';
/** A link that leads to the screen where the missing part is filled in. */
export type ReadinessFix = { label: string; href: string; screen: Page['screen'] };
export type ReadinessItem = { key: string; title: string; detail: string; tone: ReadinessTone; fixes: ReadinessFix[] };
/** Required items decide whether the branch can sell; optional ones only make the setup complete. */
export type ReadinessList = { required: ReadinessItem[]; optional: ReadinessItem[] };

const text = branchDetailText.readiness;

const pageFix = (page: Page): ReadinessFix => ({ label: page.label, href: page.path, screen: page.screen });
const tabFix = (label: string, branchId: string, tab: keyof typeof BRANCH_TABS): ReadinessFix => ({ label, href: branchPath(branchId, BRANCH_TABS[tab]), screen: PAGES.branches.screen });

function menuItem(data: BranchReadiness): ReadinessItem {
	const base = { key: 'menu', title: text.menuTitle };
	if (data.menu_count === 0) return { ...base, detail: text.menuNone, tone: 'warning', fixes: [pageFix(PAGES.menuCategories), pageFix(PAGES.menu)] };
	if (data.unpriced_menu_count > 0) {
		const names = data.unpriced_menu_names.join(', ') + (data.unpriced_menu_count > data.unpriced_menu_names.length ? ', …' : '');
		return { ...base, detail: format(text.menuUnpriced, { count: data.unpriced_menu_count, names }), tone: 'warning', fixes: [pageFix(PAGES.recipes)] };
	}
	return { ...base, detail: format(text.menuReady, { count: data.menu_count }), tone: 'success', fixes: [] };
}

function paymentItem(data: BranchReadiness): ReadinessItem {
	const base = { key: 'payment', title: text.paymentTitle };
	if (data.open_payment_labels.length === 0) return { ...base, detail: text.paymentNone, tone: 'warning', fixes: [pageFix(PAGES.paymentMethods)] };
	return { ...base, detail: format(text.paymentReady, { labels: data.open_payment_labels.join(', ') }), tone: 'success', fixes: [] };
}

function staffItem(data: BranchReadiness): ReadinessItem {
	const base = { key: 'staff', title: text.staffTitle };
	if (data.cashier_staff_count === 0) return { ...base, detail: text.staffNone, tone: 'warning', fixes: [pageFix(PAGES.roles), pageFix(PAGES.user)] };
	return { ...base, detail: format(text.staffReady, { count: data.cashier_staff_count }), tone: 'success', fixes: [] };
}

function cashierItem(data: BranchReadiness, branchId: string): ReadinessItem {
	const ready = data.cashier_name !== null;
	return {
		key: 'cashier',
		title: text.cashierTitle,
		detail: data.cashier_name ?? text.cashierMissing,
		tone: ready ? 'success' : 'warning',
		fixes: ready ? [] : [tabFix(text.devicesLink, branchId, 'devices')]
	};
}

function stationItems(data: BranchReadiness, branchId: string): ReadinessItem[] {
	return data.stations
		.filter((route) => route.kind === 'make' && route.state !== 'unused')
		.map((route) => {
			const look = ROUTE_LOOKS[route.state];
			const holder = route.holders.at(0);
			const sender = route.sender?.name ?? text.cashierTablet;
			const where = holder ? format(text.stationReady, { holder: holder.name }) : format(text.stationNoTablet, { station: route.station_name, sender });
			const ready = route.state === 'ready';
			return {
				key: route.station_id,
				title: format(text.stationTitle, { name: route.station_name }),
				detail: ready ? where : format(text.stationFix, { look: look.label, sender }),
				tone: ready ? 'success' : route.state === 'printer_disconnected' ? 'danger' : 'warning',
				fixes: ready ? [] : [tabFix(text.stationsLink, branchId, 'printers')]
			};
		});
}

/** The checklist in setup order, built from one readiness answer; the same list feeds the branch page and the dashboard guide. */
export function readinessList(data: BranchReadiness, branchId: string): ReadinessList {
	const incomplete: ReadinessItem[] = data.incomplete_payment_labels.length
		? [{ key: 'payment-incomplete', title: text.paymentIncompleteTitle, detail: format(text.paymentIncomplete, { labels: data.incomplete_payment_labels.join(', ') }), tone: 'warning', fixes: [pageFix(PAGES.paymentMethods)] }]
		: [];
	return {
		required: [menuItem(data), paymentItem(data), staffItem(data), cashierItem(data, branchId)],
		optional: [
			...incomplete,
			...stationItems(data, branchId),
			{
				key: 'receipt',
				title: text.receiptTitle,
				detail: data.settings_ready ? text.receiptReady : text.receiptMissing,
				tone: data.settings_ready ? 'success' : 'warning',
				fixes: data.settings_ready ? [] : [tabFix(text.receiptLink, branchId, 'receipt')]
			},
			{
				key: 'location',
				title: text.locationTitle,
				detail: data.location_ready ? text.locationReady : text.locationMissing,
				tone: data.location_ready ? 'success' : 'warning',
				fixes: data.location_ready ? [] : [tabFix(text.locationTitle, branchId, 'summary')]
			}
		]
	};
}

/** A branch can sell once every required item is done, whatever the optional ones say. */
export const canSell = (list: ReadinessList): boolean => list.required.every((item) => item.tone === 'success');
