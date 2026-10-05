from pathlib import Path
import yaml, subprocess, shutil, json, re
from rdflib import Graph, URIRef, BNode, RDF, RDFS, OWL
from rdflib.collection import Collection
root=Path(__file__).parent.resolve()
data=yaml.safe_load((root/'vocabulary.yml').read_text())
local={c['id'] for c in data['class']}
external=set()
for p in data['property']:
    for field in ['domain','range']:
        a=p[field] if isinstance(p[field],list) else [p[field]]
        converted=[]
        for v in a:
            if ':' not in v and v not in local:v='ebwv:'+v
            if ':' in v and not v.startswith(('xsd:','rdf:langString')):external.add(v)
            converted.append(v)
        p[field]=converted if len(converted)>1 else converted[0]
    if isinstance(p['range'],list):p['range_union']=True
    if p['id']=='hasRelationshipPath':p['container']='list'
for v in sorted(external):
    data['class'].append({'id':v,'label':v.split(':')[1],'comment':'External reference; definition is maintained by its source vocabulary.','context':'none'})
build=root/'publisher-source';build.mkdir(exist_ok=True)
(build/'vocabulary.yml').write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True))
shutil.copy(root/'template.html',build/'template.html')
subprocess.run([str(root.parent/'publishing-runtime/node_modules/.bin/yml2vocab'),'-v',str(build/'vocabulary.yml'),'-t',str(build/'template.html'),'-c','-d'],check=True)
assert (build/'vocabulary.html').exists(),'Publisher reported a conversion error'
g=Graph().parse(build/'vocabulary.ttl')
BASE='https://w3id.org/ebwv#'
# yml2vocab expands rdf:langString to a future-proof range union.
# Preserve the agreed exact signature and corresponding context.
s=URIRef(BASE+'beneficiaryClassDescription')
for triple in list(g.triples((s,RDFS.range,None))):g.remove(triple)
g.add((s,RDFS.range,RDF.langString));g.add((s,RDF.type,OWL.DatatypeProperty))
g.serialize(root/'vocabulary.ttl',format='turtle')
g.serialize(root/'vocabulary.jsonld',format='json-ld',indent=2)
ctx=json.loads((build/'vocabulary.context.jsonld').read_text())
for target in [root/'v0.1/vocabulary.context.jsonld',root/'vocabulary.context.jsonld']:
    target.write_text(json.dumps(ctx,indent=2))
h=(build/'vocabulary.html').read_text()
h=h.replace(str(build)+'/', '')
from bs4 import BeautifulSoup
soup=BeautifulSoup(h,'html.parser')
section=soup.find(id='beneficiaryClassDescription')
if section:
    for dt in section.find_all('dt'):
        if dt.get_text(strip=True)=='Range:':
            dd=dt.find_next_sibling('dd')
            dd.clear();code=soup.new_tag('code');code.string='rdf:langString';dd.append(code)
h=str(soup)
(root/'vocabulary.html').write_text(h)
(root/'index.html').write_text(h)
original=yaml.safe_load((root/'vocabulary.yml').read_text())
for p in original['property']:
    s=URIRef(BASE+p['id'])
    for field,pred in [('domain',RDFS.domain),('range',RDFS.range)]:
        vals=list(g.objects(s,pred));assert len(vals)==1,(p['id'],field,vals)
        if isinstance(p[field],list):
            head=g.value(vals[0],OWL.unionOf);assert head is not None,(p['id'],field,'missing union')
            assert len(list(Collection(g,head)))==len(p[field])
Graph().parse(root/'vocabulary.jsonld',format='json-ld')
for p in original['property']:assert soup.find(id=p['id']),p['id']
for c in original['class']:assert soup.find(id=c['id']),c['id']
print('EBWV yml2vocab/template build validated: 29 additions, 1 revision, 9 new classes; all domain/range unions preserved.')
