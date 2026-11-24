import { request, toQuery, type SortParam } from './http';
import type {
	AttendanceRecap,
	BusyProducts,
	BusySales,
	CashierReport,
	CategoryReport,
	Comparison,
	ComparisonMode,
	DailyOverview,
	ExtraReport,
	InventoryValue,
	KitchenReport,
	MarginReport,
	OverpaymentReport,
	PaymentGroup,
	Period,
	ProfitLoss,
	PromoReport,
	SalesBreakdown,
	StockReport,
	Summary,
	TransactionReport,
	Trend,
	TrendWindow,
	TurnoverReport,
	VariantReport,
	VisitorBreakdown,
	VoidReport
} from './types';

const BASE = '/web/management/reports';

export type DateParams = SortParam & { start?: string; end?: string };
export type TimeUnit = 'hour' | 'weekday' | 'date' | 'month';
export type ProductSort = 'qty' | 'revenue' | 'time';

export type TrendParams = DateParams & { period?: Period; count?: number };
export type ComparisonParams = DateParams & { mode?: ComparisonMode; previous_start?: string; previous_end?: string };
export type TransactionParams = DateParams & { group?: PaymentGroup; method?: string; include_voided?: boolean; page?: number; per_page?: number };
export type BusySalesParams = DateParams & { unit: TimeUnit; hour?: number };
export type BusyProductsParams = BusySalesParams & { search?: string; sort: ProductSort; series: number; page: number; per_page: number };
export type KitchenParams = DateParams & { threshold_minutes: number; hour_sort?: string; order_sort?: string };
export type VoidParams = DateParams & { page: number; per_page: number };
export type OverpaymentParams = DateParams & { page: number; per_page: number };
export type TurnoverParams = DateParams & { target_days: number };

const get = <T>(path: string, params: object = {}): Promise<T> => request<T>(`${BASE}${path}?${toQuery(params as Record<string, string | number | boolean | undefined>)}`);

export const reportsApi = {
	summary: (range: DateParams): Promise<Summary> => get('/summary', range),
	trend: (params: TrendParams = {}): Promise<Trend> => get('/trend', params),
	window: (params: TrendParams = {}): Promise<TrendWindow> => get('/trend/window', params),
	comparison: (params: ComparisonParams): Promise<Comparison> => get('/comparison', params),
	cashiers: (range: DateParams): Promise<CashierReport> => get('/cashiers', range),
	profitLoss: (range: DateParams): Promise<ProfitLoss> => get('/profit-loss', range),
	inventoryValue: (): Promise<InventoryValue> => get('/inventory-value'),
	dailyOverview: (range: DateParams): Promise<DailyOverview> => get('/daily-overview', range),
	transactions: (params: TransactionParams): Promise<TransactionReport> => get('/transactions', params),
	busySales: (params: BusySalesParams): Promise<BusySales> => get('/busy-sales', params),
	busyProducts: (params: BusyProductsParams): Promise<BusyProducts> => get('/busy-products', params),
	categories: (params: DateParams & { unsold_sort?: string; menu_sort?: string }): Promise<CategoryReport> => get('/categories', params),
	salesBreakdown: (params: DateParams & { type_sort?: string; outlet_sort?: string }): Promise<SalesBreakdown> => get('/sales-breakdown', params),
	variants: (params: DateParams & { by_menu: boolean }): Promise<VariantReport> => get('/variants', params),
	extras: (params: DateParams): Promise<ExtraReport> => get('/extras', params),
	promos: (range: DateParams): Promise<PromoReport> => get('/promos', range),
	margin: (range: DateParams): Promise<MarginReport> => get('/margin', range),
	kitchen: (params: KitchenParams): Promise<KitchenReport> => get('/kitchen', params),
	voids: (params: VoidParams): Promise<VoidReport> => get('/voids', params),
	overpayments: (params: OverpaymentParams): Promise<OverpaymentReport> => get('/overpayments', params),
	ingredientStock: (range: DateParams): Promise<StockReport> => get('/ingredient-stock', range),
	visitors: (params: DateParams & { gender_sort?: string; category_sort?: string }): Promise<VisitorBreakdown> => get('/visitors', params),
	attendance: (params: DateParams & { day_sort?: string; overtime_sort?: string }): Promise<AttendanceRecap> => get('/attendance', params),
	stockTurnover: (params: TurnoverParams): Promise<TurnoverReport> => get('/stock-turnover', params)
};
