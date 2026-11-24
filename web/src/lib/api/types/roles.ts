import type { Schemas } from '../contract';

export type Role = Schemas['RoleOut'];
export type RoleCreate = Omit<Schemas['RoleCreateIn'], 'sort_order'> & { sort_order?: number };
export type RoleUpdate = Schemas['RoleUpdateIn'];
export type Permission = Schemas['PermissionOut'];
export type RoleStation = Schemas['RoleStationOut'];
