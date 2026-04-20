/**
 * eli-utils.ts
 * Utilities for converting ELI strings to URL paths and data file paths.
 *
 * ELI format:  "/eli/sluzbeni/1990/10/125"
 * Page URL:    "/documents/eli/sluzbeni/1990/10/125/"
 * Data URL:    "/data/eli/sluzbeni/1990/10/125.json"
 * Params arr:  ["eli", "sluzbeni", "1990", "10", "125"]
 */

/** "/eli/sluzbeni/1990/10/125" → "/documents/eli/sluzbeni/1990/10/125" */
export function eliToPagePath(eli: string): string {
  return `/documents${eli}`;
}

/** "/eli/sluzbeni/1990/10/125" → "/data/eli/sluzbeni/1990/10/125.json" */
export function eliToDataUrl(eli: string): string {
  return `/data${eli}.json`;
}

/** ["eli","sluzbeni","1990","10","125"] → "/eli/sluzbeni/1990/10/125" */
export function paramsToEli(params: string[]): string {
  return '/' + params.join('/');
}
