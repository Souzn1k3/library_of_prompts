import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";

const rootDir = process.cwd();
const standaloneDir = join(rootDir, ".next", "standalone");
const standaloneNextDir = join(standaloneDir, ".next");

function copyIntoStandalone(source, destination, label) {
  if (!existsSync(source)) {
    console.warn(`[prepare-standalone] Skipping ${label}: ${source} not found`);
    return;
  }

  rmSync(destination, { force: true, recursive: true });
  mkdirSync(dirname(destination), { recursive: true });
  cpSync(source, destination, { recursive: true });
  console.log(`[prepare-standalone] Copied ${label} to ${destination}`);
}

if (!existsSync(standaloneDir)) {
  throw new Error("Standalone output not found. Run `next build` before preparing standalone assets.");
}

mkdirSync(standaloneNextDir, { recursive: true });

copyIntoStandalone(join(rootDir, ".next", "static"), join(standaloneNextDir, "static"), "static assets");
copyIntoStandalone(join(rootDir, "public"), join(standaloneDir, "public"), "public assets");
