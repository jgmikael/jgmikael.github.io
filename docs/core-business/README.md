# EU Core Business Vocabulary — expanded publication

Unofficial ReSpec documentation of all classes and properties in Annex A of [SEMIC Core Business Vocabulary 2.3.0](https://semiceu.github.io/Core-Business-Vocabulary/releases/2.3.0/#quick-reference).

Published at https://jgmikael.github.io/docs/core-business/

## Coverage

- 13 entity classes, 49 distinct properties, 51 class–property usages, 54 Annex A rows.
- Five supporting value types (Code is skos:Concept, a class).
- All original term IRIs retained; no replacement EU identifiers minted.
- All 146 triples from the uploaded RDF retained in the expanded 373-triple graph.

## Files

- `index.html`: complete class and property documentation, definitions, usage notes, class-specific ranges and cardinalities, subclass relationships, term index and Annex A.
- `vocabulary.ttl` and `vocabulary.jsonld`: equivalent expanded RDF descriptions of the terms.
- `core-business-ap.ttl`: original uploaded RDF, unchanged.
- `source-shapes-2.3.0.ttl`: unchanged official SHACL constraints from the release.
- `source-release-2.3.0.html`: official release HTML snapshot used to build the documentation.
- `build.py`: repeatable build and coverage checks.
- `coverage.json`: machine-readable validation summary.

The expanded RDF is a documentation compilation, not a new official EU ontology. Profile-specific uses of reused terms are not asserted as new global RDFS domains or ranges. They are documented in HTML and represented by the official SHACL. Original RDF global assertions remain unchanged. The full class-context descriptions are taken from the release HTML; shared properties can have different descriptions in each context.

## Rebuild

```sh
pip install rdflib==7.6.0 beautifulsoup4
python build.py
```

The build checks exact Annex A coverage, every class–property pair against the official SHACL, preservation of original triples, RDF graph equivalence, and internal HTML anchors.

Source material © 2026 European Union, CC BY 4.0. Source editors are credited in the publication. Original source: https://github.com/SEMICeu/Core-Business-Vocabulary/tree/master/releases/2.3.0

Separate static RDF URLs are available; Accept-header content negotiation is not configured on GitHub Pages.
