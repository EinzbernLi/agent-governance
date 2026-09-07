# Contributing

This repository has exactly two product modules: Core Governance and the
optional Local Resource and Process Lifecycle (LPRL) module. Core Governance
does not require LPRL, LPRL base operation does not require Core Governance,
and module presence does not imply loading. LPRL's current public-release
posture is Experimental / Preview; production reliance is not currently
recommended.

When proposing a change or opening a pull request:

- Identify the affected module(s) or shared tooling/documentation surface.
- Do not silently repin, load, or create a dependency on the other module.
- Normative behavior changes need tests or conformance updates and independent
  validation before acceptance. Documentation-only changes must still preserve
  canonical authority boundaries.
- Keep public examples and fixtures generic or intentionally anonymized.

Do not submit credentials, personal secrets, machine-local absolute paths,
private downstream Task/Issue/Lead/branch/SHA facts, private project data, or
adopter telemetry. GitHub Issues and pull requests are durable project facts;
README and community documentation are navigation/support surfaces, not new
semantic authority.
