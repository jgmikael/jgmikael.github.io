from pathlib import Path
from rdflib import Graph, URIRef, RDF, RDFS, OWL, SKOS, Namespace
from html import escape
from html.parser import HTMLParser
import json
P=Path(__file__).resolve().parent
g=Graph().parse(P/'core-business-ap.ttl',format='turtle')
DC=Namespace('http://purl.org/dc/terms/'); FOAF=Namespace('http://xmlns.com/foaf/0.1/'); SC=Namespace('https://schema.org/')
ont=next(g.subjects(RDF.type,OWL.Ontology))
classes=sorted(g.subjects(RDF.type,OWL.Class),key=str)
props=sorted(set(g.subjects(RDF.type,OWL.ObjectProperty))|set(g.subjects(RDF.type,OWL.DatatypeProperty)),key=str)
terms=classes+props
def eid(u): return str(u).rsplit('/',1)[-1].rsplit('#',1)[-1]
def label(u): return str(g.value(u,RDFS.label) or eid(u))
def link(u): return '<a href="'+escape('#'+eid(u) if u in terms else str(u),quote=True)+'"><code>'+escape(g.namespace_manager.normalizeUri(u))+'</code></a>'
class SafeHTML(HTMLParser):
 def __init__(self): super().__init__(); self.out=[]
 def handle_starttag(self,t,attrs):
  if t in ('ul','li','p','strong','em','br'): self.out.append('<'+t+'>')
  elif t=='a':
   href=dict(attrs).get('href','')
   self.out.append('<a href="'+escape(href,quote=True)+'">' if href.startswith(('https://','http://')) else '<a>')
 def handle_endtag(self,t):
  if t in ('ul','li','p','strong','em','a'): self.out.append('</'+t+'>')
 def handle_data(self,d): self.out.append(escape(d))
def prose(v):
 p=SafeHTML(); p.feed(str(v)); return ''.join(p.out)
def section(u):
 rows=[]
 for pred,title in [(RDF.type,'Type'),(RDFS.isDefinedBy,'Defined by'),(RDFS.domain,'Domain'),(RDFS.range,'Range')]:
  vals=list(g.objects(u,pred))
  if vals: rows.append('<tr><th>'+title+'</th><td>'+', '.join(link(v) for v in vals)+'</td></tr>')
 notes=''.join('<div class="scope"><h4>Scope note</h4>'+prose(v)+'</div>' for v in g.objects(u,SKOS.scopeNote))
 related=''
 for pred,title in [(RDFS.domain,'Properties with this domain'),(RDFS.range,'Properties with this range')]:
  vals=sorted(g.subjects(pred,u),key=str)
  if vals: related+='<p><strong>'+title+':</strong> '+', '.join(link(v) for v in vals)+'</p>'
 return '<section id="'+eid(u)+'"><h3>'+escape(label(u))+'</h3><p><a href="'+str(u)+'"><code>'+str(u)+'</code></a></p>'+''.join('<p>'+prose(v)+'</p>' for v in g.objects(u,RDFS.comment))+'<table class="def"><tbody>'+''.join(rows)+'</tbody></table>'+notes+related+'</section>'
editors=[]
for e in g.objects(ont,URIRef('http://www.w3.org/2001/02pd/rec54#editor')):
 name=' '.join(str(g.value(e,p) or '') for p in (FOAF.firstName,FOAF.lastName)).strip()
 aff=g.value(e,SC.affiliation)
 editors.append({'name':name,'company':str(g.value(aff,FOAF.name) or '')})
editors.sort(key=lambda e:e['name'].split()[-1])
url='https://jgmikael.github.io/docs/core-business/'
config={'specStatus':'unofficial','shortName':'eu-core-business','thisVersion':url,'latestVersion':url,'editors':editors,'alternateFormats':[{'uri':'core-business-ap.ttl','label':'Turtle (original RDF)'},{'uri':'vocabulary.jsonld','label':'JSON-LD'}],'publishDate':'2026-10-13','license':'cc-by','doRDFa':False}
refs=sorted({v for p in (RDFS.domain,RDFS.range) for v in g.objects(None,p) if v not in terms},key=str)
html='''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EU Core Business Vocabulary</title>
<script class="remove" src="https://www.w3.org/Tools/respec/respec-w3c"></script>
<script class="remove">var respecConfig = '''+json.dumps(config)+''';</script>
<style>body{font-family:system-ui,sans-serif;line-height:1.6;max-width:56em;margin:auto;padding:2em;color:#20252b}h1,h2,h3{color:#005a9c}a{color:#005a9c}code{overflow-wrap:anywhere}.def{border-collapse:collapse;width:100%;margin:1em 0}.def th,.def td{padding:.5em .8em;text-align:left;border-bottom:1px solid #ddd;vertical-align:top}.def th{width:8em;background:#f4f6f8}.terms>section{border-bottom:1px solid #ccd4dc;padding-bottom:1.5em}.scope{border-left:3px solid #ccd4dc;padding-left:1em}.notice{background:#f2f6fa;padding:1em}</style></head><body>
<section id="abstract"><h2>Abstract</h2><p>This publication documents the EU Core Business Vocabulary terms contained in the supplied <code>core-business-ap.ttl</code> RDF file: 4 classes and 10 properties, covering accounting documents, administrative units, contact points, legal status, registration dates and powers of attorney.</p></section>
<section id="sotd"><h2>Status of this document</h2><p class="notice">This is an unofficial HTML rendering of the supplied RDF, published alongside GAM. It is not an official EU or W3C publication. The source identifies the ontology as <code>core-business</code> and records an issue date of 12 May 2026. No version identifier is asserted in the file.</p><p>The original definitions, domains, ranges and scope notes are preserved. External terms referenced by the RDF are linked but are not redefined here. This document covers the uploaded file rather than claiming to reproduce every term in the wider Core Business Vocabulary.</p></section>
<section id="overview"><h2>Overview</h2><dl><dt>Ontology IRI</dt><dd>'''+link(ont)+'''</dd><dt>Source labels</dt><dd>core-business (English); core-business (Dutch)</dd><dt>Source maker</dt><dd>Core Vocabularies Working Group</dd><dt>Source mediator</dt><dd><a href="https://semic.eu">Semantic Interoperability Community (SEMIC)</a></dd><dt>Source license</dt><dd><a href="https://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0</a></dd></dl><p>The editors listed above are those credited by the source RDF.</p><p><a href="core-business-ap.ttl">Download original Turtle</a> · <a href="vocabulary.jsonld">Download JSON-LD</a> · <a href="build.py">Publication build script</a></p></section>
<section id="index"><h2>Term index</h2><h3>Classes</h3><ul>'''+''.join('<li>'+link(t)+' — '+escape(label(t))+'</li>' for t in classes)+'''</ul><h3>Properties</h3><ul>'''+''.join('<li>'+link(t)+' — '+escape(label(t))+'</li>' for t in props)+'''</ul></section><section id="classes" class="terms"><h2>Class definitions</h2>'''+''.join(section(t) for t in classes)+'''</section><section id="properties" class="terms"><h2>Property definitions</h2>'''+''.join(section(t) for t in props)+'''</section><section id="external"><h2>Referenced terms</h2><p>These domain and range terms are referenced, but not defined, in the uploaded RDF.</p><ul>'''+''.join('<li>'+link(t)+'</li>' for t in refs)+'''</ul></section></body></html>'''
(P/'index.html').write_text(html)
g.serialize(destination=P/'vocabulary.jsonld',format='json-ld',indent=2)
print(f'{len(g)} triples; {len(classes)} classes; {len(props)} properties')
from rdflib.compare import isomorphic
assert isomorphic(g,Graph().parse(P/'vocabulary.jsonld',format='json-ld'))
print('JSON-LD graph matches original RDF')
