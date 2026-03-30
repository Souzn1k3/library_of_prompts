import { ruCore } from "./ru/core";
import { ruHome } from "./ru/home";
import { ruAccount } from "./ru/account";
import { ruCatalog } from "./ru/catalog";
import { ruMissions } from "./ru/missions";
import { ruEconomy } from "./ru/economy";

export const ru = {
  ...ruCore,
  ...ruHome,
  ...ruAccount,
  ...ruCatalog,
  ...ruMissions,
  ...ruEconomy,
} as const;
