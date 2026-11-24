import { brand } from '$lib/text/brand';
import { resolve } from '$app/paths';
import brandLogo from '$lib/assets/logo/brand-logo.png';
import type { NavEntry, NavLeaf, SidebarBrand, SidebarProfile } from '$lib/components/sidebar/types';
import { PAGES, type Page } from './pages';
import { termText } from '$lib/text/terms';

const leaf = (page: Page): NavLeaf => ({ href: page.path, label: page.label, screen: page.screen });

export const webBrand: SidebarBrand = {
	logo: brandLogo,
	logoAlt: `Logo ${brand.name}`,
	title: 'Admin',
	subtitle: brand.name
};

export const webProfile: SidebarProfile = {
	href: resolve('/profile'),
	label: 'Profil',
	icon: 'ti-user-circle'
};

export const webNav: NavEntry[] = [
	{ ...leaf(PAGES.dashboard), icon: 'ti-chart-bar' },
	{ ...leaf(PAGES.issues), icon: 'ti-alert-triangle' },
	{
		key: 'laporan',
		label: 'Laporan',
		icon: 'ti-report-analytics',
		items: [
			leaf(PAGES.financeOverview),
			leaf(PAGES.busySales),
			leaf(PAGES.busyProducts),
			leaf(PAGES.categoriesReport),
			leaf(PAGES.optionsReport),
			leaf(PAGES.promosReport),
			leaf(PAGES.voidsReport),
			leaf(PAGES.visitorsReport),
			leaf(PAGES.ingredientStockReport),
			leaf(PAGES.stockTurnoverReport),
			leaf(PAGES.attendanceReport),
			leaf(PAGES.margin)
		]
	},
	{
		key: 'produk',
		label: 'Produk',
		icon: 'ti-tag',
		items: [
			leaf(PAGES.menu),
			leaf(PAGES.menuCategories),
			leaf(PAGES.options),
			leaf(PAGES.recipes),
			leaf(PAGES.promotions),
			leaf(PAGES.orderNotes)
		]
	},
	{
		key: 'stasiun',
		label: termText.station,
		icon: 'ti-tools-kitchen-2',
		items: [leaf(PAGES.stationMonitor), leaf(PAGES.stationPerformance), leaf(PAGES.stationTargets), leaf(PAGES.stationSetup)]
	},
	{
		key: 'inventori',
		label: 'Inventori',
		icon: 'ti-box',
		items: [
			leaf(PAGES.ingredients),
			leaf(PAGES.indirectIngredients),
			leaf(PAGES.ingredientReceipts),
			leaf(PAGES.ingredientWaste),
			leaf(PAGES.ingredientCounts),
			leaf(PAGES.stockItems)
		]
	},
	{
		key: 'keuangan',
		label: 'Keuangan',
		icon: 'ti-cash',
		items: [
			leaf(PAGES.sessionHistory),
			{ ...leaf(PAGES.cancellations), area: 'decide_cancellations' },
			leaf(PAGES.moneyChanges),
			leaf(PAGES.overpayments),
			leaf(PAGES.expenses),
			leaf(PAGES.mutations),
			leaf(PAGES.paymentMethods)
		]
	},
	{
		key: 'karyawan',
		label: termText.employee,
		icon: 'ti-users',
		items: [
			leaf(PAGES.user),
			leaf(PAGES.userPerformance),
			leaf(PAGES.roles),
			leaf(PAGES.schedule),
			leaf(PAGES.shiftCodes),
			leaf(PAGES.attendance),
			leaf(PAGES.sop),
			leaf(PAGES.tasks)
		]
	},
	{
		key: 'pengaturan',
		label: 'Pengaturan',
		icon: 'ti-settings',
		items: [
			leaf(PAGES.branches)
		]
	}
];
