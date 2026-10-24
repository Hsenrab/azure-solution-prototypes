# Architecture notes

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
Search Service Contributor covers metadata/index management; Search Index Data
Contributor covers future upload/query operations. No redundant Data Reader,
Search managed identity, model deployment, application secret, or private network
is needed.

The helper preserves the canonical CLI resolver and shares only the pure nine-key
environment-contract validation between export and readiness. It does not hide
authentication, deployment, CLI errors, or fallback behavior.

## Handoff and validation

The deployment SDK consumes the compiled Bicep, waits for actual completion, then
exports the [non-secret contract](../env/.env.example) in one write. Readiness
compares current deployment outputs, live settings, module-owned assignment IDs,
and the signed-in operator before a read-only `get_service_statistics()` call.
The Search control plane returns the region display name `North Europe`; the
readiness comparison removes spaces and ignores case to match `northeurope`,
without accepting a different region or changing the Bicep deployment location.
The pinned stable metadata SDK does not choose either reproduction client's version.
Index creation, synthetic records, queries, and cross-language execution belong
to Feature 2.

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
the complete review. Whole-group cleanup then completed: the latest state is `deleted`.
See [validation status](../README.md#validation-status) for evidence and limitations.
Provider registration remains in place; no demo Search service remains running.

## Existing guidance

Use [the authoring workflow](../../../.github/skills/azure-demo-authoring/references/workflow.md)
and unchanged notebook metadata checks. The [feature design](../../../specs/001-provision-search-debug/plan.md)
records approved decisions and runtime prerequisites.
