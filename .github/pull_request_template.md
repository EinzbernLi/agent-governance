## Review checklist

- [ ] Affected module(s) or shared surface identified.
- [ ] Exact changed paths reviewed.
- [ ] No silent Core↔LPRL dependency, automatic loading, or cross-module repin.
- [ ] Privacy boundary reviewed; no credentials, private downstream facts,
      machine-local paths, or adopter telemetry.
- [ ] LPRL Experimental / Preview posture preserved, if applicable.
- [ ] Tests, conformance, or CI evidence linked, as applicable.
- [ ] Any version or release change is declared explicitly (or none is made).
- [ ] No claim that a Worker, Validator, or CI result itself grants acceptance
      authority.
