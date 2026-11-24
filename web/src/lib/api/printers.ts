import { request, toQuery } from './http';
import type { MenuRoute, StationRoutes } from './types';

const BASE = '/web/management/printers';

const outletPath = (outletId: string): string => `${BASE}/${encodeURIComponent(outletId)}`;

export const printersApi = {
	stations: (outletId: string): Promise<StationRoutes> => request(outletPath(outletId)),
	menuRoute: (outletId: string, menuId: string): Promise<MenuRoute> => request(`${outletPath(outletId)}/menu-route?${toQuery({ menu_id: menuId })}`)
};
