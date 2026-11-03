# Architecture notes

## Mixed-fixture contribution extension

[The mixed notebook](../notebooks/06_vector_contributions.ipynb) adds a separate
`hybrid-pagination-mixed-v2` data-plane index on the unchanged service. It does not
alter Bicep, authentication, capacity, SDK/API pins, setup, or cleanup. Original
fixture/evidence/notebook bytes are protected rather than migrated.

Shared Python consumers and the independent .NET reader distinguish 6,183 indexed
IDs from 6,158 keyword IDs and the exact 50 selected vector IDs. Version 1 retains
its recipe/defaults; version 2 declares 6,133 keyword-only, 25 shared, and 25 genuinely
non-keyword vector members. Fixed synthetic proximity demonstrates mechanics only.
Expanded preview recall derives from keyword count, not indexed cardinality.

One-time preparation accepts only an absent/empty correctly defined mixed target.
Every upload result is persisted in a fixture/service/schema-bound receipt.
`uploading` or partial failure remains incomplete; all-successful `uploaded` state
can become `ready` only after exact schema/count/ID-content verification.
Read-only reuse never reuploads, upserts a populated target, deletes unexpected
data, or recreates a missing service. Both clients independently enforce readiness.
Ordered inventory pagination is not a measured case. Hidden vectors remain
non-retrievable; receipts and equal counts do not prove snapshot isolation.

[The local renderer](../app/contributions.py) recomputes eight saved cases through
common inspection and binds fixture/index/environment/query/run identity plus
source-file hashes. It separates expected groups, observed IDs, verified contributions,
count alignment, and overall acceptance. Missing or failed controls cannot establish
accepted vector-only additions. Examples join actual returned IDs to verified local
text with `textSource: verified-fixture`; measured responses remain ID-only.
Internal keyword-window membership is `not-observed` with null IDs, never inferred
from aggregate counts or a separate reference query.

The fix belongs in shared consumers because the all-indexed-equals-keyword assumption
affected both clients and inspectors, not deployed platform behavior. No local
workaround or error-only wrapper remains. Offline checks/build and the separately
approved eight-case live run are complete; see the
[measured report](../outputs/generated/reproduction/mixed-runs/20261102T233019Z-bee9da5d/contribution-comparison.md).
Both stable hybrids reported 6,183 but reached 1,046 unique IDs; preview counts and
reachability agreed at 1,046/6,183 for recall 1,000/6,158. Every hybrid returned the
25 declared vector-only IDs. Both keyword controls nevertheless had 64 duplicate
excess rows and 64 missing IDs, blocking accepted contributions and final acceptance.
The expanded preview's 1,237 populated pages, three final rows, zero duplicates/
empty pages/positive following probes were measured successfully.
All 54 protected original files and original-index metadata/count remained unchanged.
The original keyword duplicate/missing-ID acceptance failure remains unresolved.

For publishing on 2026-11-03, the user separately approved backing up the original
reproduction notebook and applying standard notebook cleanup. Only its saved
outputs, execution counts, and kernel display-name metadata were removed; code,
markdown, and separate measurement evidence were preserved. All 40 local checks
now pass, without changing the live acceptance criteria or keyword-control outcome.

## Resource and identity boundary

The subscription-scoped Bicep wrapper owns the dedicated group; its group-scoped
module owns one Basic Search service and exactly two service-scoped User role
assignments. Service and assignment names are deterministic. North Europe,
one replica/partition, public access without an IP allowlist, and disabled local
authentication are Bicep-defined settings, not notebook toggles.

The setup user's CLI identity is used explicitly through `AzureCliCredential`.
Bind the credential to the selected subscription only; Azure CLI rejects token
requests that specify both tenant and subscription. The account lookup and shared
handoff validator independently verify the tenant and principal.
Deployment and readiness align the CLI default to an explicitly supplied kernel
`AZURE_SUBSCRIPTION_ID` using `az account set` only when needed. They reread the
account after switching, reject an unsuccessful selection, and resolve the current
tenant and signed-in user before SDK use. CLI errors remain visible. This changes
the shared CLI default, not the login identity or any infrastructure settings.
Search Service Contributor covers metadata/index management; Search Index Data
Contributor covers future upload/query operations. No redundant Data Reader,
Search managed identity, model deployment, application secret, or private network
is needed.

The helper preserves the canonical CLI resolver and shares only the pure nine-key
environment-contract validation between export and readiness. It does not hide
authentication, deployment, CLI errors, or fallback behavior.

## Handoff and validation

Policy checking uses the notebook's existing Azure deployment validation and
what-if against the selected subscription/template, followed by deliberately
running the paid-deployment step. There are no prerequisite/deployment confirmation
flags: running that step submits the deployment. A manually authored policy-review file is not
required by deployment, export, or readiness. Azure errors remain visible; these
checks do not claim a full advisory-policy audit or guaranteed deployment success.
The preview writes `outputs/generated/what-if.json` from the actual SDK result.

The deployment SDK consumes the compiled Bicep, waits for actual completion, then
exports the [non-secret contract](../env/.env.example) in one write. Readiness
compares current deployment outputs, live settings, module-owned assignment IDs,
and the signed-in operator before a read-only `get_service_statistics()` call.
The Search control plane returns the region display name `North Europe`; the
readiness comparison removes spaces and ignores case to match `northeurope`,
without accepting a different region or changing the Bicep deployment location.
The pinned stable metadata SDK does not choose either reproduction client's version.
Index creation, synthetic records, queries, and cross-language execution use the
Feature 2 data-plane flow described below.

Raw SDK failures remain visible. No catch-and-explain wrappers, key/identity/network
fallbacks, new retry framework, or notebook-defined infrastructure settings are added.
Generated local validation evidence uses synthetic responses and is not live acceptance.
Runtime errors must be recorded as blocked/failed with the underlying error, not
relabelled ready to finish a task.

## Cleanup ownership and recovery

Only the new group tagged `demo=search02-hybrid-pagination` is a valid cleanup target.
Do not put unrelated resources there or adopt an unowned/shared group.
After partial deployment, use the known literal group input even when export failed.

The destroy notebook is copied **verbatim** from the speech demo, including its
current True confirmation flags. Before its destructive steps, align the active
CLI subscription with the generated/selected subscription, inspect the exact
group/resources, and obtain separate deletion approval. Never use unattended
Run All; opening a notebook is not consent to delete.

Search has no Cognitive Services account to purge. Skip that optional step rather
than changing or forking the source notebook. Its final Cognitive Services list
is informational, not proof of Search group removal. Independently verify actual
group absence and that no outside-scope targets were used. Already-absent cleanup
may raise a raw source error; report actual absence, not a new deletion.

Live validation exposed an existing canonical command issue: `az resource delete`
rejects its `--yes` argument. The per-resource step reported exit code 2, followed
by a misleading unconditional completion message. The canonical **Delete resource
group** step succeeded and independent checks verified absence. Preserve the raw
error in cleanup evidence; do not treat the per-resource message as acceptance.
No local command substitution or canonical-source edit was introduced. A shared
canonical cleanup correction is separate follow-up work.

Record UTC `observedAt` and actual `lifecycleState` in
`outputs/generated/us3-cleanup.json`; use `deleted` only after verified absence.
Retain earlier readiness as historical evidence and treat the environment export
as stale. Before Feature 2, separately approve and rerun deployment, export, and
readiness. There is no automatic reprovisioning or implicitly retained paid service.

## Acceptance outcome

On 2026-10-23, the approved deployment and unchanged-input redeployment retained one
service and the same two direct service assignments. Stable metadata access succeeded
as the setup user with zero indexes/documents. Actual-group inherited policies matched
the complete review. Whole-group cleanup then completed: that historical lifecycle ended `deleted`.
See [validation status](../README.md#validation-status) for evidence and limitations.
Provider registration remains in place. On 2026-10-30 the absent group was
recreated with explicit approval and unchanged Bicep for Feature 2. That service
remains running pending separate cleanup approval.

## Two-client measurement flow

[04_reproduce.ipynb](../notebooks/04_reproduce.ipynb) follows initial readiness,
which must run on the empty service before ingestion. Do not remove data just to
rerun that initial assertion. The notebook checks both toolchains before mutations,
generates the immutable 6,158-record corpus, prepares `hybrid-pagination-debug`,
and requires every upload result and exact indexed count before scans.

SHA-256 bytes determine 16-dimensional integer-valued float32 vectors and varied
keyword content; compact UTF-8 JSONL and a canonical declared-schema hash bind
both clients. Declared schema and actual service schema remain separate evidence.
Exhaustive cosine retrieval removes approximate-neighbor search as a confounder,
not the possibility of score ties. No embedding service or semantic configuration
is used.

Python Search 12.0.0 and .NET Search 12.0.0 independently execute keyword, vector,
and hybrid queries at explicit API 2025-09-01. Public SDK hooks/policies capture
actual payload/API/status/request identity and count sends without recording
authorization headers. Search retries are disabled. Python consumes only the
first `by_page()` page and takes count from its response hook; .NET consumes only
the first `AsPages()` page with the initial response's count. Neither traverses
continuation automatically or invokes the other client's search implementation.

Each case starts with a durable incomplete report and appends/flushed observations.
It scans all advertised offsets, reuses existing observations for boundary
selection, probes only out-of-range boundaries, then repeats once per deduplicated
offset. Probes/repeats do not inflate primary counts. Any short response with
continuation is incomplete, not evidence of exhaustion. A missing vector-only
initial count requires all ten candidate pages with null count/advertised metrics;
successful completion is `not-applicable`, never a failed-case escape hatch.

Comparison is local evidence recomputation, not replacement queries. Complete
keyword baselines and matched inputs/actual requests gate causal attribution.
A count gap plus empty advertised pages reproduces the symptom; candidate-window
causation remains a source-backed hypothesis rather than proof of a customer SDK
defect. Text/vector overlap prevents adding set sizes. Tied ordering, changing
membership across independent offsets, concurrent writes (even with equal
start/end counts), and unknown customer settings remain limitations.

This is data-plane experimentation, not a platform remediation. Bicep, network,
authentication, canonical setup/destroy, and initial readiness behavior remain
unchanged. No temporary infrastructure workaround or catch-and-explain notebook
wrapper is introduced; narrow SDK error persistence is necessary measurement
evidence and rethrows the original failure.

### Measured outcome and metadata correction

The 2026-10-30 run produced all six reports with equivalent actual requests and
matching cross-client ID sets. Both hybrid cases reported 6,158 but reached 1,039
unique IDs across 208 populated pages; advertised pages 209 through 1,232 were
empty. Both vector controls reached 50 IDs. Both keyword controls returned 6,158
rows but only 6,111 unique IDs, so the complete-ID baseline and overall causal
acceptance remain blocked. Equal-score ordering is a limitation, not a proven
explanation of those duplicate/missing IDs. No experimental inputs were changed
to conceal this result.

Client version reporting must distinguish a package from a forwarded type's
defining assembly. In these installed packages `AzureCliCredential` resolves to
Azure.Core; querying that type's assembly incorrectly labeled Identity as 1.54.0.
Loading the actual `Azure.Identity` assembly fixes the shared metadata producer.
The installed package, deps/lock metadata, and matching DLL hashes establish
Identity 1.21.0. Audited corrections preserve original version metadata without
changing page JSONL, query results, or timestamps. This local reporting correction
does not remediate or claim to explain Search's count behavior.

## Optional configured-preview experiment [PREVIEW]

The user separately approved a shorter Python-only comparison in
[05_compare_preview.ipynb](../notebooks/05_compare_preview.ipynb). The existing
Python 12.0.0 evidence is reused unchanged; `.venv-preview` isolates Python Search
12.1.0b2 at explicit API 2026-08-01-preview. Two read-only hybrid cases set
`countRetrievableResults` and text recall 1,000/6,158 against the same fixture.
No new .NET project, kernel switch, schema update, infrastructure, or data writes
are required.

The shared measurement engine accepts an explicit preview profile while retaining
the original stable defaults and CLI contract. Preview SDK model construction
occurs only in the isolated interpreter; local comparison can run in the original
kernel. The comparison recomputes both actual observation files, verifies
baseline input identity, and records the intended SDK/API/settings differences.
It also checks following-page probes for undercounting, not just empty advertised
pages for overcounting.

This is a combined configuration comparison, not an isolated SDK regression test.
The original failed keyword control remains a causal-acceptance limitation.
Preview support and observed count alignment are not production/GA commitments.

The approved read-only run aligned preview counts with unique reachable IDs:
1,039 at recall 1,000, and all 6,158 expected fixture IDs at recall 6,158.
Both had zero empty advertised pages, duplicates, or positive following-page
probes. The 1,000-recall preview shared 1,033 IDs with historical stable evidence,
so membership equality must not be inferred from equal reachable counts.
See the [measured comparison](../README.md#observed-preview-comparison).

## Existing guidance

Use [the authoring workflow](../../../.github/skills/azure-demo-authoring/references/workflow.md)
and unchanged notebook metadata checks. The [feature design](../../../specs/001-provision-search-debug/plan.md)
records approved decisions and runtime prerequisites.
