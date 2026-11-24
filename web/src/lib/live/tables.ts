/** Tables a screen shows, by name as the server publishes them; pages pick the groups they depend on. */
export const SALES_TABLES = ['orders', 'order_items', 'order_item_options', 'cash_sessions', 'expenses', 'overpayments'];
export const SESSION_TABLES = ['cash_sessions', 'orders', 'expenses', 'overpayments'];
export const EXPENSE_TABLES = ['expenses', 'cash_sessions'];
export const STOCK_TABLES = ['stock_items', 'stock_cards', 'ingredients', 'ingredient_cards'];
export const MENU_TABLES = ['menu_items', 'menu_outlet_prices', 'recipe_ingredients', 'recipe_add_costs'];
export const STATION_TABLES = ['station_tasks', 'orders', 'cash_sessions', 'stations', 'station_flows', 'station_branch_settings', 'cancellation_requests'];
export const TASK_TABLES = ['tasks', 'outlet_tasks', 'task_attachments'];
// Attendance, schedule, overtime, and tasks that change also change the figures of user performance.
export const PERFORMANCE_TABLES = ['attendance_records', 'schedules', 'overtime_records', 'tasks', 'users'];
// Every table a Laporan Masalah detector reads; a detector that starts reading another table adds it here.
export const ISSUE_TABLES = [
	...new Set([
		...SALES_TABLES,
		...STOCK_TABLES,
		'deposits',
		'deposit_days',
		'non_cash_checks',
		'cancellation_requests',
		'station_tasks',
		'station_flows',
		'ingredient_counts',
		'ingredient_count_lines',
		'ingredient_count_requests',
		'recipe_ingredients',
		'variant_choice_recipes',
		'extra_recipes',
		'recipe_add_costs',
		'menu_items',
		'menu_outlet_prices',
		'cafe_settings',
		'promos',
		'cafe_promotions',
		'leave_requests',
		'schedules',
		'day_offs',
		'attendance_records',
		'overtime_records',
		'users',
		'roles',
		'outlets',
		'outlet_batches',
		'outlet_batch_runs',
		'devices'
	])
];
