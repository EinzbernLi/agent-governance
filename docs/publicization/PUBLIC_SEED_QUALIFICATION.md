# Clean Public Seed Qualification

This document defines how to derive a **qualified clean public seed** from an
accepted private Governance Lab source. A target public repository must be
created from that derived seed view, not by changing the private source
repository's visibility and not by copying its Git history.

The qualification flow is:

```text
accepted private source main
-> apply config/PUBLIC_SEED_POLICY.json exclusions
-> scan retained text for private-Lab literals, strong secret patterns, and
   concrete user-home absolute paths
-> qualify the retained seed view
-> later, after Owner decisions and target public repository identity exist,
   create a fresh public root/history
```

## Reinitialized surfaces

When the source is a private Governance Lab, its `.agent/**` files are active
self-hosting and Lead-continuity state. They are excluded from the clean seed
instead of being destructively rewritten. The source private `CHANGELOG.md` is
also excluded because private development and pilot history is not public
release history.

After the target public repository identity and continuity sink exist, public
`.agent/BOOTSTRAP.md` and `.agent/PROJECT_STATE.md` are initialized from fresh
public facts. `CHANGELOG.md` is initialized from the public release boundary.
None of those public files are copied from their private-Lab counterparts.

Source `.publicization/**` is private-Lab-only qualification control data. In
particular, the source private denylist is an input to qualification and is
itself forbidden from entering the seed.

## Authority boundary

A PASS means only that the derived tree content satisfies the current clean-seed
contract. It does not authorize repository creation or publication, does not
choose namespace, LICENSE, or first public version, and does not decide whether
optional Console tooling is in the first release tag.

Any target public repository created from this process must begin with a fresh
root/history; no private commit ancestry is inherited.

After public launch, public-to-private baseline synchronization may be
mechanical. Private-to-public changes remain controlled promotion candidates
that require generalization, sanitization, public-side validation, and public
acceptance. A full Promotion Protocol is outside this qualification task.
