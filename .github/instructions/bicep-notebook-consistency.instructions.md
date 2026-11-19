---
applyTo: "demos/**,demo-template/**"
excludeAgent: "cloud-agent"
---

For code reviews of demos, check only concrete, relevant consistency issues:

- Trace Bicep parameters and outputs through generated `env/.env`, `env/.env.example`, and notebook/helper consumers. Check identity and RBAC usage against deployed authentication and network settings; infrastructure and platform behavior belong in Bicep, not notebook workarounds.
- Compare setup notebooks with the `speech01` flow (venv/kernel, Azure authentication and optional subscription selection, then dependencies) and destroy notebooks with the canonical `speech01` behavior. Allow intentional demo-specific substitutions.
- Check setup dependencies and kernel, resource and subscription scope, notebook ordering, and directly related documentation for conflicting paths or values and their practical consequences.

Preserve intentional differences between demos, lightweight feasibility scope, and pinned experimental SDK/API versions. Do not request blanket production hardening or unrelated outdated-code fixes. Report only actionable, evidence-backed findings on the pull request; refer to notebook headings, not cell numbers. Explain the conflicting files or values and practical consequence, and prefer a Bicep or shared-root correction when supported by the evidence. Do not make changes, commit suggested fixes, open fix pull requests, or claim execution that was not observed.
