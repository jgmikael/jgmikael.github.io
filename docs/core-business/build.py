"""Rebuild documentation and expanded RDF from the supplied RDF and SEMIC 2.3.0.
Dependencies: rdflib==7.6.0 beautifulsoup4 (compatible release).
Source HTML and SHACL are snapshots of the official release, CC BY 4.0 EU.
"""
from pathlib import Path
from collections import defaultdict
from urllib.parse import urljoin
from html import escape
from bs4 import BeautifulSoup
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL, SKOS
from rdflib.compare import isomorphic
import json
P=Path(__file__).resolve().parent
SOURCE='https://semiceu.github.io/Core-Business-Vocabulary/releases/2.3.0/'
URL='https://jgmikael.github.io/docs/core-business/'
DC=Namespace('http://purl.org/dc/terms/'); FOAF=Namespace('http://xmlns.com/foaf/0.1/'); SC=Namespace('https://schema.org/'); SH=Namespace('http://www.w3.org/ns/shacl#')
soup=BeautifulSoup((P/'source-release-2.3.0.html').read_text(),'html.parser')
g=Graph().parse(P/'core-business-ap.ttl'); original=set(g)
shapes=Graph().parse(P/'source-shapes-2.3.0.ttl')
for p,n in {'cv':'http://data.europa.eu/m8g/','legal':'http://www.w3.org/ns/legal#','locn':'http://www.w3.org/ns/locn#','org':'http://www.w3.org/ns/org#','adms':'http://www.w3.org/ns/adms#','a4g':'http://data.europa.eu/a4g/ontology#','dct':str(DC)}.items():g.bind(p,Namespace(n))
def text(x):return x.get_text(' ',strip=True) if x else ''
def clean(x):
 if not x:return ''
 b=BeautifulSoup(x.decode_contents(),'html.parser')
 for t in list(b.find_all(True)):
  if t.name in ('script','style','img'):t.decompose();continue
  if t.name not in ('a','p','ul','ol','li','strong','em','code','br','b','i'):t.unwrap();continue
  href=t.get('href');t.attrs={}
  if t.name=='a' and href:
   u=urljoin(SOURCE,href)
   if u.startswith(('https://','http://')):t['href']=u
 return str(b).strip()
annex=[]
for row in soup.select('#quick-reference tbody tr'):
 t=row.find_all('td',recursive=False)
 if len(t)==5:
  annex.append({'class':text(t[1]),'classLabel':text(t[0]),'property':text(t[4]),'propertyLabel':text(t[3])})
class_uris={r['class'] for r in annex}; prop_uris={r['property'] for r in annex if r['property']}
classes={}; data={}; uses=defaultdict(list)
for h in soup.select('h3[id]'):
 a=h.find('a',href=True)
 if not a or a['href'] not in class_uris:continue
 u=a['href']; sec=h.find_parent('section');dl=h.find_next_sibling('dl')
 fields={' '.join(str(x).strip() for x in dt.find_all(string=True,recursive=False)).strip():dt.find_next('dd') for dt in dl.find_all('dt') if ''.join(dt.find_all(string=True,recursive=False)).strip()}
 parents=[]
 if fields.get('Subclass of'):
  for a2 in fields['Subclass of'].select('a[href]'):
   target=soup.find(id=a2['href'].lstrip('#'));pa=target.find('a',href=True) if target else None
   if pa:parents.append(pa['href'])
 classes[u]={'label':text(a),'definition':clean(fields.get('Definition')),'usage':clean(fields.get('Usage Note')),'parents':parents,'source':SOURCE+'#'+h['id']}
 for row in sec.select('tr[resource]'):
  t=row.find_all('td',recursive=False);p=row['resource']
  assert p in prop_uris
  ra=t[2].find('a',href=True);rid=ra['href'].lstrip('#') if ra else ''
  target=soup.find(id=rid);ruri=target.find('a',href=True)['href'] if target else None
  uses[p].append({'class':u,'label':text(t[1]),'range':ruri,'rangeLabel':text(t[2]),'cardinality':text(t[3]),'definition':clean(t[4]),'usage':clean(t[5]),'source':SOURCE+'#'+row['id']})
for name in ['Code','Date','Literal','Text','URI']:
 d=soup.find(id=name);a=d.find('a');u=a['href'];cells=d.find_parent('tr').find_all('td',recursive=False)
 data[u]={'label':name,'definition':clean(cells[1])}
assert set(classes)==class_uris and set(uses)==prop_uris
assert {(x['class'],p) for p,v in uses.items() for x in v}=={(r['class'],r['property']) for r in annex if r['property']}
# Describe all reused terms without promoting profile-specific constraints to global axioms.
for u,c in classes.items():
 s=URIRef(u);g.add((s,RDF.type,OWL.Class));g.add((s,RDFS.label,Literal(c['label'],lang='en')));g.add((s,DC.source,URIRef(c['source'])))
 if not list(g.objects(s,RDFS.comment)):g.add((s,RDFS.comment,Literal(BeautifulSoup(c['definition'],'html.parser').get_text(' ',strip=True),lang='en')))
 for parent in c['parents']:g.add((s,RDFS.subClassOf,URIRef(parent)))
for p,contexts in uses.items():
 s=URIRef(p)
 if not list(g.objects(s,RDF.type)):g.add((s,RDF.type,RDF.Property))
 for v in contexts:
  g.add((s,RDFS.label,Literal(v['label'],lang='en')));g.add((s,DC.source,URIRef(v['source'])))
 # A shared term can have different descriptions in different class contexts.
 # Those descriptions and constraints belong in the official SHACL, not global domain/range assertions.
 if len(contexts)==1 and not list(g.objects(s,RDFS.comment)):
  g.add((s,RDFS.comment,Literal(BeautifulSoup(contexts[0]['definition'],'html.parser').get_text(' ',strip=True),lang='en')))
for u,d in data.items():
 s=URIRef(u);g.add((s,RDFS.label,Literal(d['label'],lang='en')))
 g.add((s,RDF.type,OWL.Class if d['label']=='Code' else RDFS.Class if d['label']=='Literal' else RDFS.Datatype))
 if not list(g.objects(s,RDFS.comment)):g.add((s,RDFS.comment,Literal(BeautifulSoup(d['definition'],'html.parser').get_text(' ',strip=True),lang='en')))
# The local publication is a derived document, not a new EU ontology release.
g.add((URIRef(URL),DC.source,URIRef(SOURCE)));g.add((URIRef(URL),DC.license,URIRef('https://creativecommons.org/licenses/by/4.0/')))
def eid(u):return u.rsplit('/',1)[-1].rsplit('#',1)[-1]
labels={u:c['label'] for u,c in classes.items()}|{u:d['label'] for u,d in data.items()}|{p:' / '.join(dict.fromkeys(v['label'] for v in vs)) for p,vs in uses.items()}
assert len({eid(u) for u in labels})==len(labels)
def link(u,label=None):
 return '<a href="'+escape('#'+eid(u) if u in labels else u,quote=True)+'">'+escape(label or labels.get(u,u))+'</a>'
def uri(u):return '<a href="'+escape(u,quote=True)+'"><code>'+escape(u)+'</code></a>'
def table(headers,rows):return '<div class="table-wrap"><table class="def"><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+v+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def class_section(u):
 c=classes[u];entries=[(p,v) for p,vs in uses.items() for v in vs if v['class']==u]
 out='<section id="'+eid(u)+'"><h3>'+escape(c['label'])+'</h3><p>'+uri(u)+'</p><div>'+c['definition']+'</div>'
 if c['usage']:out+='<div class="scope"><p><strong>Usage note</strong></p>'+c['usage']+'</div>'
 if c['parents']:out+='<p><strong>Subclass of:</strong> '+', '.join(link(p) for p in c['parents'])+'</p>'
 out+='<p><a href="'+c['source']+'">Source: SEMIC Core Business 2.3.0</a></p>'
 if entries:out+=table(['Property','Range in this profile','Cardinality'],[[link(p,v['label']),link(v['range'],v['rangeLabel']),escape(v['cardinality'])] for p,v in entries])
 else:out+='<p>No properties are specified for this class in the release.</p>'
 return out+'</section>'
def prop_section(p):
 out='<section id="'+eid(p)+'"><h3>'+escape(labels[p])+'</h3><p>'+uri(p)+'</p>'
 asserted=[]
 for pred,name in [(RDF.type,'RDF type in uploaded file'),(RDFS.domain,'Global domain in uploaded file'),(RDFS.range,'Global range in uploaded file')]:
  vals=[o for s,pr,o in original if s==URIRef(p) and pr==pred]
  if vals:asserted.append([name,', '.join(link(str(v)) for v in vals)])
 if asserted:out+=table(['Original RDF assertion','Value'],asserted)
 for v in uses[p]:
  out+='<div class="scope"><p><strong>Usage on '+link(v['class'])+'</strong></p><div>'+v['definition']+'</div><p><strong>Profile range:</strong> '+link(v['range'],v['rangeLabel'])+' · <strong>Cardinality:</strong> '+escape(v['cardinality'])+'</p>'
  if v['usage']:out+='<div><strong>Usage note:</strong> '+v['usage']+'</div>'
  out+='<p><a href="'+v['source']+'">Source definition</a></p></div>'
 return out+'</section>'
ont=next(g.subjects(RDF.type,OWL.Ontology));editors=[]
for e in g.objects(ont,URIRef('http://www.w3.org/2001/02pd/rec54#editor')):
 editors.append({'name':' '.join(str(g.value(e,p) or '') for p in [FOAF.firstName,FOAF.lastName]).strip(),'company':str(g.value(g.value(e,SC.affiliation),FOAF.name) or '')})
config={'specStatus':'unofficial','shortName':'eu-core-business','thisVersion':URL,'latestVersion':URL,'editors':sorted(editors,key=lambda x:x['name']),'publishDate':'2026-10-14','license':'cc-by','doRDFa':False,'alternateFormats':[{'uri':'vocabulary.ttl','label':'Expanded Turtle'},{'uri':'vocabulary.jsonld','label':'Expanded JSON-LD'},{'uri':'source-shapes-2.3.0.ttl','label':'Official SHACL 2.3.0'}]}
html='''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EU Core Business Vocabulary</title><script class="remove" src="https://www.w3.org/Tools/respec/respec-w3c"></script><script class="remove">var respecConfig='''+json.dumps(config)+''';</script><style>body{font-family:system-ui,sans-serif;line-height:1.6;max-width:60em;margin:auto;padding:2em;color:#20252b}h1,h2,h3{color:#005a9c}a{color:#005a9c}code{overflow-wrap:anywhere}.table-wrap{overflow-x:auto}.def{border-collapse:collapse;width:100%;margin:1em 0}.def th,.def td{padding:.5em .8em;text-align:left;border-bottom:1px solid #ddd;vertical-align:top}.def th{background:#f4f6f8}.terms>section{border-bottom:1px solid #ccd4dc;padding-bottom:1.5em}.scope{border-left:3px solid #ccd4dc;padding-left:1em;margin:1em 0}.notice{background:#f2f6fa;padding:1em}</style></head><body>'''
html+='''<section id="abstract"><h2>Abstract</h2><p>This publication documents all 13 entity classes and 49 distinct properties listed in Annex A of EU Core Business Vocabulary 2.3.0, including 51 class–property usages and five supporting value types. It includes reused terms from Core Location, ADMS, W3C ORG, FOAF, SKOS and Dublin Core.</p></section><section id="sotd"><p class="notice">This is an unofficial documentation and RDF compilation based on <a href="'''+SOURCE+'''">SEMIC Core Business Vocabulary 2.3.0</a> (12 May 2026) and the supplied RDF. It is not a new official EU or W3C release. Source material: © 2026 European Union, CC BY 4.0. The source editors are credited above.</p><p>The original term IRIs are preserved. The uploaded Turtle remains available unchanged. The expanded RDF describes every Annex A term. Class-specific ranges, cardinalities and descriptions are documented as profile usages; they are not added as global RDFS domain/range axioms. The official SHACL is supplied separately for machine-readable profile constraints.</p></section>'''
html+='<section id="overview"><h2>Overview and downloads</h2><p><a href="vocabulary.ttl">Expanded Turtle</a> · <a href="vocabulary.jsonld">Expanded JSON-LD</a> · <a href="source-shapes-2.3.0.ttl">Official SHACL</a> · <a href="core-business-ap.ttl">Original uploaded Turtle</a> · <a href="build.py">Build script</a></p><p>Definitions and usage notes follow the official release. “Code” denotes the class skos:Concept; it is not an RDF literal datatype. Each property entry links to its original source definition.</p></section>'
html+='<section id="term-index"><h2>Term index</h2><h3>Classes</h3><ul>'+''.join('<li>'+link(u)+'</li>' for u in sorted(classes,key=lambda u:labels[u]))+'</ul><h3>Properties</h3><ul>'+''.join('<li>'+link(p)+' — <code>'+escape(g.namespace_manager.normalizeUri(URIRef(p)))+'</code></li>' for p in sorted(uses,key=lambda p:labels[p]))+'</ul></section>'
html+='<section class="terms" id="classes"><h2>Class definitions</h2>'+''.join(class_section(u) for u in sorted(classes,key=lambda u:labels[u]))+'</section>'
html+='<section class="terms" id="properties"><h2>Property definitions</h2>'+''.join(prop_section(p) for p in sorted(uses,key=lambda p:labels[p]))+'</section>'
html+='<section id="value-types"><h2>Supporting value types</h2>'+''.join('<section id="'+eid(u)+'"><h3>'+escape(d['label'])+'</h3><p>'+uri(u)+'</p>'+d['definition']+'</section>' for u,d in data.items())+'</section>'
html+='<section id="quick-reference" class="appendix"><h2>Quick reference of classes and properties</h2><p>All entries from <a href="'+SOURCE+'#quick-reference">Annex A of the official release</a>.</p>'+table(['Class','Class IRI','Property','Property IRI'],[[link(r['class']),uri(r['class']),link(r['property'],r['propertyLabel']) if r['property'] else '—',uri(r['property']) if r['property'] else '—'] for r in annex])+'</section></body></html>'
(P/'index.html').write_text(html)
g.serialize(P/'vocabulary.ttl',format='turtle');g.serialize(P/'vocabulary.jsonld',format='json-ld',indent=2)
assert len(list(g.triples((None,RDFS.subClassOf,None))))==3
assert original<=set(g)
assert isomorphic(g,Graph().parse(P/'vocabulary.jsonld',format='json-ld'))
# All Annex A terms are defined locally, and every profile usage exists in the official shapes.
for p,vs in uses.items():
 for v in vs:
  matches=[ps for ns in shapes.subjects(SH.targetClass,URIRef(v['class'])) for ps in shapes.objects(ns,SH.property) if shapes.value(ps,SH.path)==URIRef(p)]
  assert matches,(p,v['class'])
page=BeautifulSoup(html,'html.parser');ids=[x['id'] for x in page.select('[id]')];assert len(ids)==len(set(ids))
assert all(a['href'][1:] in ids for a in page.select('a[href^="#"]'))
report={'source':SOURCE,'classes':len(classes),'distinct_properties':len(uses),'class_property_usages':sum(map(len,uses.values())),'annex_rows':len(annex),'supporting_value_types':len(data),'expanded_triples':len(g),'original_triples_preserved':len(original),'annex_coverage':'complete','official_shacl_usage_coverage':'complete','rdf_serializations':'isomorphic','internal_links':'valid'}
(P/'coverage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
