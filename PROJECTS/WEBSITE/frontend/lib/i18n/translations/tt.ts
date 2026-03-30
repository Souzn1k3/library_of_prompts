import { ttCore } from "./tt/core";
import { ttHome } from "./tt/home";
import { ttAccount } from "./tt/account";
import { ttCatalog } from "./tt/catalog";
import { ttMissions } from "./tt/missions";
import { ttEconomy } from "./tt/economy";

export const tt = {
  ...ttCore,
  ...ttHome,
  ...ttAccount,
  ...ttCatalog,
  ...ttMissions,
  ...ttEconomy,
} as const;
