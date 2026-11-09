# ASSERT architecture and acceptance evidence

## Current status - 2026-11-09

**Three-model infrastructure, native connections and 14-case comparison passed.**
After the user freed GPT-5.4 quota (100 used / 250 limit), live catalog validation
confirmed the exact GA version 2026-03-05, GlobalStandard capacity 10. The user
explicitly approved restoring `assert-intermediate` through the existing Bicep
and evaluating only that target. The account/project/auth/network settings and
older/newer identities were preserved; metadata now contains three real models
and no skip. The original two completed runs and all frozen suite inputs stayed
byte-identical. `newer` remains generator/tester/judge for comparable results.
Live second-policy/replacement exercises and destructive cleanup remain not run.

## Original M1 authorization - 2026-11-05 (historical)

**Two-model live connection verification passed. Full M1 remains incomplete.**
The user explicitly approved two-model verification with GPT-5.4 pending, then
approved the investigated Entra authentication change. The user subsequently
authorized M2 with the two deployed targets and `newer` generation/tester/judge,
including bounded paid evaluation. Original third-model acceptance is deferred.

## M2 implementation and generation evidence

- Editable policy/settings, native stage configs/CLI, review/merge/approval,
  saved-result metrics/evidence and descriptive comparisons are implemented in
  the shared helper and configuration/test notebooks.
- Native taxonomy generation completed: two categories, one boolean permissible
  label of each kind; two actual provider calls, no target evaluation.
- Native case generation completed: 8 prompts (4/4 assignments), 4 scenarios
  (2/2). Four actual provider calls; no fabricated or regenerated rows.
- Reviewed actual definitions, examples and every generated seed description.
  The synthetic refund policy permits guidance while prohibiting unsupported
  actions/status/guarantees; generated content matches that split.
- Explicit review removes generated scenario-specific system prompts from a
  separate copy so the selected policy controls every target.
- Two handwritten prompts added through JSONL; approved coverage is
  5 prohibited/5 permitted prompts and 2 prohibited/2 permitted scenarios,
  14 stable identifiers total.
- Approved suite:
  `outputs/generated/suites/customer-support-1-2fcbd1c12907-f243daf8`.
  Approval records policy/taxonomy/test byte hashes, prompt/shared-settings
  hashes, expected IDs/counts and pinned package versions.
- 52 focused tests pass, including native stage consumption, approval
  invalidation and full-transcript early-failure weighting. All five notebooks
  have valid JSON/Python syntax. Fixtures are synthetic, never live evidence.

### Native integration corrections (shared scope)

1. The released test-set stage rejects `enabled: true` although the runner
   accepts it. The shared emitter omits it only for this active stage (native
   default true); disabled stages remain explicit false. A regression test
   invokes the actual stage with generation mocked, not only the config parser.
2. Native top-level `behavior` is the policy label; `dimensions.behavior` is the
   category accessor. Shared validation/accounting and fixtures use that exact
   shape. No classification is guessed or invented.
3. The native cache writes versioned artifacts and compatibility files, overriding
   save paths. The shared helper resolves `latest.json` and preserves generated
   bytes before review/merge.
4. Prompt rows have no tester identity; scenario rows do. The loader checks these
   released identities instead of rejecting valid prompt artifacts.
5. Native inference unconditionally renumbers cases by input order. The shared
   loader calls the actual release normalizer to join native rows back to
   approved source IDs, including handwritten cases. Evidence shows both IDs;
   new provenance explicitly records the map. Raw inputs/outputs stay intact.
6. Original timestamp-plus-UUID run names made the viewer temp path 264
   characters, exceeding Windows MAX_PATH. Compact suite/run IDs fix the cause;
   shared pre-inference path validation rejects oversized paths. A regression
   test invokes the actual native viewer writer and creates its temp-file shape
   under this repository's generated directory, verifying paths below 260.

No dependency was patched; no replacement conversation/scoring engine, provider
fallback, force-stage retry or catch-and-explain wrapper was added. These are
shared consumer-contract fixes, not infrastructure drift: M1 Bicep remains the
platform source of truth. No temporary local workaround remains.

### Transient prerequisite failure

An initial post-approval management identity check timed out launching Azure CLI
at its native 10-second default, before target inference. An explicit timing
check subsequently succeeded in 1.63 seconds without displaying/persisting the
token. Reused the same approval; no auth substitution or notebook branch.
The initial native test-generation config-key error likewise occurred before
model calls and was fixed upstream in the shared emitter.

### Retained failed evaluation and approved rerun

The original GPT-5 run `older-20261109T082724-cca27fe1` completed all 14
inference rows (34 native model calls: target plus tester), then failed building
the native viewer index at the 264-character path. Judging never started. It is
retained unchanged as failed evidence; the saved-result loader reports 10/10
prompt and 4/4 scenario attempts, 14 missing scores, unavailable rates, and
`complete: false`.

The user explicitly chose **a fresh GPT-5 rerun on short paths**, accepting
duplicate inference cost, instead of reusing saved responses. No automatic
retry/resume or altered evaluation inputs were introduced. The new comparison
still uses the exact approved 14 source cases and shared model roles/settings.

## Completed three-model live verification - 2026-11-09

| Actual target | Run ID | Approved / inferred / scored | Prompt violation | Prompt unnecessary refusal | Scenario violation | Scenario unnecessary refusal |
|---|---|---|---|---|---|---|
| gpt-5 / 2025-08-07 | `older-d4ca097fa39b` | 14 / 14 / 14 | 0/5 (0%) | 0/5 (0%) | 0/2 (0%) | 0/2 (0%) |
| gpt-5.4 / 2026-03-05 | `intermediate-2278f31101eb` | 14 / 14 / 14 | 0/5 (0%) | 0/5 (0%) | 0/2 (0%) | 0/2 (0%) |
| gpt-5.6-sol / 2026-07-09 | `newer-97e575781e6e` | 14 / 14 / 14 | 0/5 (0%) | 0/5 (0%) | 0/2 (0%) | 0/2 (0%) |

- All three native manifests and inference/judge stages completed, with all expected
  IDs reconciled through the pinned source/native mapping. Both native metric
  artifacts and config snapshots reopened successfully.
- Shared approval/policy/taxonomy/test/settings/prompt hashes and package/model
  role identities match. Target identity is the intentional differing field.
- Each run has 10 prompts plus 4 conversations. All twelve actual conversations
  across the three runs contain exactly 3 target responses; none exceed the limit.
- Zero missing inference/scores, inference failures, judge failures/skips,
  filter skips or semantic N/A in the completed comparison.
- No native assessed failures were found, so no live failure example was
  invented. Synthetic fixture tests prove early-failure/later-correction
  weighting, multiple offending-turn evidence and unavailable/error accounting.
- Native successful logical call accounting: 34 inference/tester + 14 judge
  calls per completed target. Rate-limit cooldown/retries occurred in the original
  two runs and completed through the native provider; no custom retry or
  quota/network workaround was made.
  The retained original GPT-5 attempt consumed another 34 logical calls.
- GPT-5.4 completed 34 inference/tester calls and 14 judge calls in 506.3 seconds.
  A subsequent ad-hoc export assertion expected an incorrect comparison label;
  native evaluation had already succeeded and the pre/post immutability checks
  had passed. Export was finalized from that exact saved run using the real
  `equivalent completed comparison` label, with no repeated model calls.
  `third-target-acceptance.json` records current hashes and that verification.
- Real result summaries and descriptive comparison persist in ignored
  `outputs/generated/comparison.json`; selection pointers reopen the three
  completed runs, not the retained failed attempt.
- The existing demo runtime initially lacked IPython, detected by the real
  notebook-source execution check. Installed the standard setup's existing
  `ipykernel` prerequisite and registered `Python (assert01-foundry-evaluation)`.
  No requirements change or global VS Code interpreter switch was made.
- A fresh registered demo Jupyter kernel executed the actual load/result/evidence/
  comparison sections against all three saved live runs and rendered 3 HTML tables.
  The separate unpaid preview reported no missing targets, and execution of the
  completed-target resume never invoked a guard that rejects paid evaluation.
  Captured execution contents were inspected for credentials before disposal.
  The temporary kernel was shut down; no paid calls were made by this check.

### Final local gates and evidence limits

| Check | Outcome |
|---|---|
| Focused standard-library tests | 52 passed, including actual notebook result code, unpaid comparison preview, reuse guards and native viewer writer |
| Dependency consistency and native CLI help | Passed |
| All five notebook JSON/Python syntax | Passed |
| Existing notebook cleanup | Passed; outputs inspected before cleanup |
| Setup-flow/source substitutions and verbatim destroy equality | Passed in focused tests |
| Bicep compilation | Passed; existing local BCP081 type-definition warnings remain, with prior newer-compiler validation recorded below |
| Live deployment identity/version/keyless auth | Reverified; all three selected targets active, account/project and earlier identities unchanged |
| Credential inspection | 81 input/settings/config/native artifact files plus all five notebook outputs inspected; no credential-shaped content found; execution streams also reviewed |
| Approved three-model generation/evaluation/comparison | Passed using the original generated/reviewed suite; no statistical or universal safety conclusion |
| Second-policy customization | Configuration-only/local tests passed; fresh live generation/evaluation not run under bounded two-model authorization |
| Target replacement | Configuration-only/local native config tests passed; additional live alternative not provisioned/evaluated |
| Original third target / three-model acceptance | Passed: exact GPT-5.4 version deployed, native text/JSON and unchanged-suite 14-case evaluation verified |
| Destruction and purge | Not run; resources retained, requiring explicit confirmation before deletion |

### Requirements and success-criteria accounting

| Requirement / criterion | Evidence and status |
|---|---|
| FR-001 | Two ordered milestones delivered under the explicitly approved M1 gate exception |
| FR-002, FR-005, FR-006, FR-008, FR-016 | Eight-section notebooks, editable inputs and documented formats/budgets/lifecycle implemented; local and fresh-kernel display checks passed |
| FR-003, FR-014 | Three distinct real model generations deployed and compared on identical approved inputs |
| FR-004, SC-007 | Native Entra, ignored non-secret settings, source/artifact/output inspections passed |
| FR-007, FR-009, FR-010, FR-011 | Actual generation before approval, immutable hashes, source/native ID mapping, identical target policy and reopenable saved artifacts passed |
| FR-012, FR-013, FR-021, SC-005 | Live numerators/denominators reconciled; local error/N/A/early-failure fixtures passed; no invented live failure examples |
| FR-015, SC-006 | Configuration-only second-policy/target-replacement and retained-suite tests passed; fresh live second-policy evaluation not run |
| FR-017, FR-018, FR-019, FR-020 | Actual 8+4 generation, two additions, both interaction/classification types, finite adaptive transcripts and visible failed-run accounting verified |
| FR-022 | Descriptive equivalent/incomplete/non-equivalent displays implemented/tested; no baseline/regression/pass-fail behavior |
| SC-001 | All three real native text and strict-JSON model connections passed |
| SC-002 | Eight sections implemented; approval gating and actual result rendering verified |
| SC-003, SC-004 | Required 14-case content/turn/provenance checks passed for all three targets; earlier inputs/runs retained byte-identically |
| SC-008 | All three targets displayed from saved artifacts in a fresh kernel; real original failed run still truthfully labeled incomplete |

The hypothesis is supported only as a functioning learning workflow: it can
generate, review, run and compare policy evaluations with real saved evidence.
This small set exposed no violations or unnecessary refusals and does not
establish their absence generally. GPT-5.6-sol is both a compared target and the
shared judge/tester, so the scores are not independent. Original three-model and
live customization success criteria are not falsely marked passed.

### Reusable deployed state

| Setting | Actual value |
|---|---|
| Subscription | `6e7322e5-6a37-496c-b25c-f647c15bebd8` |
| Resource group / location | `rg-assert01` / `eastus2` |
| Account | `aiassert01cqwx2` |
| Project | `proj-assert01` |
| Provider endpoint | `https://aiassert01cqwx2.openai.azure.com/` |
| Project endpoint | `https://aiassert01cqwx2.services.ai.azure.com/api/projects/proj-assert01` |
| Provider API / route | `2024-10-21` / `azure/gpt5_series/<deployment-name>` |
| Authentication | Explicit Entra; Azure CLI developer identity |
| Actual platform settings | `disableLocalAuth: true`, public network enabled |
| Inference RBAC | Account-scoped Cognitive Services OpenAI User |

| Alias | Deployment | Actual model/version | SKU/capacity | Text / strict JSON |
|---|---|---|---|---|
| older | `assert-older` | `gpt-5` / `2025-08-07` | GlobalStandard / 10 | `READY` / `{"ready":true}` |
| newer | `assert-newer` | `gpt-5.6-sol` / `2026-07-09` | GlobalStandard / 10 | `READY` / `{"ready":true}` |
| intermediate | Not deployed | Planned `gpt-5.4` / `2026-03-05` | Not allocated | Skipped, not passed |

GPT-5.4 Global Standard quota was 400 used / 250 limit, leaving no allocation.
All three identities/versions were present as GenerallyAvailable in the selected
live AIServices/S0 catalog. Default capacity was 10; minimum/increment were absent,
so no inferred TPM minimum/increment was used. The catalog also returns OpenAI
account rows: validation selects AIServices/S0, not an arbitrary duplicate.

## Approved authentication remediation

The inherited `MCAPSGovDeployPolicies` initiative's
`CognitiveServices_LocalAuth_Modify` definition forces local authentication off
for AIServices. Its effective effect is `modify`; no policy overrides/exemptions
were applied. Review resolved 11 inherited assignments and 334 member records,
and repeated the actual resource-group scope before account provisioning
(same 11 assignments; no exemptions).

The initial key-based design conflicted with this policy. The installed ASSERT
0.3.0 already implements `ASSERT_AZURE_USE_AAD=1`, a cached
`DefaultAzureCredential`, and a refreshable bearer-token callback for `azure/*`.
The user approved Entra after an actual secure CLI token-acquisition check.
`AZURE_TOKEN_CREDENTIALS=AzureCliCredential` restricts the native chain to the
setup login; no application-owned auth adapter or static token is required.

**Root scope:** Bicep disables local auth and declares scoped developer inference
RBAC. Shared helpers generate only non-secret settings and load explicit native
Entra options. No account keys are fetched. No exclusion tags, policy exemptions,
network mutations, provider switches, or auth fallback remain.

## Other upstream fixes established during execution

- Foundry child operations initially conflicted when project/model writes ran in
  parallel. Bicep now orders deployments after project creation and uses
  `@batchSize(1)`. The subsequent infrastructure deployment succeeded. No notebook
  retry loop or catch-and-explain wrapper was added.
- The management SDK exposes account and deployment details under `.properties`;
  actual SDK objects verified this. Metadata export uses that shape, with a
  regression test executing the real export section against SDK model fixtures.
- A 1,024-token smoke request returned `finish_reason=length`, empty text, and no
  parsed JSON. Reasoning consumed the completion budget. The shared finite budget
  is now 4,096, with no temperature/reasoning overrides or silent token retries.
  Both real text/structured checks then passed. Earlier diagnostic requests were
  billable too; the final successful smoke consists of four logical requests.

## Source provenance and installed environment

- Skeleton/metadata field set: `demo-template`.
- Bicep baseline: `gpt4o01-text-image-audio/infra/main.bicep`.
- Setup: speech source, with only required Python prerequisite/demo identity text
  substitutions; ordered setup flow unchanged.
- Destroy: speech source copied verbatim, not executed.
- CLI resolver: speech executable-path-only helper; no shared subprocess wrapper.
- ASSERT immutable source: `04b713fe73879208369750b3bd5ad53544f3eecc`.

| Runtime/dependency | Actual version |
|---|---|
| Python | 3.12.10 |
| assert-ai | 0.3.0 |
| litellm | 1.106.6 |
| azure-identity | 1.27.0 |
| azure-mgmt-cognitiveservices | 14.1.0 |
| azure-mgmt-resource | 26.0.0 |
| python-dotenv | 1.2.4 |
| pandas | 3.1.0 |

## Validation evidence

- Dependency installation, `pip check`, and native `python -m assert_ai.cli --help`
  passed in this demo's isolated environment.
- Focused standard-library tests cover deployment boundaries, explicit partial
  skips, catalog/quota, secret-free settings, native client parsing/token mapping,
  exact SDK export shape, notebook syntax/hygiene, and source notebook equality.
- Bicep compilation and actual ARM provisioning passed. The installed CLI compiler
  0.45.15 warns BCP081 for newer 2026-09-01 types; independent Bicep 0.48.1 tooling
  validates the stable schema with no diagnostics. No global tool upgrade or API
  downgrade was used.
- Actual deployment/configuration notebook code ran sequentially from its JSON
  sources in a controlled runner. Notebook files retain no saved outputs. Execution
  streams, including deployment/export and failed smoke diagnostics, were inspected;
  no account keys or bearer tokens were displayed. Native raw payloads were not printed.
- Generated environment, metadata, parameters, preflight, and connection evidence
  are covered by existing ignore rules. `.env` now contains no credentials.
- Notebook cleanup and final test outcomes are recorded at completion below.
- Editor Pylance was using another demo's environment and reported missing imports;
  it was not silently switched. Actual execution/import checks used this demo's
  interpreter. Select this demo's kernel/interpreter when opening the lab.

## Original M1 handoff boundary (historical)

Preserve `env/.env` and `outputs/generated/{deployment,connections,preflight}.json`.
These record actual state and the skipped deployment; no fake intermediate alias
is generated. Keep the existing account/project/models/RBAC for subsequent work.

When GPT-5.4 quota is available, remove the explicit skip, revalidate all three,
and rerun deployment/connections using the same identities. At this original
handoff, no policy cases, evaluation fixtures, metrics or comparisons had been
produced. The later explicit two-model M2 approval supersedes the original
three-model prerequisite; completed M2 evidence is recorded above.

Cleanup/purge is not run during M1. Before eventual destruction, inspect possibly
enabled confirmation flags and explicitly select the recorded subscription.

## Original M1 local checks

- All **26 focused tests passed** after notebook normalization.
- Existing pre-commit `nbstripout` hook **passed twice** on all five notebooks.
- Setup authorized-substitution equality and destroy byte equality passed.
- Dependency consistency, native CLI help, compiled Bicep and final typed Bicep
  diagnostics passed; the latest compiler reported zero diagnostics.
- Final read-only SDK verification confirmed exactly two healthy deployments,
  Entra-only account settings, and saved real success evidence with explicit skip.
- No cleanup/purge or M2 tasks were executed.
