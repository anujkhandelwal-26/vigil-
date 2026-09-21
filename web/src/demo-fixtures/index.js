/**
 * ⚠ DEMO-ONLY DATA SOURCE — not part of VIGIL's decisioning path.
 *
 * Randomly samples real rows out of the synthetic training dataset (see
 * build_samples.py in this directory, which produced samples.json from
 * data/generated/applications.csv and new_vector_injection.csv) so the
 * Apply dashboard's scenario picker hands back a fresh, genuinely varied
 * application every time a scenario is chosen or the page is reloaded,
 * instead of replaying one hardcoded template verbatim on every click.
 *
 * This exists purely to make the interactive demo more convincing and to
 * stop every "clean" test submission from clustering into a false fraud
 * ring (they were all near-identical before this existed). Nothing in
 * this directory should be imported by anything other than
 * src/data/scenarios.js.
 */
import samples from './samples.json'

export function randomSample(typologyKey) {
  const bucket = samples[typologyKey]
  if (!bucket || bucket.length === 0) {
    throw new Error(`demo-fixtures: no samples for typology "${typologyKey}" — re-run build_samples.py`)
  }
  return { ...bucket[Math.floor(Math.random() * bucket.length)] }
}
