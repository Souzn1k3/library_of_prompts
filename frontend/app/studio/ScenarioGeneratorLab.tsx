"use client";

/**
 * Compatibility shim for hot-reload sessions after Studio refactors.
 * The feature moved to the new scenario-runtime surface, but keeping this
 * module avoids transient webpack module-resolution crashes during HMR.
 */
export function ScenarioGeneratorLab() {
  return null;
}
