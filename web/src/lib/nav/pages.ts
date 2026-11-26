import { resolve } from '$app/paths';
import type { Screen } from '$lib/api/types';
import { termText } from '$lib/text/terms';

/** A screen of the web: its address, checked against the routes by svelte-check, its name, and the server screen whose gate opens it. */
export type Page = { path: string; label: string; screen: Screen };

export const CANCELLATIONS_TAB = 'cancellations';
export const USAGE_TAB = 'usage';
export const LEAVE_TAB = 'izin';
// Jangkar panel QC nontunai di Ringkasan Keuangan, tempat pemeriksaannya dikerjakan.
export const QC_ANCHOR = 'qc-nontunai';

const page = (path: string, label: string, screen: Screen): Page => ({ path, label, screen });

export const PAGES = {
	dashboard: page(resolve('/admin/dashboard'), 'Dashboard', 'dashboard'),
	issues: page(resolve('/admin/issues'), 'Laporan Masalah', 'issues'),
	financeOverview: page(resolve('/admin/reports/finance-overview'), 'Ringkasan Keuangan', 'finance_overview'),
	busySales: page(resolve('/admin/reports/sales-peak'), 'Penjualan', 'busy_sales'),
	busyProducts: page(resolve('/admin/reports/product-peak'), 'Produk', 'busy_products'),
	categoriesReport: page(resolve('/admin/reports/categories'), 'Kategori', 'categories_report'),
	optionsReport: page(resolve('/admin/reports/options'), 'Varian dan Ekstra', 'options_report'),
	promosReport: page(resolve('/admin/reports/promotions'), termText.promo, 'promos_report'),
	voidsReport: page(resolve('/admin/reports/voids'), 'Transaksi Batal', 'voids_report'),
	visitorsReport: page(resolve('/admin/reports/visitors'), 'Pengunjung', 'visitors_report'),
	ingredientStockReport: page(resolve('/admin/reports/ingredient-stock'), 'Stok Bahan', 'ingredient_stock_report'),
	stockTurnoverReport: page(resolve('/admin/reports/stock-turnover'), 'Perputaran Stok', 'stock_turnover_report'),
	attendanceReport: page(resolve('/admin/reports/attendance'), 'Kehadiran Karyawan', 'attendance_report'),
	margin: page(resolve('/admin/margin'), 'Margin per Menu', 'margin'),
	menu: page(resolve('/admin/menu'), 'Kelola Menu', 'menu'),
	menuCategories: page(resolve('/admin/menu-categories'), 'Kategori Menu', 'menu_categories'),
	options: page(resolve('/admin/options'), 'Varian dan Ekstra', 'options'),
	recipes: page(resolve('/admin/recipes'), 'Master Resep', 'recipes'),
	promotions: page(resolve('/admin/promotions'), 'Promosi', 'promotions'),
	orderNotes: page(resolve('/admin/order-notes'), 'Catatan Pesanan', 'order_notes'),
	stationMonitor: page(resolve('/admin/stations/monitor'), 'Pantauan', 'station_monitor'),
	stationPerformance: page(resolve('/admin/stations/performance'), 'Kinerja', 'station_performance'),
	stationTargets: page(resolve('/admin/stations/targets'), 'Target Waktu', 'station_targets'),
	stationSetup: page(resolve('/admin/stations/setup'), 'Pengaturan', 'station_setup'),
	ingredients: page(resolve('/admin/ingredients'), 'Daftar Bahan', 'ingredients'),
	ingredientReceipts: page(resolve('/admin/ingredients/receipts'), 'Barang Masuk', 'ingredient_receipts'),
	indirectIngredients: page(resolve('/admin/ingredients/indirect'), 'Bahan Tidak Langsung', 'indirect_ingredients'),
	indirectUsage: page(resolve(`/admin/ingredients/indirect?tab=${USAGE_TAB}`),'Pemakaian Bahan Tidak Langsung', 'indirect_ingredients'),
	ingredientWaste: page(resolve('/admin/ingredients/waste'), 'Rusak dan RnD', 'ingredient_waste'),
	ingredientCounts: page(resolve('/admin/ingredients/counts'), 'Stok Opname', 'ingredient_counts'),
	stockItems: page(resolve('/admin/stock-items'), 'Stok Barang Jual-Ulang', 'stock_items'),
	sessionHistory: page(resolve('/admin/session-history'), 'Riwayat Sesi Kasir', 'session_history'),
	moneyChanges: page(resolve('/admin/money-changes'), 'Jejak Perubahan Uang', 'money_changes'),
	cancellations: page(resolve(`/admin/session-history?tab=${CANCELLATIONS_TAB}`), 'Pengajuan Pembatalan', 'session_history'),
	overpayments: page(resolve('/admin/overpayments'), 'Kelebihan Pembayaran', 'overpayments'),
	expenses: page(resolve('/admin/expenses'), termText.expense, 'expenses'),
	mutations: page(resolve('/admin/mutations'), 'Mutasi', 'mutations'),
	paymentMethods: page(resolve('/admin/payment-methods'), termText.payment, 'payment_methods'),
	user: page(resolve('/admin/users'), 'Kelola Karyawan', 'users'),
	userPerformance: page(resolve('/admin/user-performance'), 'Kinerja Karyawan', 'users'),
	roles: page(resolve('/admin/roles'), 'Peran dan Izin', 'roles'),
	schedule: page(resolve('/admin/schedule'), 'Jadwal dan Kehadiran', 'schedule'),
	shiftCodes: page(resolve('/admin/shift-codes'), 'Kode Shift', 'shift_codes'),
	attendance: page(resolve('/admin/attendance'), 'Daftar Absensi', 'attendance'),
	leaveRequests: page(resolve(`/admin/attendance?tab=${LEAVE_TAB}`), 'Pengajuan Izin', 'attendance'),
	nonCashCheck: page(resolve(`/admin/reports/finance-overview#${QC_ANCHOR}`), 'QC Non-tunai', 'finance_overview'),
	sop: page(resolve('/admin/sop'), 'SOP Karyawan', 'sop'),
	tasks: page(resolve('/admin/tasks'), 'Tugas', 'tasks'),
	branches: page(resolve('/admin/branches'), termText.branch, 'branches'),
	cafeSettings: page(resolve('/admin/cafe-settings'), 'Pengaturan Struk', 'cafe_settings'),
	devices: page(resolve('/admin/devices'), 'Perangkat', 'devices'),
	printers: page(resolve('/admin/printers'), 'Stasiun dan Printer', 'printers'),
	attendanceRules: page(resolve('/admin/attendance-rules'), 'Aturan Absensi', 'attendance_rules')
} as const satisfies Record<string, Page>;

/** The page an address belongs to, the longest match winning; a detail page such as /admin/menu/{id} belongs to its list. */
export function pageAt(pathname: string): Page | undefined {
	let found: Page | undefined;
	for (const page of Object.values(PAGES)) {
		if (page.path.includes('?')) continue;
		const inside = pathname === page.path || pathname.startsWith(`${page.path}/`);
		if (inside && (!found || page.path.length > found.path.length)) found = page;
	}
	return found;
}

export const SIGN_IN_PATH = resolve('/login');
export const SOP_DRAFT_PARAM = 'draft';
export const NEW_SOP_PATH = resolve('/admin/sop/new');

export const employeePath = (id: string): string => resolve('/(app)/admin/users/[id]', { id });
export const userPerformancePath = (id: string): string => resolve('/(app)/admin/user-performance/[id]', { id });
export const cancellationPath = (id: string): string => resolve('/(app)/admin/session-history/cancellations/[id]', { id });
/** Tab halaman detail cabang; alamat lama halaman-halaman pengaturan cabang mengarah ke sini. */
export const BRANCH_TABS = { summary: 'summary', periods: 'periods', receipt: 'receipt', pricing: 'pricing', cashier: 'cashier', rules: 'rules', devices: 'devices', printers: 'printers' } as const;
export type BranchTab = (typeof BRANCH_TABS)[keyof typeof BRANCH_TABS];
export const branchPath = (id: string, tab?: BranchTab): string => {
	const path = resolve('/(app)/admin/branches/[id]', { id });
	return tab ? `${path}?${new URLSearchParams({ tab })}` : path;
};
export const branchPeriodPath = (outlet: string, start: string): string => resolve('/(app)/admin/branches/periods/[outlet]/[start]', { outlet, start });
export const stockItemPath = (id: string): string => resolve('/(app)/admin/stock-items/[id]', { id });
export const scheduleEntryPath = (id: string): string => resolve('/(app)/admin/schedule/[id]', { id });
export const stockItemCountPath = (): string => resolve('/(app)/admin/stock-items/count');
export const orderNotePath = (id: string): string => resolve('/(app)/admin/order-notes/[id]', { id });
export const paymentMethodPath = (id: string): string => resolve('/(app)/admin/payment-methods/[id]', { id });
export const taskPath = (id: string): string => resolve('/(app)/admin/tasks/[id]', { id });
export const TASK_SOURCE_PARAM = 'source';
/** A new task for an employee; with a filling it is the follow-up of that filling. */
export const taskNewPath = (sourceRunId?: string): string => {
	const base = resolve('/(app)/admin/tasks/new');
	return sourceRunId ? `${base}?${new URLSearchParams({ [TASK_SOURCE_PARAM]: sourceRunId })}` : base;
};
export const TASKS_TAB_PARAM = 'tab';
/** The tasks page opened on one of its tabs. */
export const tasksTabPath = (tab: string): string => `${resolve('/(app)/admin/tasks')}?${new URLSearchParams({ [TASKS_TAB_PARAM]: tab })}`;
export const batchRunPath = (id: string): string => resolve('/(app)/admin/tasks/runs/[id]', { id });
export const batchPath = (id: string): string => resolve('/(app)/admin/tasks/batches/[id]', { id });
export const ingredientCountPath = (id: string, partStart: string | null = null): string =>
	resolve('/(app)/admin/ingredients/counts/[id]', { id }) + (partStart ? `?part=${encodeURIComponent(partStart)}` : '');
export const ingredientCountRequestPath = (id: string): string => resolve('/(app)/admin/ingredients/counts/requests/[id]', { id });
export const rolePath = (id: string): string => resolve('/(app)/admin/roles/[id]', { id });
export const deviceNewPath = (): string => resolve('/(app)/admin/devices/new');
export const devicePath = (id: string): string => resolve('/(app)/admin/devices/[id]', { id });
export const paymentMethodNewPath = (): string => resolve('/(app)/admin/payment-methods/new');
export const shiftCodeNewPath = (): string => resolve('/(app)/admin/shift-codes/new');
export const shiftCodeBulkPath = (): string => resolve('/(app)/admin/shift-codes/bulk');
export const BATCH_KIND_PARAM = 'kind';
export const batchNewPath = (kind: 'outlet' | 'routine' = 'outlet'): string => `${resolve('/(app)/admin/tasks/batches/new')}?${new URLSearchParams({ [BATCH_KIND_PARAM]: kind })}`;
export const roleNewPath = (): string => resolve('/(app)/admin/roles/new');
export const roleBulkPath = (): string => resolve('/(app)/admin/roles/bulk');
export const expenseBulkPath = (): string => resolve('/(app)/admin/expenses/bulk');
export const EXPENSE_SESSION_PARAM = 'session';
/** A new expense, bound to a session when it is added from that session's page. */
export const expenseNewPath = (sessionId?: string): string => {
	const base = resolve('/(app)/admin/expenses/new');
	return sessionId ? `${base}?${new URLSearchParams({ [EXPENSE_SESSION_PARAM]: sessionId })}` : base;
};
export const expenseEditPath = (id: string): string => resolve('/(app)/admin/expenses/[id]/edit', { id });
export const promoNewPath = (): string => resolve('/(app)/admin/promotions/discounts/new');
export const announcementNewPath = (): string => resolve('/(app)/admin/promotions/announcements/new');
export const branchNewPath = (): string => resolve('/(app)/admin/branches/new');
export const employeeNewPath = (): string => resolve('/(app)/admin/users/new');
export const employeeBulkPath = (): string => resolve('/(app)/admin/users/bulk');
export const menuNewPath =(): string => resolve('/(app)/admin/menu/new');
export const menuBulkPath = (): string => resolve('/(app)/admin/menu/bulk');
/** Halaman bahan baru menyalakan centang tidak langsung bila dibuka dari daftar bahan tidak langsung. */
export const INDIRECT_PARAM = 'indirect';
export const ingredientNewPath = (indirect = false): string => resolve('/(app)/admin/ingredients/new') + (indirect ? `?${INDIRECT_PARAM}=1` : '');
export const ingredientBulkPath = (): string => resolve('/(app)/admin/ingredients/bulk');
export const ingredientPath = (id: string): string => resolve('/(app)/admin/ingredients/[id]', { id });
export const promoPath = (id: string): string => resolve('/(app)/admin/promotions/discounts/[id]', { id });
export const announcementPath = (id: string): string => resolve('/(app)/admin/promotions/announcements/[id]', { id });
export const variantGroupPath = (id: string): string => resolve('/(app)/admin/options/variant-groups/[id]', { id });
export const variantGroupNewPath = (): string => resolve('/(app)/admin/options/variant-groups/new');
export const extraNewPath = (): string => resolve('/(app)/admin/options/extras/new');
export const extraPath = (id: string): string => resolve('/(app)/admin/options/extras/[id]', { id });
export const menuPath = (id: string): string => resolve('/(app)/admin/menu/[id]', { id });
export const orderPath = (sessionId: string, orderId: string): string => resolve('/(app)/admin/session-history/[id]/orders/[orderId]', { id: sessionId, orderId });
export const mutationPath = (sessionId: string): string => resolve('/(app)/admin/mutations/[id]', { id: sessionId });
export const assignmentPath = (id: string): string => resolve('/(app)/admin/schedule/[id]', { id });
export const assignmentNewPath = (date?: string, userId?: string): string => {
	const base = resolve('/(app)/admin/schedule/new');
	const query = new URLSearchParams();
	if (date) query.set('tanggal', date);
	if (userId) query.set('karyawan', userId);
	return query.size > 0 ? `${base}?${query}` : base;
};
export const scheduleBulkPath = (): string => resolve('/(app)/admin/schedule/bulk');
export const sessionPath = (id: string): string => resolve('/(app)/admin/session-history/[id]', { id });
export const attendancePath = (id: string): string => resolve('/(app)/admin/attendance/[id]', { id });
export const expensePath = (id: string): string => resolve('/(app)/admin/expenses/[id]', { id });
export const receiptNewPath = (): string => resolve('/(app)/admin/ingredients/receipts/new');
export const receiptBulkPath = (): string => resolve('/(app)/admin/ingredients/receipts/bulk');
export const receiptPath = (id: string): string => resolve('/(app)/admin/ingredients/receipts/[id]', { id });
export const lossNewPath = (kind: string): string => `${resolve('/(app)/admin/ingredients/waste/new')}?${new URLSearchParams({ jenis: kind })}`;
export const lossBulkPath = (): string => resolve('/(app)/admin/ingredients/waste/bulk');
export const lossPath = (id: string): string => resolve('/(app)/admin/ingredients/waste/[id]', { id });
export const usageNewPath = (): string => resolve('/(app)/admin/ingredients/indirect/usage/new');
export const usagePath = (id: string): string => resolve('/(app)/admin/ingredients/indirect/usage/[id]', { id });
export const shiftCodePath = (id: string): string => resolve('/(app)/admin/shift-codes/[id]', { id });
export const recipePath = (key: string): string => resolve('/(app)/admin/recipes/[id]', { id: key });
export const recipeEditPath = (key: string): string => resolve('/(app)/admin/recipes/[id]/edit', { id: key });
export const sopReadersPath = (id: string): string => resolve('/(app)/admin/sop/[id]/readers', { id });
export const sopEditPath = (id: string): string => resolve('/(app)/admin/sop/[id]/edit', { id });
export const stationPath = (id: string): string => resolve('/(app)/admin/stations/setup/[id]', { id });
export const NEW_STATION_PATH = stationPath('new');
export const menuTargetPath = (id: string): string => resolve('/(app)/admin/stations/targets/[id]', { id });
export const stationTaskPath = (id: string): string => resolve('/(app)/admin/stations/monitor/[id]', { id });
export const sopDraftPath = (draftId: string): string => `${NEW_SOP_PATH}?${new URLSearchParams({ [SOP_DRAFT_PARAM]: draftId })}`;
