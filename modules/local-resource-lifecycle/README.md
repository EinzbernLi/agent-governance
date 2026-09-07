# Local Resource Lifecycle (LPRL)

> **Current public-release posture: Experimental / Preview.** LPRL has not completed sufficient real-project end-to-end validation, and production use is **not currently recommended**. Inclusion in this repository supports evaluation, design review and controlled experimentation; it is not a production-readiness claim. LPRL remains optional and disabled by default, and module presence does not imply loading.

LPRL is an optional, independently pinned module. It is not part of the Core Governance default surface and is loaded only when a downstream project explicitly enables its accepted LPRL pin.

Canonical paths at this module pin:

- specifications and controlled-migration documents: `modules/local-resource-lifecycle/docs/`
- LPRL schemas and operational templates: `modules/local-resource-lifecycle/templates/`
- module semantic version: `modules/local-resource-lifecycle/VERSION`

A downstream project must resolve the module root and these paths at the exact LPRL pin it accepted. An ordinary-governance upgrade must not silently repin an independently pinned LPRL module or rewrite the paths valid at an older pin. Git history remains the archive; no legacy compatibility copy is maintained in the current tree.
