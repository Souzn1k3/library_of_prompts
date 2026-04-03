import { enCore } from "./en/core";
import { enHome } from "./en/home";
import { enAccount } from "./en/account";
import { enCatalog } from "./en/catalog";
import { enMissions } from "./en/missions";
import { enEconomy } from "./en/economy";

export const en = {
  ...enCore,
  ...enHome,
  ...enAccount,
  ...enCatalog,
  ...enMissions,
  ...enEconomy,
} as const;
