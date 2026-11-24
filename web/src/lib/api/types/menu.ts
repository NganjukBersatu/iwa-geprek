import type { Schemas } from '../contract';

export type MenuItem = Schemas['MenuItemOut'];
export type MenuPage = Schemas['MenuItemPageOut'];
export type MenuCreate = Schemas['MenuCreateIn'];
export type MenuUpdate = Schemas['MenuUpdateIn'];
export type FixedCost = Schemas['FixedCostOut'];
export type FixedCostUpdate = Schemas['FixedCostIn'];
export type MenuCategory = Schemas['MenuCategoryOut'];
/** A category as its own screen shows it: with the menus filed under it and the station that makes it. */
export type MenuCategoryRecord = Schemas['MenuCategoryRecordOut'];
export type MenuCategoryCreate = Schemas['MenuCategoryCreateIn'];
export type MenuCategoryUpdate = Schemas['MenuCategoryUpdateIn'];
