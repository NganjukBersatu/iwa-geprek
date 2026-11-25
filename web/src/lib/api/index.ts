import { attendanceApi } from './attendance';
import { attendanceRulesApi } from './attendanceRules';
import { cafeSettingsApi } from './cafeSettings';
import { depositsApi } from './deposits';
import { devicesApi } from './devices';
import { ingredientCountsApi } from './ingredientCounts';
import { ingredientCountRequestsApi } from './ingredientCountRequests';
import { printersApi } from './printers';
import { stockItemsApi } from './stockItems';
import { ingredientMovementsApi } from './ingredientMovements';
import { ingredientsApi } from './ingredients';
import { issuesApi } from './issues';
import { authApi } from './auth';
import { demoApi } from './demo';
import { batchesApi } from './batches';
import { branchesApi } from './branches';
import { employeesApi } from './employees';
import { expensesApi } from './expenses';
import { exportsApi } from './exports';
import { leaveRequestsApi } from './leaveRequests';
import { cancellationsApi } from './cancellations';
import { menuApi } from './menu';
import { menuCategoriesApi } from './menuCategories';
import { mutationsApi } from './mutations';
import { optionsApi } from './options';
import { moneyChangesApi } from './moneyChanges';
import { orderNotesApi } from './orderNotes';
import { promotionsApi } from './promotions';
import { outletsApi } from './outlets';
import { paymentMethodsApi } from './paymentMethods';
import { profileApi } from './profile';
import { qcApi } from './qc';
import { recipesApi } from './recipes';
import { releasesApi } from './releases';
import { reportsApi } from './reports';
import { rolesApi } from './roles';
import { scheduleApi } from './schedule';
import { screensApi } from './screens';
import { sessionsApi } from './sessions';
import { shiftCodesApi } from './shiftCodes';
import { sopApi } from './sop';
import { userPerformanceApi } from './userPerformance';
import { stationsApi } from './stations';
import { tasksApi } from './tasks';

export { ApiError } from './http';

export const api = {
	attendance: attendanceApi,
	attendanceRules: attendanceRulesApi,
	cafeSettings: cafeSettingsApi,
	devices: devicesApi,
	ingredients: ingredientsApi,
	issues: issuesApi,
	ingredientMovements: ingredientMovementsApi,
	deposits: depositsApi,
	exports: exportsApi,
	ingredientCounts: ingredientCountsApi,
	ingredientCountRequests: ingredientCountRequestsApi,
	printers: printersApi,
	stockItems: stockItemsApi,
	auth: authApi,
	demo: demoApi,
	batches: batchesApi,
	branches: branchesApi,
	employees: employeesApi,
	expenses: expensesApi,
	leaveRequests: leaveRequestsApi,
	cancellations: cancellationsApi,
	stations: stationsApi,
	menu: menuApi,
	menuCategories: menuCategoriesApi,
	mutations: mutationsApi,
	options: optionsApi,
	moneyChanges: moneyChangesApi,
	orderNotes: orderNotesApi,
	promotions: promotionsApi,
	outlets: outletsApi,
	paymentMethods: paymentMethodsApi,
	profile: profileApi,
	qc: qcApi,
	recipes: recipesApi,
	releases: releasesApi,
	reports: reportsApi,
	roles: rolesApi,
	schedule: scheduleApi,
	screens: screensApi,
	sessions: sessionsApi,
	shiftCodes: shiftCodesApi,
	sop: sopApi,
	userPerformance: userPerformanceApi,
	tasks: tasksApi
};
