# Ownership Attestation content examples — EBWV + LAOC

Four fictional, unsigned EAA content examples. Open index.html in any browser; all reading pages and CSS work offline. JSON-LD uses an embedded prefix context and therefore needs no remote context fetch. Turtle and JSON-LD carry the same RDF data. No signature, disclosure proof, real cnf key binding or operational status service is included.

Sources:
- Ownership Rulebook branch rb_ownership_semantics_feedback_bb, pinned commit 5c9ace01b674ca302f1dd5cc03e58b54c6dd32b5, version 1.0.1 (feedback draft).
- Original EBWV source at a2306846c73de3272321bd82e3d83b3051f45f17.
- LAOC proposal https://jgmikael.github.io/docs/ebwv-ownership/ (draft 0.1, 5 October 2026).

The Rulebook structure is projected into a local oa: namespace, not silently added to EBWV. The current ebwv:owner domain is BankAccount; ebwv:amount is a MonetaryAmount field. Neither is repurposed. Arrangement names, purposes and administration addresses avoid original legal-person domain implications. The original ownershipPercentage TBD/xsd:float definition is replaced by the LAOC proposal.

Validation:
- laoc-content.shacl.ttl: explicit local content profile, based in general on Rulebook sections 2.1–2.9; all four examples pass.
- rulebook-strict-overlay.shacl.ttl: add to the content shapes for literal IR-09/10/11 checks on every interest and an IR-19 all-record total warning. First two pass mandatory checks; indirect case has a 160% double-counting warning. Trust beneficiary and conditional-control cases deliberately fail the literal requirement for artificial ownership/share fields; conditional control also lacks economic rights.
- validation-results.json: actual pySHACL output summary and six negative checks.
- profile.html: mappings, all integrity-rule coverage and limitations.

Birth dates are included using the stricter interpretation of the conflicting draft. Countries are a demo-only FI/GB subset. Entity examples use fictional Euid-format identifiers and a demo identifier; registry existence is not asserted. Trustee and beneficiary economic interests overlap and must not be aggregated as ownership. No UBO determination is made. A production profile must resolve authoritative legal and rulebook decisions, list/array encoding, full code schemes, evidence authenticity, complete indirect-path calculations and cryptographic issuance/presentation verification.

Rebuild:
python3 -m pip install rdflib PyYAML pyshacl
python3 build_examples.py

The build regenerates all reading pages, RDF, profile vocabulary, SHACL and reports, verifies positive/negative checks and JSON-LD/Turtle isomorphism, then creates the downloadable zip.
