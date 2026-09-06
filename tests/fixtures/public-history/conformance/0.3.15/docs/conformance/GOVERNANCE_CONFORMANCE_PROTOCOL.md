# Governance Conformance Protocol

Version: 0.3.15  
Status: Accepted normative protocol

## 1. Purpose and authority boundary

Conformance is a deterministic, offline and non-mutating evaluation of accepted
governance facts. It answers whether those facts are mutually consistent and
whether a proposed local action has already satisfied its separate authority
gates. It never creates Task, Result, Lead, project-policy, module or resource
lifecycle authority.

```text
accepted facts -> read-only evaluation -> derived evidence
derived evidence != authority
ALLOW != action execution
```

The machine-readable policy is `config/CONFORMANCE_POLICY.yaml`. This document
explains that policy; it does not define a parallel workflow engine. Central
governance remains accepted main + release metadata + GitHub Task/PR/Acceptance
and Lead continuity. It must not create a recursive central
`.agent/GOVERNANCE_LOCK.yaml`.

## 2. Canonical results

Overall status is exactly:

```text
CONFORMANT
RECONCILIATION_REQUIRED
BLOCKED
```

Internal drift normalizes as follows:

```text
CONFORMANT        -> CONFORMANT
DRIFT_RECONCILABLE -> RECONCILIATION_REQUIRED
DRIFT_BLOCKING     -> BLOCKED
```

`update_available` is a separate advisory. It never adopts or advances a pin.
Unknown schemas/enums, duplicate keys, unreadable authority inputs, missing
required facts and conflicting refs fail closed.

## 3. Evaluation modes

### Central governance

The caller supplies an explicit repository root and exact expected commit/tree
or candidate identity. The evaluator checks VERSION/release agreement, release
schema and change class, required authority surfaces, takeover and 0.3.14
dispatch invariants, and independent-module metadata. It also verifies that the
declared module version matches the module VERSION file.

The 0.3.14 baseline contains a stale release note naming LPRL 0.2.4 while its
accepted module pin is 0.2.5. That baseline is `RECONCILIATION_REQUIRED`; 0.3.15
corrects only the note. The module block and LPRL module are unchanged.

### Downstream project

The caller supplies an explicit Owner-supplied/confirmed project root. The
evaluator reads only explicitly named paths within that root and checks the
accepted governance lock, local-policy layering, project-state digest, durable
Lead/Task refs, independent-module pin and supplied current topology facts.

```text
project runs != project is governed and conformant
```

The evaluator does not fetch GitHub, search adjacent directories, discover
projects, follow main, repin a module or upload project facts.

## 4. Local Action Gate

The optional local-action request covers Source, Workspace, Deployment, State,
Data, Evidence and Cache, and the actions create/reuse/modify/migrate/retire.
The exact root must be explicit, Owner-supplied/confirmed, verified and within
the project boundary. cwd, HOME, TEMP, repository-name, historical or inferred
paths are never root authority.

An `ALLOW` requires valid governance pin, local policy, matching durable Task,
current topology and a known resource class. Shared/protected resources also
require separate action-specific authority and a complete owner set. Missing or
ambiguous facts produce `BLOCK`.

Unknown resources produce a non-mutating inventory/classification/reconciliation
advisory. The evaluator never adopts, quarantines, migrates, cleans, retires,
resets or deletes them. Those actions remain under existing project/LPRL
authority. A Source change never authorizes Deployment/State/Data/Evidence
mutation.

## 5. Bounded drift triggers

Re-evaluate at these gates, when materially applicable:

1. fresh takeover or reconciliation;
2. new Task activation;
3. governance adoption or update;
4. independent-module repin;
5. before local deploy, migrate or retire;
6. before release acceptance;
7. after material topology change.

These are synchronous gates, not a daemon, polling service, telemetry stream or
central project registry.

## 6. Reference checker

Run the reference checker with explicit paths:

```text
python templates/GOVERNANCE_CONFORMANCE_CHECK.py \
  --root <absolute-owner-confirmed-root> \
  --policy <absolute-policy-path> \
  --input <absolute-input-path>
```

It writes one JSON Result to stdout and no files. Exit codes are 0 for
`CONFORMANT`, 2 for `RECONCILIATION_REQUIRED`, and 3 for `BLOCKED` or evaluator
failure. Its strict YAML subset rejects unsupported constructs rather than
silently misreading them. It has no third-party or network dependency.

The input is a facts/reference envelope, not authority. The output records
checked path/ref identities and findings, but cannot select a root, authorize
work, advance a pin, perform an action or complete acceptance.

## 7. Thin launcher and future Console

A formal Task launcher is one stable copy-oriented thin block pointing to the
durable Task. An editable drafting surface is not the formal launcher payload.
The full durable Task remains authority.

A future Console may display conformance Results as a derived read model only.
It is optional and cannot become authority or a prerequisite for this protocol.

## 8. Qualification

`tests/test_governance_conformance.py` covers Q1-Q12 from the frozen Task plus
determinism, read-only behavior, offline implementation, duplicate-key
fail-closed handling and the exact maximum write-surface declaration.
