from pathlib import Path
import re
root=Path(__file__).parent
t=(root/'upstream/template.html').read_text()
t=t.replace('https://w3id.org/ebwv"','https://jgmikael.github.io/docs/ebwv-ownership/"')
t=t.replace('shortName:   "ebwv/v0.1"','shortName:   "ebwv-ownership-draft"')
t=re.sub(r'editors: \[.*?\],\s*alternateFormats:', 'editors: [{name: "Mikael af Hällström"}],\n          alternateFormats:',t,flags=re.S)
t=t.replace('postProcess : [remove_status_remark],','')
t=re.sub(r'<section id="sotd">.*?</section>', '<section id="sotd"><p><strong>Draft proposal, 5 October 2026.</strong> Not an adopted EBWV release or W3C Recommendation. Proposed identifiers retain the EBWV namespace pending governance approval. Contains 29 new properties, 9 new classes and a replacement proposal for ownershipPercentage.</p><p>Source: <a href="vocabulary.yml">YAML</a>. Existing EBWV classes are referenced without redeclaration. Domain and range alternatives are OWL unions, not mandatory fields. Detailed condition profiles and controlled concept schemes remain to be designed.</p></section>',t,flags=re.S)
t=re.sub(r'<h3>Data model</h3>.*?<section>\s*<h2><code>@context</code>', '<h3>Data model</h3><p>Legal arrangements, instruments, participation, asset rights and AML determinations are distinct resources. A trust position does not automatically establish title to every asset. Relationships are not declared transitive.</p><p>OWL signatures infer types. SHACL profiles should validate percentages, concept schemes, path members, dates and cardinalities. The existing ownershipPercentage definition must be replaced during integration, rather than combined with this draft.</p><p>AML basis: Regulation (EU) 2024/1624, Articles 2, 55, 58–60 and 62. General applicability begins 10 July 2027.</p></section><section><h2><code>@context</code>',t,flags=re.S)
t=t.replace('<dd>0.1</dd>','<dd>Draft 0.1 — 2026-10-05</dd>')
t=t.replace('<style type="text/css">','<style type="text/css">\nbody{max-width:72rem;margin:2rem auto;padding:0 1.5rem;font:17px/1.6 system-ui,sans-serif;color:#202b33;}h1,h2,h3{color:#005a9c;}code{overflow-wrap:anywhere;}')
t=t.replace('<link rel="icon" type="image/svg+xml" href="/favicon.svg" />','')
(root/'template.html').write_text(t)
