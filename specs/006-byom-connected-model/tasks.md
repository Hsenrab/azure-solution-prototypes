# Tasks: BYOM Connected Model Through APIM

**Inputs**: [Specification](./spec.md), [plan](./plan.md).
The user approved local implementation and the field-specific BCP036 accommodation.
Live Azure changes and paid inference are not authorized.

## Tasks

- [X] T001 Enable APIM identity in `demos/byom01-capability-testing/infra/main.bicep`; add `infra/gateway.bicep`, `infra/gateway-policy.xml`, and `infra/backend-access.bicep` for the verified connection, fixed Responses route, scoped RBAC, and body-free telemetry.
- [X] T002 Create `demos/byom01-capability-testing/notebooks/02_configure.ipynb`, reusing the deployment notebook's SDK/compile flow and generated settings; read back the registered connection and save ignored gateway settings.
- [X] T003 Create `demos/byom01-capability-testing/notebooks/03_test.ipynb` for one connected-model prompt-agent invocation, persisted correlation evidence, test-only cleanup, and independent telemetry recheck.
- [X] T004 Update `demos/byom01-capability-testing/requirements.txt`, `README.md`, `metadata.json`, and deployment notebook handoff; exclude only the new generated files in `.gitignore`.
- [X] T005 Compile changed Bicep and validate new notebook syntax and existing notebook hygiene; record results in `specs/006-byom-connected-model/tasks.md`.
- [X] T006 After explicit live approval, run `demos/byom01-capability-testing/notebooks/02_configure.ipynb` twice and `03_test.ipynb` once; verify SC-001 through SC-005, recheck saved evidence without inference, and remove only validation-created resources.
- [X] T007 Add the approved backend navigation project and name/ID outputs in `demos/byom01-capability-testing/infra/backend.bicep`, update README/metadata and feature artifacts, and compile locally. After separately applying the template, verify backend project selection and model visibility in Foundry.
- [X] T008 Move automatic deletion out of **Invoke Connected Model** in `demos/byom01-capability-testing/notebooks/03_test.ipynb`, reuse **Clean Up Test Resources** as the explicit deletion step, update related instructions, and validate locally without live calls.

Dependencies: T002 depends on T001; T003 depends on T002's settings contract.
T004 depends on T001-T003; T005 covers T001-T004. T006 depends on T005 and
separate live approval, including modifications to existing resources and paid calls.

## Validation

Use the existing notebook/Pylance and Bicep tools for local checks. Preserve
canonical setup/destroy and existing pre-commit gates. No new test framework.
Live acceptance requires a nonempty completed Foundry response and a matching
successful APIM trace for the intended GPT-5.4 backend. Missing telemetry remains
pending/unverified. Source review and local compilation are not live acceptance.

### Results

#### Final user-run acceptance and commit checks

- User-run Configure output shows successful deployment, connection readback, and
  generated settings. User-run Test returned a completed, nonempty Foundry response.
- The corrected log query returned a matching APIM request for the saved test:
  API `byom01-responses`, deployment `gpt-5.4`, intended backend URL/resource,
  permitted project principal, and HTTP 200. Verification reported `VERIFIED`.
- The user confirmed backend portal visibility and subsequently reported
  "all works". Configuration repeatability is accepted on that user report, not
  an independently observed assistant-run second deployment.
- User-run explicit cleanup output confirms test conversation/version deletion.
  Configuration resources remain for the user's demo; no assistant-created live
  validation resources require removal.
- The configured pre-commit nbstripout hook removed execution outputs/counts and
  kernel display-name metadata from the four demo notebooks before commit. The
  earlier unavailable-runner and pending-live notes below are historical.

#### Earlier implementation checks

- User-run gateway evidence query failed with KQL SYN0002 at the unquoted `time`
  alias. Fixed the query at its source in `03_test.ipynb` by using `['time']` in
  projection and ordering, preserving the Python result key and verification
  checks. Microsoft Kusto identifier documentation confirms this quoting syntax;
  editor diagnostics report no errors. No catch/reformat wrapper, Bicep change,
  live query, or inference call was added. T006 still requires rerunning the
  corrected log-query cell against the saved invocation.
- Explicit cleanup follow-up: removed invocation's deletion/finally block and
  retained the separate cleanup cell's retry flags, evidence persistence, and
  project guard. Updated notebook/README instructions and spec/plan. Built-in
  notebook summary parsed the changed structure; editor diagnostics reported no
  errors. Existing user execution outputs were preserved, not rerun or treated as
  evidence of the edited behavior. No live inference or deletion was performed.
- Approved backend-navigation follow-up implemented in `infra/backend.bicep`:
  one project using the consumer project pattern, with name/resource-ID outputs.
  Built-in backend Bicep compilation passed with zero diagnostics. Account/model
  configuration and gateway routing remain unchanged; no notebook wrappers or
  local workarounds were added. README/metadata and spec/plan updated.
  T007 remains open only for live backend project selection and model visibility;
  this follow-up did not deploy or modify Azure resources.
- Built-in Bicep compilation passed for the consumer template and gateway template
  (including its backend-access module), with no remaining diagnostics. The
  field-specific, approved BCP036 accommodation remains.
- Inspection of compiled policy output exposed literal placeholders in a Bicep
  multiline string. Remediated upstream by loading the XML policy and performing
  explicit Bicep substitutions; the subsequent compile contains the expected
  ARM replacement expressions.
- Built-in Pylance syntax checks passed for the configure/test Python source.
  Notebook summaries parsed both new notebooks and reported no executed cells.
- Built-in text checks found no execution counts, nonempty output arrays, or
  kernel display-name metadata in the three changed notebooks.
- The configured pre-commit runner was unavailable in the terminal. No dependency
  installation or further terminal validation was attempted after the user
  requested built-in tools. T005 remains open for that exact hygiene gate;
  syntax/text checks are not a claim that pre-commit ran.
- Direct notebook-file Pylance diagnostics were unavailable; syntax validation
  used its code-snippet parser instead. Runtime SDK checks were interrupted and
  are not claimed as passed. Source documentation confirms the selected SDK
  invocation/credential contracts, but does not replace runtime validation.
- XML/service policy validation, dependency installation, configuration
  redeployment/idempotency, Responses feature availability, inference, telemetry
  correlation, and live cleanup have not been verified. T006 requires separate
  explicit approval. No Azure resource or test agent was created.
