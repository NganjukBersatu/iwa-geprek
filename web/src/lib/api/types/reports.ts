import type { Schemas } from '../contract';

export type Period = Schemas['Period'];
export type ComparisonMode = Schemas['ComparisonMode'];

export type Summary = Schemas['SalesSummaryOut'];
export type Trend = Schemas['TrendOut'];
export type TrendWindow = Schemas['WindowOut'];
export type TrendPoint = Schemas['TrendPointOut'];
export type Comparison = Schemas['ComparisonOut'];
export type ComparisonMetric = Schemas['MetricOut'];
export type CashierReport = Schemas['CashierReportOut'];
export type CashierRow = Schemas['CashierRowOut'];
export type ProfitLoss = Schemas['ProfitLossOut'];
export type InventoryValue = Schemas['InventoryValueOut'];

export type DailyOverview = Schemas['DailyOverviewOut'];
export type DailyRow = Schemas['DailyRowOut'];
export type DailyTotals = Schemas['DailyTotalsOut'];
export type TransactionReport = Schemas['TransactionsOut'];
export type TransactionRow = Schemas['TransactionOut'];
export type PaymentGroup = TransactionReport['group'];

export type BusySales = Schemas['BusySalesOut'];
export type BusySalesRow = Schemas['BusySalesRowOut'];
export type BusyProducts = Schemas['BusyProductsOut'];
export type BusyProductRow = Schemas['BusyProductRowOut'];
export type Highlight = Schemas['HighlightOut'];

export type CategoryReport = Schemas['CategoriesOut'];
export type CategorySales = Schemas['CategorySalesOut'];
export type UnsoldMenu = Schemas['UnsoldMenuOut'];
export type MenuSales = Schemas['MenuSalesOut'];

export type SalesBreakdown = Schemas['SalesBreakdownOut'];
export type BreakdownRow = Schemas['BreakdownRowOut'];
export type VariantReport = Schemas['VariantsOut'];
export type VariantRow = Schemas['VariantRowOut'];
export type ExtraReport = Schemas['ExtrasOut'];
export type ExtraRow = Schemas['ExtraRowOut'];
export type PromoReport = Schemas['PromosOut'];
export type PromoUsage = Schemas['PromoUsageOut'];
export type MarginReport = Schemas['MarginOut'];
export type MarginItem = Schemas['MenuMarginOut'];

export type KitchenReport = Schemas['KitchenOut'];
export type KitchenHour = Schemas['KitchenHourOut'];
export type KitchenOrder = Schemas['KitchenOrderOut'];
export type VoidReport = Schemas['VoidsOut'];
export type VoidedOrder = Schemas['VoidedOrderOut'];
export type OverpaymentReport = Schemas['OverpaymentsOut'];
export type Overpayment = Schemas['OverpaymentOut'];

export type StockReport = Schemas['IngredientStockOut'];
export type StockRow = Schemas['IngredientStockRowOut'];
export type ReplacementStatus = StockRow['replacement_status'];
export type TurnoverReport = Schemas['TurnoverOut'];
export type TurnoverRow = Schemas['TurnoverRowOut'];
export type TurnoverStatus = TurnoverRow['status'];

export type VisitorBreakdown = Schemas['VisitorBreakdownOut'];
export type VisitorGroup = Schemas['VisitorGroupOut'];
export type VisitorDay = Schemas['VisitorDayOut'];

export type AttendanceRecap = Schemas['AttendanceRecapOut'];
export type UserRecap = Schemas['UserRecapOut'];
export type RecapDay = Schemas['RecapDayOut'];
export type RecapOvertime = Schemas['RecapOvertimeOut'];
export type AttendanceStatus = RecapDay['status'];
