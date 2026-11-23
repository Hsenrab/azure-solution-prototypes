# Feature Specification: BYOM Capability Testing - Resource Setup

**Feature Branch**: `005-byom-capability-testing`

**Created**: 2026-11-19

**Status**: Approved scope; ready for planning

**Input**: Create a new BYOM capability testing demo, reusing
`evalgw02-aoai-apim-eval`. Step one provides setup notebooks and Bicep provisioning
for APIM, Foundry, and a search resource for future Foundry IQ use. Use standard
paid SKUs. Connecting Foundry IQ and adding capability tests are later work.

## Clarifications

### Session 2026-11-19

- Q: Should this initial demo use public service endpoints or private networking?
  A: Public service endpoints; no private endpoints or virtual network in this step.
  Authentication is still required.
- Q: May cleanup include an explicit APIM purge command after the standard
  cleanup notebook?
  A: Yes. Keep the standard notebook unchanged and document the targeted APIM
  purge command afterward.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare the resource foundation (Priority: P1)

As an engineer preparing to explore bring-your-own-model capabilities, I want one
repeatable setup journey that prepares my local environment and provisions the
gateway, AI project, and search service, without implementing integrations yet.

**Problem**: BYOM experiments need a shared resource foundation before individual
capabilities can be connected or tested.

**Hypothesis**: An engineer can follow the setup journey to provision all three
services and retain their connection details without manually creating resources
or editing generated configuration.

**Why this priority**: This is the entire first slice; capability testing depends
on the resource foundation.

**Independent Test**: Starting with the documented prerequisites and an authorized
Azure subscription, run setup and deployment. Verify all requested services and
the project exist, and their identifiers and endpoints are saved locally.

**Acceptance Scenarios**:

1. **Given** the documented prerequisites, **When** the engineer runs setup,
   **Then** the local environment, notebook kernel, Azure authentication, and
   dependencies are ready in the repository-standard order.
2. **Given** an authenticated engineer and the selected subscription and region,
   **When** deployment completes, **Then** one APIM service, one Foundry resource
   with one project, and one Azure AI Search service exist in the demo resource
   group using standard paid service tiers.
3. **Given** successful deployment, **When** the engineer continues,
   **Then** the resource identifiers and endpoints are available in generated local
   configuration without manually entering values.
4. **Given** the provisioned demo resource group, **When** the engineer runs the
   standard cleanup flow with its required confirmations, **Then** demo resources
   are deleted and supported soft-deleted resources are purged.

### Edge Cases

- Missing prerequisites, insufficient permissions, unsupported regional SKUs, or
  unavailable service capacity must surface their underlying failures; setup must
  not silently switch subscriptions, regions, or pricing tiers.
- Repeating deployment with the same inputs must target the same resource names
  rather than create another set of paid resources.
- Failed deployment must not generate configuration that claims the deployment
  succeeded. Cleanup must remain possible for partially provisioned resources.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Provide a self-contained demo titled "BYOM capability testing" with
  a documented provisioning-only scope and prerequisite list.
- **FR-002**: Provide the standard local setup journey followed by resource
  deployment, with no manual resource creation required.
- **FR-003**: Provision one APIM service, one current Foundry resource with a
  project, and one Azure AI Search service in a single demo resource group.
- **FR-004**: Use standard paid SKUs supported by each service, not free or
  developer tiers. Document the selected tiers and ongoing charges.
- **FR-005**: Generate local configuration containing the subscription, resource
  group, resource/project identifiers, and service/project endpoints after
  successful deployment. Do not commit generated configuration or credentials.
- **FR-006**: Provide the repository-standard cleanup journey for the demo
  resource group, including supported soft-delete purging. Keep the standard
  destroy notebook unchanged and document an explicit, targeted APIM purge
  command afterward.
- **FR-007**: Keep this slice limited to resource setup: no Foundry IQ connections,
  knowledge bases, search indexes, ingestion, APIM routes/backends, model
  deployments, BYOM registration, or evaluation/capability tests.
- **FR-008**: Use public service endpoints with authentication required. Private
  endpoints and virtual-network infrastructure are out of scope for this step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Following only the documented setup journey produces all three
  requested services and one AI project, with zero manual resource-creation steps.
- **SC-002**: All required identifiers and endpoints are saved automatically;
  zero generated connection values require manual copying.
- **SC-003**: Repeating deployment with unchanged inputs leaves one set of demo
  resources, not duplicate paid instances.
- **SC-004**: The confirmed cleanup journey removes the demo resource group and
  purges supported soft-deleted resources.

## Assumptions

- Approved scope: provisioning only is step one. Paid resources are acceptable;
  connecting Foundry IQ and testing BYOM capabilities are explicitly deferred.
- The demo directory will be `demos/byom01-capability-testing/`. Reuse applicable
  deployment code from `demos/evalgw02-aoai-apim-eval/`, not its classic OpenAI
  resource design, model deployments, gateway routing, or evaluations.
- Use Bicep for infrastructure. Follow the existing demo template for supporting
  files and the speech demo's source-of-truth setup and destroy notebooks.
- This approved initial slice includes only setup, deployment, and cleanup
  notebooks; do not add empty configure/test notebooks to fill the usual journey.
- Azure AI Search is the resource foundation for future Foundry IQ functionality;
  provisioning it does not constitute a working Foundry IQ integration.
- Select concrete supported standard SKUs and stable resource API versions during
  planning/implementation. Do not add a model merely to provision the foundation.
- The engineer supplies an authorized subscription and a supported region.
  Subscription selection follows repository guidance, never the first enabled
  subscription by default.
- Validate Bicep compilation and applicable notebook hygiene locally during
  authoring. The user authorizes live deployment and acceptance for this demo
  using the agreed standard paid SKUs. Clean up all resources created for
  validation, including Foundry/APIM soft-delete purges, and verify cleanup.
  Do not delete unrelated or pre-existing resources. Report live evidence
  separately from local checks and explicitly identify anything remaining.
