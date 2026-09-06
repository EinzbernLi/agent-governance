# Governance Source, Update Discovery & Adoption Protocol

Version: 0.3.10  
Status: Accepted normative protocol

## 1. Goal

A downstream project adopts one explicit governance source plus one exact accepted pin in `.agent/GOVERNANCE_LOCK.yaml`.

Core invariants:

```text
accepted pin = current downstream governance authority
new/changed upstream release != automatic downstream adoption
fork history != downstream governance semantics
```

From the downstream project's perspective, the configured `governance.repository` is simply its governance upstream. Whether that repository is an official distribution, a fork or an independently maintained compatible repository is not a separate project mode.

## 2. AI-first informed adoption contract

Normal adoption is AI-first. A Web/Codex/other capable coding agent reads this governance repository and the target repository, derives the minimum required project files, and asks the Owner only about real optional behavior that cannot be inferred safely.

Ordinary governance adoption means **Core Governance is enabled**. Core safety/authority semantics are not decomposed into disable-able feature checkboxes. First adoption presents one thin informed prompt covering only:

```text
1. governance update discovery
   - github_native_notify (recommended)
   - manual_pinned

2. project-local model calibration
   - enabled (recommended when supported)
   - disabled
   - data remains in this project either way

3. anonymized upstream model feedback permission
   - disabled (default)
   - enabled for explicit anonymized aggregate export only
   - enabled != automatic delivery

4. optional LPRL
   - disabled (default)
   - enabled only after repeating Experimental / Preview posture
```

Governance Console is separate optional tooling and is not an ordinary adoption question.

The AI should explain the effect of the recommended profile, let the Owner confirm or change those choices once, and then deploy automatically. This interaction is presentation only:

```text
informed adoption != feature management system
no second adoption state store
```

Choices persist only in existing downstream surfaces:

```text
GOVERNANCE_LOCK.update_policy.mode
LOCAL_POLICY.model_calibration.enabled
LOCAL_POLICY.model_calibration.upstream_export
GOVERNANCE_LOCK.modules.lprl + existing LOCAL_POLICY LPRL state when selected
```

Do not create `ADOPTION_PROFILE`, feature-flag databases, wizard state, module-manager state or a central adopter registry merely to remember onboarding choices.

A minimal AI-first adoption should:

```text
read governance source
-> inspect target repository
-> preserve existing project-local rules
-> derive one governance source + exact accepted pin
-> present the four bounded optional choices above
-> Owner confirms once
-> write/update minimum existing .agent governance state
-> install only selected existing detector/calibration components
-> if LPRL selected, continue through existing LPRL gates
-> run applicable conformance / cold-start validation
```

The Agent must not ask the Owner to hand-copy templates or repeat facts that can be safely derived from the target repository. Human-readable docs/templates remain the auditable specification, AI input and recovery path, not a second manual-installation product.

## 3. Update modes

### `github_native_notify`

Install the central template `templates/GOVERNANCE_UPDATE_CHECK.yml` into the downstream project as:

```text
.github/workflows/governance-update-check.yml
```

The installed detector is downstream-local convenience infrastructure. It reads `.agent/GOVERNANCE_LOCK.yaml` as its source/version/mode configuration and must not maintain a second governance-source config file.

Normal takeover/new-Task behavior:

```text
read accepted GOVERNANCE_LOCK
-> read downstream-local governance-update signal if present
-> no signal: continue under accepted pin
-> signal present: surface it; compatibility review begins only when Owner/project policy chooses
```

A normal takeover must not re-read the entire upstream governance repository merely to prove that no update exists.

### `manual_pinned`

Do not install proactive governance-update checking.

Keep the accepted exact governance pin and do not proactively query the upstream source during ordinary takeover, resume or new-Task creation.

Only an explicit Owner request such as `检查治理规则更新` or `升级治理规则` initiates upstream discovery/review.

## 4. Downstream-local GitHub update signal

The canonical detector signal is one open GitHub Issue in the downstream repository using marker/title prefix:

```text
[GOVERNANCE-UPDATE-SIGNAL]
```

The provided workflow reconciles that signal from the current `.agent/GOVERNANCE_LOCK.yaml`:

```text
mode != github_native_notify
-> detector self-disables and closes any stale open signal

observed source VERSION == accepted protocol_version
-> close any open signal

observed source VERSION differs
-> create or refresh one local signal

configured source cannot be checked
-> create or refresh one local CHECK_FAILED signal
```

A source mismatch is intentionally treated as review-needed evidence rather than assuming semantic-version ordering. The project Lead/Owner decides whether the observed source state is a newer compatible release, a rollback/divergence, or another condition.

The signal may include only the minimum downstream-local facts needed for review, such as configured governance source, accepted version/pin, observed source version, check status and observation time.

The detector must not write those downstream facts into the governance source repository.

## 5. Credentials and source access

Public governance sources require no extra adopter credential beyond normal public GitHub access.

A project that intentionally adopts a private custom governance source may optionally provide a downstream-local GitHub Actions secret named:

```text
GOVERNANCE_SOURCE_TOKEN
```

That secret is only for downstream read access to the configured private governance source. It must not be committed, logged, uploaded to central governance, or treated as adopter registration.

Failure to read the configured source creates/refreshes a downstream-local `CHECK_FAILED` signal. It does not revoke the project's existing accepted pin unless the project's own `LOCAL_POLICY` imposes a stricter freshness requirement.

## 6. Discovery is not adoption

In either mode:

```text
update discovered
!=
update adopted
```

A newer or otherwise different upstream release has no downstream authority effect until the project explicitly accepts a new pin.

Adoption flow:

```text
local update signal or explicit Owner request
-> read upstream VERSION / release compatibility metadata from one coherent ref
-> load only release-specific migration/change material needed for review
-> assess compatibility with downstream LOCAL_POLICY and active work
-> update only project files required by that release
-> update GOVERNANCE_LOCK protocol_version + pinned_ref
-> perform release-required validation if any
-> project Lead / Owner accepts the pin change
```

`auto_follow_main`, automatic adoption and automatic pin advancement are forbidden.

## 7. Project-specific supplementary rules

Central/upstream governance and project-local policy are separate layers:

```text
governance source
  = reusable authority/safety/continuity invariants

GOVERNANCE_LOCK
  = source + exact accepted version/ref + update mode

LOCAL_POLICY
  = project-specific protected paths, tests, domain constraints,
    risk rules, local-resource boundaries and local calibration/export choices

Task
  = bounded task-specific scope/authorization

runtime-local plan
  = execution aid only
```

Precedence:

```text
upstream non-negotiable invariants at the accepted pin
>
project LOCAL_POLICY
>
explicit Task scope/authorization
>
runtime-local planning
```

A lower layer may refine or tighten an upper layer but must not silently weaken it. An upstream upgrade that genuinely conflicts with `LOCAL_POLICY` stops at compatibility review; it does not silently overwrite project rules.

Project-specific supplementary rules stay in the downstream repository and are never uploaded to the governance source as part of update checking.

## 8. Public-repository / stateless-upstream model

A reusable governance repository may be public. Normal use is a pull relationship:

```text
governance source repository
        ↓ read release/version metadata when needed
AI / downstream GitHub automation
        ↓
user project
  GOVERNANCE_LOCK
  LOCAL_POLICY
  PROJECT_STATE / GitHub Task facts
  project-local model calibration
  optional LPRL facts
```

The governance source requires:

- no adopter registration;
- no downstream-project registry;
- no downstream repository/Issue/Lead/Task/branch/SHA/workspace/deployment/state/LPRL-fact ingestion;
- no raw downstream model-outcome or raw project-evidence ingestion;
- no usage telemetry or phone-home for correctness;
- no adopter credentials/tokens;
- no automatic cross-repository mutation.

These boundaries apply whether the downstream repository is public or private. Full downstream facts remain at the downstream authority boundary.

Optional model feedback may cross that boundary only after downstream-side anonymization and aggregation, using `templates/PROJECT_ROUTING_FEEDBACK.yaml`. It is an explicit contribution path, not part of ordinary correctness:

```text
upstream feedback sharing is explicit opt-in and never automatic
downstream raw facts -> local aggregation -> anonymized aggregate -> explicit contribution
```

The upstream aggregate must not carry project/repository identity, Task/Issue/PR/SHA/path/business/personal facts, raw sample rows or a stable adopter pseudonym/hash. An anonymous package without stable source identity cannot be counted as machine proof of a distinct project source for global-promotion thresholds; do not create a hidden identity solely to satisfy that threshold.

Only intentionally generic/anonymized reusable rules, fixtures, public-safe reproducers or aggregate calibration conclusions belong upstream.

## 9. GitHub-native detector authority boundary

The update detector is convenience infrastructure, not authority.

It may:

- read `.agent/GOVERNANCE_LOCK.yaml` in the downstream repository;
- read `VERSION` from the configured governance source;
- create/update/close one downstream-local governance update Issue signal;
- run on a bounded schedule or `workflow_dispatch`.

It may not:

- edit `GOVERNANCE_LOCK` automatically;
- edit `LOCAL_POLICY` automatically;
- merge an upgrade;
- grant Task/Result/Lead authority;
- register the project with upstream;
- send project facts or telemetry upstream;
- silently switch governance source;
- silently change `update_policy.mode`.

A failed/missing scheduled check does not invalidate an already accepted pin. Projects that require stronger freshness guarantees may tighten this in `LOCAL_POLICY`, but the public core does not force that policy on every adopter.

## 10. Release metadata contract

Root `GOVERNANCE_RELEASE.yaml` is compact compatibility metadata, not a second authority. It describes at least:

- current ordinary-governance version/change class;
- supported downstream update-discovery modes;
- detector template/signal contract when provided;
- whether automatic adoption/pin advancement is allowed (false);
- compatibility-review requirements for a pin change;
- project-local policy layering invariants;
- independent module-pin behavior;
- zero-registration/zero-telemetry/stateless-upstream privacy properties;
- informed-adoption behavior without creating a second adoption state store.

Accepted upstream source ref/version remains the release authority; the downstream project's exact accepted pin remains its active governance authority until explicitly changed.

## 11. Acceptance cases

- AI-first first adoption -> presents the four bounded optional choices, then writes only existing downstream authority/state surfaces.
- Core adoption -> does not offer safety/Task/Acceptance/anti-drift invariants as disable-able feature flags.
- project-local calibration -> explicit first-adoption choice; if disabled, routing falls back to governance/global priors without weakening Task authority.
- upstream model feedback -> disabled by default; enabling permits explicit anonymized aggregate export only and never automatic cross-repository delivery.
- LPRL -> disabled by default and retains independent pin / Preview posture when selected.
- `github_native_notify` -> installs the downstream workflow template and records its mode in `GOVERNANCE_LOCK`.
- detector -> reads source/version/mode from `GOVERNANCE_LOCK`, not duplicate workflow configuration.
- source version matches accepted version -> no open governance update signal remains.
- source version differs -> one downstream-local update signal exists; no automatic adoption occurs.
- source check fails -> one downstream-local `CHECK_FAILED` signal exists; existing accepted pin remains authority.
- `manual_pinned` -> no proactive update workflow is installed; ordinary takeover/new Task does not proactively access upstream.
- no second adoption state store exists; Console remains separate optional tooling rather than an onboarding module.
