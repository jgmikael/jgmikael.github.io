"""Generate fictional, unsigned ownership content, SHACL profiles and reading views."""
from pathlib import Path
import json, base64, html, zipfile, copy
from datetime import datetime, timezone
import yaml
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS, SKOS
from rdflib.collection import Collection
from pyshacl import validate

ROOT = Path(__file__).parent
E = Namespace('https://w3id.org/ebwv#')
A = Namespace('https://jgmikael.github.io/docs/ownership-attestations/profile#')
C = Namespace('https://www.w3.org/2018/credentials#')
D = Namespace('urn:example:ownership:')
SH = Namespace('http://www.w3.org/ns/shacl#')
RB = 'https://github.com/webuild-consortium/webuild-attestation-rulebooks-catalog/blob/5c9ace01b674ca302f1dd5cc03e58b54c6dd32b5/rulebooks/rb-ownership/README.md'
ORIGINAL = 'https://github.com/webuild-consortium/wp4-semantics-group/blob/a2306846c73de3272321bd82e3d83b3051f45f17/vocab/src/vocabulary.yml'
LAOC = 'https://jgmikael.github.io/docs/ebwv-ownership/'
CONTEXT = {'ebwv':str(E), 'oa':str(A), 'cred':str(C), 'dct':str(DCTERMS), 'rdfs':str(RDFS), 'skos':str(SKOS), 'xsd':str(XSD)}
def text(v): return Literal(v)
def date(v): return Literal(v, datatype=XSD.date)
def code(v): return A[v]
def add(g,s,p,o): g.add((s,p,o)); return o
def label(g,s,v): add(g,s,RDFS.label,text(v))
def graph():
    g=Graph()
    for k,v in CONTEXT.items(): g.bind(k,Namespace(v))
    return g
def address(g, node, number='1', town='Helsinki', country='FI'):
    add(g,node,RDF.type,E.Address)
    for p,v in [(E.thoroughfare,'Example Street'),(E.locatorDesignator,number),(E.postName,town),(E.adminUnitL2,'Example Region'),(E.postCode,'00100')]: add(g,node,p,text(v))
    add(g,node,E.adminUnitL1,Literal(country,datatype=E.CountryCode))
    return node
def person(g,slug,first,last,birth):
    n=D[slug]; add(g,n,RDF.type,E.NaturalPerson); label(g,n,first+' '+last)
    add(g,n,E.givenName,text(first)); add(g,n,E.familyName,text(last)); add(g,n,E.dateOfBirth,date(birth))
    add(g,n,E.domicile,address(g,D[slug+'-address']))
    return n
def company(g,slug,name):
    n=D[slug]
    for t in [E.LegalPerson,E.Company,E.EconomicOperator]: add(g,n,RDF.type,t)
    label(g,n,name); add(g,n,E.legalName,text(name)); add(g,n,E.legalForm,text('Private limited company'))
    add(g,n,E.legalIdentifier,Literal('FI.DEMO.'+slug.upper(),datatype=E.Euid))
    add(g,n,E.identifier,text('DEMO-'+slug.upper())); add(g,n,E.jurisdiction,Literal('FI',datatype=E.CountryCode))
    add(g,n,E.registeredAddress,address(g,D[slug+'-address']))
    add(g,n,A.entityForm,code('private_company'))
    return n
def period(g,slug,start='2026-09-01'):
    n=D[slug+'-period']; add(g,n,RDF.type,E.PeriodOfTime); add(g,n,E.startDate,date(start)); return n
def evidence(g,slug,title,kind,content):
    n=D[slug]; add(g,n,RDF.type,A.Evidence); label(g,n,title)
    add(g,n,DCTERMS.identifier,text('DEMO-'+slug.upper())); add(g,n,A.evidenceType,code(kind))
    content='FICTIONAL DEMONSTRATION DOCUMENT — NOT AN AUTHENTIC REGISTER OR LEGAL INSTRUMENT.\n\n'+content
    add(g,n,A.evidenceData,Literal(base64.b64encode(content.encode()).decode(),datatype=XSD.base64Binary))
    add(g,n,DCTERMS.description,text(content)); return n
def instrument(g,slug,title,kind,content):
    n=evidence(g,slug,title,kind,content); add(g,n,RDF.type,E.LegalInstrument); return n
def relation(g,slug,holder,target,title,types,level='direct',pct=None,quantity=None,rights=(),basis=None,ev=None,start='2026-09-01',kind='legalTitle',mode='alone'):
    n=D[slug]; add(g,n,RDF.type,E.OwnershipOrControlRelationship); label(g,n,title)
    add(g,n,E.rightHolder,holder); add(g,n,E.relationshipTarget,target); add(g,n,E.relationshipType,code(kind))
    add(g,n,A.level,code(level)); add(g,n,E.exerciseMode,code(mode)); add(g,n,E.effectivePeriod,period(g,slug,start))
    for t in types: add(g,n,A.interestType,code(t))
    if pct is not None: add(g,n,E.ownershipPercentage,Literal(str(pct),datatype=XSD.decimal))
    if quantity is not None: add(g,n,A.shareQuantity,Literal(quantity,datatype=XSD.integer))
    if quantity is not None: add(g,n,A.shareClass,code('ordinary'))
    for r in rights: add(g,n,A.economicRight,code(r))
    if basis: add(g,n,E.establishedUnder,basis)
    if ev: add(g,n,E.supportedBy,ev)
    return n
def record(g,att,slug,party,rel,ev,kind='Person'):
    n=D[slug]; add(g,n,RDF.type,A.OwnerRecord); add(g,att,A.ownerRecord,n)
    add(g,n,A.ownerType,text(kind)); add(g,n,A.party,party); add(g,n,A.interest,rel)
    add(g,n,A.ownerJurisdiction,text('FI')); add(g,n,A.evidence,ev)
    add(g,n,A.effectiveDate,next(g.objects(next(g.objects(rel,E.effectivePeriod)),E.startDate)))
    return n
def attestation(g,slug,subject,title):
    n=D[slug]
    for t in [A.OwnershipAttestation,E.ElectronicAttestationOfAttributes,C.VerifiableCredential]: add(g,n,RDF.type,t)
    label(g,n,title); add(g,n,C.credentialSubject,subject); add(g,n,C.issuer,subject)
    add(g,n,E.attestationLegalCategory,E.EAA)
    add(g,n,C.validFrom,Literal('2026-10-05T09:00:00Z',datatype=XSD.dateTime))
    add(g,n,C.validUntil,Literal('2026-11-04T09:00:00Z',datatype=XSD.dateTime))
    add(g,n,A.assessedOn,date('2026-10-05')); add(g,n,A.contentStatus,code('fictionalUnsigned'))
    add(g,n,A.credentialType,text('eu.we-build:ownership:1')); add(g,n,A.holderKeyReference,D['placeholder-public-key'])
    status=D[slug+'-status']; add(g,n,A.status,status); add(g,status,RDF.type,A.StatusReference)
    add(g,status,A.statusList,URIRef('https://issuer.example/status/demo')); add(g,status,A.statusIndex,Literal(0,datatype=XSD.integer)); add(g,status,A.statusPurpose,text('revocation'))
    return n
ECON=('dividend_rights','liquidation_rights')

examples=[]
g=graph(); subject=company(g,'northstar','Northstar Workshop Oy'); att=attestation(g,'direct-attestation',subject,'Direct share ownership')
p1=person(g,'aino','Aino','Kallio','1984-04-12'); p2=person(g,'mikko','Mikko','Laine','1980-11-08')
ev=evidence(g,'northstar-register','Shareholder register — Northstar','officialRegister','As at 5 October 2026: 1,000 ordinary shares issued. Aino Kallio holds 600; Mikko Laine holds 400. One vote and equal economic rights per share.')
for slug,p,pct,qty in [('aino-direct',p1,60,600),('mikko-direct',p2,40,400)]:
    r=relation(g,slug,p,subject,f'{pct}% ordinary shares',['shareholding','votingRights'],pct=pct,quantity=qty,rights=ECON,ev=ev)
    add(g,r,E.votingRightsPercentage,Literal(str(pct),datatype=XSD.decimal)); record(g,att,slug+'-record',p,r,ev)
examples.append(dict(slug='direct-shares',g=g,att=att,title='A straightforward share register',subtitle='Two people own all 1,000 ordinary shares.',tag='01 · Direct shares',summary='Aino owns 60% and Mikko owns 40% of Northstar Workshop Oy. Share ownership, votes and economic rights coincide in this example.',takeaway='These are current, direct rights in the company. The attestation reports the register; it does not turn the issuer’s statement into independent verification.',facts=[('Issued by','Northstar Workshop Oy, about its own ownership'),('Company capital','1,000 ordinary shares · one vote per share'),('Direct shares accounted for','100% · 1,000 of 1,000 shares')],story=[],scope='Complete direct share register; no indirect holdings are asserted.',strict=True))

g=graph(); subject=company(g,'baltic-parts','Baltic Parts Oy'); holding=company(g,'kallio-holding','Kallio Holding Oy'); att=attestation(g,'indirect-attestation',subject,'Direct and indirect share ownership')
aino=person(g,'aino','Aino','Kallio','1984-04-12'); omar=person(g,'omar','Omar','Niemi','1987-03-02'); leena=person(g,'leena','Leena','Salo','1978-09-21')
ev=evidence(g,'baltic-register','Shareholder register — Baltic Parts','officialRegister','Baltic Parts Oy has 1,000 ordinary shares. Kallio Holding Oy owns 600 and Leena Salo owns 400.')
evh=evidence(g,'holding-register','Shareholder register — Kallio Holding','officialRegister','Kallio Holding Oy has 100 ordinary shares. Aino Kallio owns 50 and Omar Niemi owns 50. Equal economic rights; no other intermediate entities.')
rhc=relation(g,'holding-to-baltic',holding,subject,'60% direct shares',['shareholding'],pct=60,quantity=600,rights=ECON,ev=ev)
record(g,att,'holding-record',holding,rhc,ev,'Entity')
rl=relation(g,'leena-to-baltic',leena,subject,'40% direct shares',['shareholding'],pct=40,quantity=400,rights=ECON,ev=ev); record(g,att,'leena-record',leena,rl,ev)
for slug,p in [('aino',aino),('omar',omar)]:
    rp=relation(g,slug+'-to-holding',p,holding,'50% of the holding company',['shareholding'],pct=50,quantity=50,rights=ECON,ev=evh)
    ri=relation(g,slug+'-indirect-baltic',p,subject,'30% indirect economic ownership',['shareholding'],level='indirect',pct=30,quantity=300,rights=ECON,ev=evh,kind='economicEntitlement')
    add(g,ri,A.quantityMeaning,text('Equivalent economic units: 50% × 600 shares. Not 300 registered shares in the person’s name.'))
    add(g,ri,A.calculation,text('50% × 60% = 30%')); head=BNode(); Collection(g,head,[rp,rhc]); add(g,ri,E.hasRelationshipPath,head); record(g,att,slug+'-indirect-record',p,ri,evh)
examples.append(dict(slug='indirect-shares',g=g,att=att,title='Ownership through a holding company',subtitle='Follow each person’s interest through an intermediary.',tag='02 · Indirect shares',summary='Kallio Holding owns 60% of Baltic Parts. Aino and Omar each own half of Kallio Holding, giving each a 30% indirect economic interest in Baltic Parts. Leena owns the remaining 40% directly.',takeaway='The 60% holding-company stake and the two 30% indirect interests describe the same shares at different levels. Adding them together would count the shares twice. Multiplication here establishes economic ownership, not an automatic conclusion about control.',facts=[('Direct share register','Kallio Holding 60% · Leena Salo 40%'),('Look-through economic view','Aino 30% · Omar 30% · Leena 40%'),('Calculation basis','Equal economic rights at both levels')],story=[('Aino → Kallio Holding → Baltic Parts','50% × 60% = 30%'),('Omar → Kallio Holding → Baltic Parts','50% × 60% = 30%')],scope='Complete direct register and one-level economic look-through. Indirect quantities are equivalents, not registered holdings.',strict=True))

g=graph(); subject=company(g,'harbour-robotics','Harbour Robotics Oy'); trustee=company(g,'meridian-trustees','Meridian Trustees Oy'); att=attestation(g,'trust-attestation',subject,'Share ownership and trust economic entitlement')
elina=person(g,'elina','Elina','Virta','1990-06-15'); settlor=person(g,'jukka','Jukka','Virta','1956-07-09'); protector=person(g,'kaisa','Kaisa','Ranta','1977-02-18')
trust=D['virta-trust']; add(g,trust,RDF.type,E.LegalArrangement); add(g,trust,RDF.type,E.ExpressTrust); label(g,trust,'Virta Family Trust')
add(g,trust,E.arrangementType,code('expressTrust')); add(g,trust,E.governingLaw,URIRef('https://www.legislation.gov.uk/ukpga/2000/29/contents'))
add(g,trust,DCTERMS.description,text('Administer the specified share block for Elina’s fixed economic entitlement. A fictional English-law express trust; Finnish company and trustee identities are illustrative only.'))
add(g,trust,A.arrangementJurisdiction,text('GB')); add(g,trust,A.arrangementForm,code('trust')); add(g,trust,A.administrationAddress,address(g,D['trust-address'],'2','London','GB')); add(g,trust,E.effectivePeriod,period(g,'trust','2025-01-01'))
deed=instrument(g,'virta-deed','Virta Family Trust deed · clauses 3, 5 and 8','trustDeed','Fictional deed: Jukka settled a 600-share block. Meridian holds legal title as trustee. Elina has a fixed entitlement to all distributions attributable to that block. Kaisa may remove the trustee under clause 8; this is not personal title to the block.')
add(g,trust,E.constitutedBy,deed)
asset=D['harbour-share-block']; add(g,asset,RDF.type,E.Asset); label(g,asset,'600 ordinary shares in Harbour Robotics Oy'); add(g,asset,DCTERMS.description,text('The trust property is a specified 600-share block, representing 60% of the company’s 1,000 ordinary shares.'))
add(g,trust,E.arrangementAsset,asset)
participations={}
for slug,p,role in [('settlor',settlor,'settlor'),('trustee',trustee,'trustee'),('beneficiary',elina,'beneficiaryOfLegalArrangement'),('protector',protector,'protector')]:
    n=D['trust-'+slug]; add(g,n,RDF.type,E.ArrangementParticipation); add(g,trust,E.hasParticipation,n); add(g,n,E.participatingParty,p); add(g,n,E.participationRole,code(role)); add(g,n,E.effectivePeriod,period(g,'trust-'+slug,'2025-01-01')); participations[slug]=n
ev=evidence(g,'harbour-register','Shareholder register — Harbour Robotics','officialRegister','1,000 ordinary shares issued. Meridian Trustees Oy is registered for 600 as trustee of Virta Family Trust. Elina Virta personally owns 400 separately.')
rt=relation(g,'trustee-company-title',trustee,subject,'60% legal title held as trustee',['shareholding','trustee'],pct=60,quantity=600,rights=ECON,basis=trust,ev=ev,start='2025-01-01'); add(g,rt,E.supportingParticipation,participations['trustee']); add(g,rt,A.capacityNote,text('Holds the 600 shares in trustee capacity. Economic proceeds are administered for Elina; they are not Meridian’s own benefit.')); record(g,att,'trustee-owner-record',trustee,rt,ev,'Entity')
ra=relation(g,'trustee-asset-title',trustee,asset,'Legal title to the entire specified share block',['trustee'],basis=trust,ev=deed,start='2025-01-01'); add(g,ra,E.supportingParticipation,participations['trustee'])
re=relation(g,'elina-direct-harbour',elina,subject,'40% personal share ownership',['shareholding'],pct=40,quantity=400,rights=ECON,ev=ev); record(g,att,'elina-direct-record',elina,re,ev)
rb=relation(g,'elina-trust-benefit',elina,subject,'60% economic entitlement through the trust',['beneficiaryOfLegalArrangement','economicBeneficiary'],level='indirect',rights=ECON,basis=trust,ev=deed,start='2025-01-01',kind='economicEntitlement')
add(g,rb,E.economicEntitlementPercentage,Literal('60',datatype=XSD.decimal)); add(g,rb,E.supportingParticipation,participations['beneficiary']); add(g,rb,A.capacityNote,text('All distributions from the 600-share block. No personal registered share title to this block. No personal share-ownership percentage or registered share quantity is claimed for this beneficiary right.')); record(g,att,'elina-beneficiary-record',elina,rb,deed)
examples.append(dict(slug='trust-arrangement',g=g,att=att,title='A trust separates title from benefit',subtitle='A company holds the shares; a person receives their economic benefit.',tag='03 · Trust arrangement',summary='Meridian Trustees holds 600 shares for the Virta Family Trust. Elina owns another 400 shares personally and is entitled to the economic benefit of the trust’s block. The trust deed connects the participants, asset and distinct rights.',takeaway='Elina has 40% personal share ownership plus 60% economic entitlement through the trust. Meridian’s 60% legal-title holding is the same trust share block, not another 60% of economic ownership. Settlor and protector roles do not themselves assert personal title to the shares.',facts=[('Direct share register','Meridian Trustees in trustee capacity 60% · Elina personally 40%'),('Economic benefit','Elina: 40% direct + 60% trust entitlement'),('Trust property','A specifically identified block of 600 ordinary shares')],story=[],scope='Direct register, fixed trust economic entitlement and named trust participants. No automatic UBO determination is asserted.',strict=False))

g=graph(); subject=company(g,'aurora-machines','Aurora Machines Oy'); att=attestation(g,'conditional-attestation',subject,'Share ownership with a conditional governance power')
sanna=person(g,'sanna','Sanna','Aalto','1985-01-30'); jari=person(g,'jari','Jari','Koski','1981-05-04'); kaisa=person(g,'kaisa','Kaisa','Ranta','1977-02-18')
ev=evidence(g,'aurora-register','Shareholder register — Aurora Machines','officialRegister','1,000 ordinary shares issued. Sanna Aalto owns 700; Jari Koski owns 300. Kaisa Ranta owns no shares.')
for slug,p,pct,qty in [('sanna',sanna,70,700),('jari',jari,30,300)]:
    r=relation(g,slug+'-aurora-shares',p,subject,f'{pct}% direct shares',['shareholding'],pct=pct,quantity=qty,rights=ECON,ev=ev); record(g,att,slug+'-record',p,r,ev)
agreement=instrument(g,'aurora-agreement','Governance agreement · clause 12','shareholderAgreement','Clause 12: Kaisa may appoint two of three directors only after an uncured payment default and written consent of the lender. At assessment no default has occurred and no consent has been given. The clause conveys no share title or economic distribution rights.')
r=relation(g,'kaisa-appointment',kaisa,subject,'Conditional power to appoint two of three directors',['appointmentOfBoard','conditionalRightsGrantedByContract'],level='direct',basis=agreement,ev=agreement,kind='appointmentPower',mode='subjectToConsent')
cond=D['appointment-condition']; add(g,cond,RDF.type,E.RelationshipCondition); add(g,r,E.conditions,cond)
add(g,cond,A.trigger,text('Uncured payment default under clause 12')); add(g,cond,A.consentRequired,text('Written consent of the lender')); add(g,cond,A.conditionSatisfied,Literal(False)); add(g,cond,A.assessedOn,date('2026-10-05'))
add(g,r,A.powerState,code('contingent')); add(g,r,A.capacityNote,text('No ownership percentage, share quantity, dividend or liquidation rights. Power is not currently exercisable.')); record(g,att,'kaisa-power-record',kaisa,r,agreement)
examples.append(dict(slug='conditional-control',g=g,att=att,title='A control power without share ownership',subtitle='A legal instrument grants a power that is not yet exercisable.',tag='04 · Conditional control',summary='Sanna and Jari own all shares. Kaisa has a contractual right to appoint two directors only if a payment default remains uncured and the lender gives written consent. Neither condition is met at the assessment date.',takeaway='Kaisa’s potential appointment power is not a share percentage. Recording 0% ownership would not describe the power; recording 100% would misstate it. The attestation identifies the condition and shows the power as contingent.',facts=[('Direct share register','Sanna 70% · Jari 30%'),('Appointment right','Two of three directors, subject to clause 12'),('Current position','Conditions not satisfied · power not exercisable')],story=[],scope='Complete direct share register plus one contingent contractual power. The shareholder agreement is a legal instrument; it is not assumed to be an AML legal arrangement.',strict=False))

# Profile terms are explicitly local: they do not silently add terms to EBWV.
vocab=graph()
classes=['OwnershipAttestation','OwnerRecord','Evidence','StatusReference']
props=['ownerRecord','party','interest','ownerType','ownerJurisdiction','effectiveDate','evidence','evidenceType','evidenceData','evidenceUrl','entityForm','level','interestType','shareQuantity','shareClass','economicRight','calculation','quantityMeaning','capacityNote','assessedOn','contentStatus','credentialType','holderKeyReference','status','statusList','statusIndex','statusPurpose','arrangementJurisdiction','arrangementForm','administrationAddress','trigger','consentRequired','conditionSatisfied','powerState']
for c in classes: add(vocab,A[c],RDF.type,RDFS.Class)
for p in props: add(vocab,A[p],RDF.type,RDF.Property)
terms={
 'InterestType':['shareholding','nomineeShareholding','votingRights','appointmentOfBoard','otherInfluenceOrControl','seniorManagingOfficial','settlor','trustee','protector','beneficiaryOfLegalArrangement','rightsGrantedByContract','conditionalRightsGrantedByContract','economicBeneficiary','controlViaCompanyRulesOrArticles','controlByLegalFramework'],
 'Level':['direct','indirect','joint','unknown'], 'EconomicRight':['dividend_rights','liquidation_rights'],
 'ShareClass':['ordinary','preferred','dual-class','other'],
 'EntityForm':['private_company','public_company','partnership','limited_partnership','trust','foundation','cooperative','state_owned_enterprise','other'],
 'EvidenceType':['officialRegister','selfDeclaration','thirdPartyVerification','trustDeed','shareholderAgreement','articlesOfAssociation','governanceChart'],
 'RelationshipType':['legalTitle','economicEntitlement','appointmentPower'],
 'ExerciseMode':['alone','jointly','subjectToConsent'], 'ArrangementType':['expressTrust'],
 'PowerState':['contingent','exercisable'], 'ContentStatus':['fictionalUnsigned']}
for scheme,values in terms.items():
    add(vocab,A[scheme],RDF.type,SKOS.ConceptScheme)
    for v in values:
        add(vocab,code(v),RDF.type,SKOS.Concept); add(vocab,code(v),SKOS.inScheme,A[scheme]); label(vocab,code(v),v)
add(vocab,A.ownershipProfile,RDF.type,RDFS.Resource); add(vocab,A.ownershipProfile,DCTERMS.source,URIRef(RB))
vocab.serialize(ROOT/'profile-vocabulary.ttl',format='turtle')

# Shapes validate the semantic content projection, not JWT signatures or wire arrays.
prefix='''@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ebwv: <https://w3id.org/ebwv#> .
@prefix oa: <https://jgmikael.github.io/docs/ownership-attestations/profile#> .
@prefix cred: <https://www.w3.org/2018/credentials#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
'''
def prop(path,extra): return f'[ sh:path {path}; {extra} ]'
def enum(values): return '( '+' '.join('oa:'+v for v in values)+' )'
def single(dtype): return f'sh:minCount 1; sh:maxCount 1; sh:datatype {dtype}'
shape=prefix+'''
oa:AttestationShape a sh:NodeShape; sh:targetClass oa:OwnershipAttestation;
 sh:property [ sh:path oa:ownerRecord; sh:minCount 1; sh:node oa:OwnerRecordShape; sh:message "IR-01: at least one owner record" ];
 sh:property [ sh:path oa:ownerRecord; sh:qualifiedValueShape [ sh:property [ sh:path oa:ownerType; sh:hasValue "Person" ] ]; sh:qualifiedMinCount 1; sh:message "IR-02: at least one natural-person record (Rulebook design choice)" ];
 sh:property [ sh:path cred:credentialSubject; sh:minCount 1; sh:maxCount 1; sh:class ebwv:LegalPerson ];
 sh:property [ sh:path cred:issuer; sh:minCount 1; sh:maxCount 1; sh:class ebwv:EconomicOperator ];
 sh:property [ sh:path ebwv:attestationLegalCategory; sh:hasValue ebwv:EAA; sh:maxCount 1 ];
 sh:property [ sh:path cred:validFrom; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:dateTime ];
 sh:property [ sh:path cred:validUntil; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:dateTime ];
 sh:property [ sh:path oa:assessedOn; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:date ];
 sh:property [ sh:path oa:holderKeyReference; sh:minCount 1; sh:maxCount 1; sh:nodeKind sh:IRI ];
 sh:property [ sh:path oa:credentialType; sh:hasValue "eu.we-build:ownership:1"; sh:maxCount 1 ];
 sh:property [ sh:path oa:status; sh:minCount 1; sh:maxCount 1; sh:node oa:StatusShape ];
 sh:sparql [ sh:message "Credential validity must end after issuance."; sh:select """
 PREFIX cred: <https://www.w3.org/2018/credentials#>
 SELECT $this WHERE { $this cred:validFrom ?from; cred:validUntil ?until . FILTER (?until <= ?from) } """ ].
oa:StatusShape a sh:NodeShape;
 sh:property [ sh:path oa:statusList; sh:minCount 1; sh:maxCount 1; sh:nodeKind sh:IRI ];
 sh:property [ sh:path oa:statusIndex; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:integer; sh:minInclusive 0 ];
 sh:property [ sh:path oa:statusPurpose; sh:hasValue "revocation"; sh:maxCount 1 ].
oa:OwnerRecordShape a sh:NodeShape; sh:targetClass oa:OwnerRecord;
 sh:property [ sh:path oa:ownerType; sh:minCount 1; sh:maxCount 1; sh:in ("Person" "Entity") ];
 sh:property [ sh:path oa:party; sh:minCount 1; sh:maxCount 1; sh:nodeKind sh:IRI ];
 sh:xone (
  [ sh:property [ sh:path oa:ownerType; sh:hasValue "Person" ]; sh:property [ sh:path oa:party; sh:class ebwv:NaturalPerson; sh:not [ sh:class ebwv:LegalPerson ]; sh:node oa:PersonShape ] ]
  [ sh:property [ sh:path oa:ownerType; sh:hasValue "Entity" ]; sh:property [ sh:path oa:party; sh:not [ sh:class ebwv:NaturalPerson ]; sh:or ( [ sh:class ebwv:LegalPerson; sh:node oa:EntityShape ] [ sh:class ebwv:LegalArrangement; sh:node oa:ArrangementShape ] ) ] ]
 );
 sh:property [ sh:path oa:ownerJurisdiction; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:string; sh:in ("FI" "GB"); sh:message "IR-18: demo country subset of ISO 3166-1 alpha-2" ];
 sh:property [ sh:path oa:interest; sh:minCount 1; sh:class ebwv:OwnershipOrControlRelationship; sh:node oa:InterestShape ];
 sh:property [ sh:path oa:effectiveDate; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:date; sh:message "IR-17/21: effective date" ];
 sh:property [ sh:path oa:evidence; sh:minCount 1; sh:node oa:EvidenceShape; sh:message "IR-13: evidence required" ];
 sh:sparql [ sh:message "The owner-record party must be the holder of every asserted interest."; sh:select """
 PREFIX oa: <https://jgmikael.github.io/docs/ownership-attestations/profile#>
 PREFIX ebwv: <https://w3id.org/ebwv#>
 SELECT $this WHERE { $this oa:party ?party; oa:interest ?r . ?r ebwv:rightHolder ?h . FILTER (?party != ?h) } """ ];
 sh:sparql [ sh:message "Owner effective date and relationship start date must agree."; sh:select """
 PREFIX oa: <https://jgmikael.github.io/docs/ownership-attestations/profile#>
 PREFIX ebwv: <https://w3id.org/ebwv#>
 SELECT $this WHERE { $this oa:effectiveDate ?d; oa:interest ?r . ?r ebwv:effectivePeriod/ebwv:startDate ?s . FILTER (?d != ?s) } """ ].
oa:PersonShape a sh:NodeShape;
 sh:property [ sh:path ebwv:givenName; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:string; sh:minLength 1 ];
 sh:property [ sh:path ebwv:familyName; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:string; sh:minLength 1 ];
 sh:property [ sh:path ebwv:dateOfBirth; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:date ];
 sh:property [ sh:path ebwv:domicile; sh:minCount 1; sh:maxCount 1; sh:class ebwv:Address; sh:node oa:AddressShape ].
oa:EntityShape a sh:NodeShape;
 sh:property [ sh:path ebwv:legalName; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:string; sh:minLength 1 ];
 sh:property [ sh:path ebwv:legalIdentifier; sh:minCount 1; sh:maxCount 1; sh:datatype ebwv:Euid; sh:minLength 1 ];
 sh:property [ sh:path ebwv:identifier; sh:minCount 1; sh:or ( [ sh:datatype xsd:string; sh:minLength 1 ] [ sh:datatype ebwv:Lei ] [ sh:datatype ebwv:Tin ] ) ];
 sh:property [ sh:path ebwv:jurisdiction; sh:minCount 1; sh:maxCount 1; sh:datatype ebwv:CountryCode; sh:in ("FI"^^ebwv:CountryCode "GB"^^ebwv:CountryCode) ];
 sh:property [ sh:path ebwv:legalForm; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:string; sh:minLength 1 ];
 sh:property [ sh:path ebwv:registeredAddress; sh:minCount 1; sh:maxCount 1; sh:node oa:AddressShape ].
oa:ArrangementShape a sh:NodeShape; sh:targetClass ebwv:LegalArrangement;
 sh:property [ sh:path rdfs:label; sh:minCount 1; sh:datatype xsd:string; sh:minLength 1 ];
 sh:property [ sh:path ebwv:constitutedBy; sh:minCount 1; sh:class ebwv:LegalInstrument; sh:node oa:EvidenceShape; sh:message "IR-05: settlement instrument" ];
 sh:property [ sh:path dct:description; sh:minCount 1; sh:datatype xsd:string; sh:minLength 1; sh:message "IR-05: declared arrangement purpose" ];
 sh:property [ sh:path ebwv:arrangementAsset; sh:minCount 1; sh:class ebwv:Asset; sh:message "IR-05: identified arrangement assets" ];
 sh:property [ sh:path oa:arrangementJurisdiction; sh:minCount 1; sh:maxCount 1; sh:in ("FI" "GB") ];
 sh:property [ sh:path oa:administrationAddress; sh:minCount 1; sh:node oa:AddressShape ];
 sh:property [ sh:path ebwv:hasParticipation; sh:minCount 1; sh:class ebwv:ArrangementParticipation ].
oa:EvidenceShape a sh:NodeShape; sh:targetClass oa:Evidence;
 sh:property [ sh:path dct:identifier; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:string; sh:minLength 1; sh:message "IR-14: evidence identifier" ];
 sh:property [ sh:path oa:evidenceData; sh:datatype xsd:base64Binary ];
 sh:property [ sh:path oa:evidenceUrl; sh:nodeKind sh:IRI ];
 sh:or ( [ sh:property [ sh:path oa:evidenceData; sh:minCount 1 ] ] [ sh:property [ sh:path oa:evidenceUrl; sh:minCount 1 ] ] ).
oa:RelationshipShape a sh:NodeShape; sh:targetClass ebwv:OwnershipOrControlRelationship;
 sh:property [ sh:path ebwv:rightHolder; sh:minCount 1; sh:maxCount 1; sh:or ( [ sh:class ebwv:NaturalPerson ] [ sh:class ebwv:LegalPerson ] [ sh:class ebwv:EconomicOperator ] ) ];
 sh:property [ sh:path ebwv:relationshipTarget; sh:minCount 1; sh:maxCount 1; sh:or ( [ sh:class ebwv:Asset ] [ sh:class ebwv:LegalPerson ] [ sh:class ebwv:EconomicOperator ] [ sh:class ebwv:LegalArrangement ] ) ];
 sh:property [ sh:path ebwv:effectivePeriod; sh:minCount 1; sh:maxCount 1; sh:node oa:PeriodShape ];
 sh:property [ sh:path ebwv:supportedBy; sh:minCount 1; sh:node oa:EvidenceShape ];
 sh:property [ sh:path ebwv:ownershipPercentage; sh:maxCount 1; sh:datatype xsd:decimal; sh:minInclusive 0; sh:maxInclusive 100 ];
 sh:property [ sh:path ebwv:economicEntitlementPercentage; sh:maxCount 1; sh:datatype xsd:decimal; sh:minInclusive 0; sh:maxInclusive 100 ];
 sh:property [ sh:path ebwv:votingRightsPercentage; sh:maxCount 1; sh:datatype xsd:decimal; sh:minInclusive 0; sh:maxInclusive 100 ];
 sh:property [ sh:path ebwv:establishedUnder; sh:or ( [ sh:class ebwv:LegalArrangement ] [ sh:class ebwv:LegalInstrument ] ) ];
 sh:property [ sh:path ebwv:supportingParticipation; sh:class ebwv:ArrangementParticipation ];
 sh:property [ sh:path ebwv:conditions; sh:class ebwv:RelationshipCondition; sh:node oa:ConditionShape ];
 sh:sparql [ sh:message "Indirect shareholding needs an ordered relationship path."; sh:select """
 PREFIX oa: <https://jgmikael.github.io/docs/ownership-attestations/profile#>
 PREFIX ebwv: <https://w3id.org/ebwv#>
 SELECT $this WHERE { $this oa:level oa:indirect; oa:interestType oa:shareholding . FILTER NOT EXISTS { $this ebwv:hasRelationshipPath ?p } } """ ];
 sh:sparql [ sh:message "Each path member must be an OwnershipOrControlRelationship."; sh:select """
 PREFIX ebwv: <https://w3id.org/ebwv#>
 PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
 SELECT $this WHERE { $this ebwv:hasRelationshipPath/rdf:rest*/rdf:first ?r . FILTER NOT EXISTS { ?r a ebwv:OwnershipOrControlRelationship } } """ ];
 sh:sparql [ sh:message "Indirect path must start at its holder and end at its target."; sh:select """
 PREFIX ebwv: <https://w3id.org/ebwv#>
 PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
 SELECT $this WHERE { $this ebwv:hasRelationshipPath ?p; ebwv:rightHolder ?h; ebwv:relationshipTarget ?t . ?p rdf:first/ebwv:rightHolder ?first . ?p rdf:rest* ?lastCell . ?lastCell rdf:rest rdf:nil; rdf:first/ebwv:relationshipTarget ?last . FILTER (?h != ?first || ?t != ?last) } """ ];
 sh:sparql [ sh:message "Adjacent path relationships must connect through the same intermediary."; sh:select """
 PREFIX ebwv: <https://w3id.org/ebwv#>
 PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
 SELECT $this WHERE { $this ebwv:hasRelationshipPath/rdf:rest* ?cell . ?cell rdf:first/ebwv:relationshipTarget ?t; rdf:rest/rdf:first/ebwv:rightHolder ?h . FILTER (?t != ?h) } """ ];
 sh:sparql [ sh:message "Supporting participation must name the right holder and belong to its establishing arrangement."; sh:select """
 PREFIX ebwv: <https://w3id.org/ebwv#>
 SELECT $this WHERE { $this ebwv:rightHolder ?h; ebwv:supportingParticipation ?p . FILTER NOT EXISTS { ?p ebwv:participatingParty ?h . $this ebwv:establishedUnder ?a . ?a ebwv:hasParticipation ?p } } """ ].
oa:PeriodShape a sh:NodeShape;
 sh:property [ sh:path ebwv:startDate; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:date ];
 sh:property [ sh:path ebwv:endDate; sh:maxCount 1; sh:datatype xsd:date ];
 sh:sparql [ sh:message "Period end precedes its start."; sh:select """
 PREFIX ebwv: <https://w3id.org/ebwv#>
 SELECT $this WHERE { $this ebwv:startDate ?s; ebwv:endDate ?e . FILTER (?e < ?s) } """ ].
oa:ParticipationShape a sh:NodeShape; sh:targetClass ebwv:ArrangementParticipation;
 sh:property [ sh:path ebwv:participatingParty; sh:minCount 1; sh:maxCount 1; sh:or ( [ sh:class ebwv:NaturalPerson ] [ sh:class ebwv:LegalPerson ] [ sh:class ebwv:EconomicOperator ] ) ];
 sh:property [ sh:path ebwv:participationRole; sh:minCount 1; sh:maxCount 1; sh:in (oa:settlor oa:trustee oa:protector oa:beneficiaryOfLegalArrangement) ];
 sh:property [ sh:path ebwv:effectivePeriod; sh:minCount 1; sh:node oa:PeriodShape ].
oa:ConditionShape a sh:NodeShape; sh:targetClass ebwv:RelationshipCondition;
 sh:property [ sh:path oa:trigger; sh:minCount 1; sh:datatype xsd:string; sh:minLength 1 ];
 sh:property [ sh:path oa:consentRequired; sh:minCount 1; sh:datatype xsd:string; sh:minLength 1 ];
 sh:property [ sh:path oa:conditionSatisfied; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:boolean ];
 sh:property [ sh:path oa:assessedOn; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:date ].
'''
for path in ['ebwv:thoroughfare','ebwv:locatorDesignator','ebwv:postName','ebwv:adminUnitL2','ebwv:postCode']:
    pass
shape+='oa:AddressShape a sh:NodeShape;\n'+ ';\n'.join(' sh:property '+prop(p,single('xsd:string')+'; sh:minLength 1') for p in ['ebwv:thoroughfare','ebwv:locatorDesignator','ebwv:postName','ebwv:adminUnitL2','ebwv:postCode'])+';\n sh:property [ sh:path ebwv:adminUnitL1; sh:minCount 1; sh:maxCount 1; sh:datatype ebwv:CountryCode; sh:in ("FI"^^ebwv:CountryCode "GB"^^ebwv:CountryCode) ] .\n'
for name,path,vs,minimum in [('InterestShape','oa:interestType',terms['InterestType'],True),('InterestShape','oa:level',terms['Level'],True),('InterestShape','oa:economicRight',terms['EconomicRight'],False),('InterestShape','oa:shareClass',terms['ShareClass'],False),('EntityShape','oa:entityForm',terms['EntityForm'],True),('EvidenceShape','oa:evidenceType',terms['EvidenceType'],True),('RelationshipShape','ebwv:relationshipType',terms['RelationshipType'],True),('RelationshipShape','ebwv:exerciseMode',terms['ExerciseMode'],True),('ArrangementShape','oa:arrangementForm',['trust'],True),('ArrangementShape','ebwv:arrangementType',['expressTrust'],True)]:
    shape+=f'oa:{name} sh:property [ sh:path {path}; '+('sh:minCount 1; ' if minimum else '')+f'sh:in {enum(vs)} ] .\n'
shape+='oa:InterestShape sh:property [ sh:path oa:shareQuantity; sh:maxCount 1; sh:datatype xsd:integer; sh:minInclusive 0 ] .\n'
shape+='''
oa:InterestShape sh:or (
 [ sh:property [ sh:path oa:interestType; sh:hasValue oa:shareholding ]; sh:property [ sh:path ebwv:ownershipPercentage; sh:minCount 1 ]; sh:property [ sh:path oa:shareQuantity; sh:minCount 1 ]; sh:property [ sh:path oa:economicRight; sh:minCount 1 ] ]
 [ sh:property [ sh:path ebwv:relationshipType; sh:hasValue oa:economicEntitlement ]; sh:property [ sh:path ebwv:economicEntitlementPercentage; sh:minCount 1 ]; sh:property [ sh:path oa:economicRight; sh:minCount 1 ] ]
 [ sh:property [ sh:path ebwv:relationshipType; sh:hasValue oa:appointmentPower ]; sh:property [ sh:path ebwv:establishedUnder; sh:minCount 1 ]; sh:property [ sh:path ebwv:conditions; sh:minCount 1 ]; sh:property [ sh:path oa:powerState; sh:hasValue oa:contingent ]; sh:property [ sh:path ebwv:ownershipPercentage; sh:maxCount 0 ]; sh:property [ sh:path oa:shareQuantity; sh:maxCount 0 ]; sh:property [ sh:path oa:economicRight; sh:maxCount 0 ] ]
).
oa:RelationshipShape sh:sparql [ sh:message "Contingent power cannot be marked as having satisfied conditions."; sh:select """
 PREFIX oa: <https://jgmikael.github.io/docs/ownership-attestations/profile#>
 PREFIX ebwv: <https://w3id.org/ebwv#>
 SELECT $this WHERE { $this oa:powerState oa:contingent; ebwv:conditions/oa:conditionSatisfied true } """ ].
oa:AttestationShape sh:sparql [ sh:message "Every owner interest must target the credential subject."; sh:select """
 PREFIX oa: <https://jgmikael.github.io/docs/ownership-attestations/profile#>
 PREFIX ebwv: <https://w3id.org/ebwv#>
 PREFIX cred: <https://www.w3.org/2018/credentials#>
 SELECT $this WHERE { $this cred:credentialSubject ?s; oa:ownerRecord/oa:interest/ebwv:relationshipTarget ?t . FILTER (?s != ?t) } """ ].
oa:AttestationShape sh:sparql [ sh:message "Direct shareholding percentages exceed 100%; do not add indirect or economic-entitlement records."; sh:select """
 PREFIX oa: <https://jgmikael.github.io/docs/ownership-attestations/profile#>
 PREFIX ebwv: <https://w3id.org/ebwv#>
 SELECT $this WHERE { { SELECT $this (SUM(?p) AS ?total) WHERE { $this oa:ownerRecord/oa:interest ?r . ?r oa:level oa:direct; oa:interestType oa:shareholding; ebwv:ownershipPercentage ?p } GROUP BY $this } FILTER (?total > 100) } """ ].
'''
(ROOT/'laoc-content.shacl.ttl').write_text(shape)
# Strict Rulebook overlay deliberately preserves literal IR-09/10/11 requirements.
strict=prefix+'''
oa:StrictInterestShape a sh:NodeShape; sh:targetObjectsOf oa:interest;
 sh:property [ sh:path ebwv:ownershipPercentage; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:decimal; sh:minInclusive 0; sh:maxInclusive 100; sh:message "IR-09: Rulebook requires an ownership percentage for every interest" ];
 sh:property [ sh:path oa:shareQuantity; sh:minCount 1; sh:maxCount 1; sh:datatype xsd:integer; sh:minInclusive 0; sh:message "IR-10: Rulebook requires a quantity for every interest" ];
 sh:property [ sh:path oa:economicRight; sh:minCount 1; sh:in (oa:dividend_rights oa:liquidation_rights); sh:message "IR-11: Rulebook requires an economic right for every interest" ].
oa:StrictTotalShape a sh:NodeShape; sh:targetClass oa:OwnershipAttestation; sh:severity sh:Warning;
 sh:sparql [ sh:message "IR-19 (SHOULD): summing all owner percentages exceeds 100%; this may double-count direct and indirect levels"; sh:select """
 PREFIX oa: <https://jgmikael.github.io/docs/ownership-attestations/profile#>
 PREFIX ebwv: <https://w3id.org/ebwv#>
 SELECT $this WHERE { { SELECT $this (SUM(?p) AS ?total) WHERE { $this oa:ownerRecord/oa:interest/ebwv:ownershipPercentage ?p } GROUP BY $this } FILTER (?total > 100) } """ ].
'''
(ROOT/'rulebook-strict-overlay.shacl.ttl').write_text(strict)

base_shapes=Graph().parse(data=shape,format='turtle'); strict_shapes=Graph().parse(data=shape+'\n'+strict,format='turtle')
def results(g,shapes):
    conforms,report,_=validate(g,shacl_graph=shapes,allow_warnings=True,inference='none',advanced=True)
    rs=[]
    for n in report.subjects(RDF.type,SH.ValidationResult):
        rs.append({'severity':str(report.value(n,SH.resultSeverity)).split('#')[-1], 'focus':str(report.value(n,SH.focusNode)), 'message':str(report.value(n,SH.resultMessage)), 'path':str(report.value(n,SH.resultPath) or '')})
    return {'conforms':bool(conforms),'results':rs}
validation=[]
for ex in examples:
    g=ex['g']; slug=ex['slug']
    g.serialize(ROOT/(slug+'.ttl'),format='turtle')
    g.serialize(ROOT/(slug+'.jsonld'),format='json-ld',context=CONTEXT,indent=2)
    roundtrip=Graph().parse(ROOT/(slug+'.jsonld'),format='json-ld')
    from rdflib.compare import isomorphic
    assert isomorphic(g,roundtrip),slug+' JSON-LD roundtrip'
    ex['validation']=results(g,base_shapes); ex['strictValidation']=results(g,strict_shapes)
    assert ex['validation']['conforms'], (slug,ex['validation'])
    assert results(roundtrip,base_shapes)['conforms'],slug+' serialized JSON-LD validation'
    assert results(Graph().parse(ROOT/(slug+'.ttl')),base_shapes)['conforms'],slug+' serialized Turtle validation'
    assert ex['strictValidation']['conforms']==ex['strict'], (slug,ex['strictValidation'])
    validation.append({'example':slug,'laocProfile':ex['validation'],'strictRulebookProjection':ex['strictValidation']})

# Meaningful negative checks: constraints must catch incorrect content.
tests=[]
def negative(name,index,mutation):
    g=Graph(); [g.add(t) for t in examples[index]['g']]; mutation(g)
    outcome=results(g,base_shapes); assert not outcome['conforms'],name
    tests.append({'test':name,'rejected':True,'messages':sorted(set(r['message'] for r in outcome['results']))})
negative('Missing owner evidence',0,lambda g:g.remove((D['aino-direct-record'],A.evidence,None)))
negative('Ownership percentage above 100',0,lambda g:(g.remove((D['aino-direct'],E.ownershipPercentage,None)),g.add((D['aino-direct'],E.ownershipPercentage,Literal('101',datatype=XSD.decimal)))))
negative('Broken intermediary in indirect path',1,lambda g:(g.remove((D['aino-to-holding'],E.relationshipTarget,None)),g.add((D['aino-to-holding'],E.relationshipTarget,D['leena']))))
negative('Missing trust deed',2,lambda g:g.remove((D['virta-trust'],E.constitutedBy,None)))
negative('Incorrect party for trustee capacity',2,lambda g:(g.remove((D['trust-trustee'],E.participatingParty,None)),g.add((D['trust-trustee'],E.participatingParty,D['elina']))))
negative('Contingent power with satisfied conditions',3,lambda g:(g.remove((D['appointment-condition'],A.conditionSatisfied,None)),g.add((D['appointment-condition'],A.conditionSatisfied,Literal(True)))))
(ROOT/'validation-results.json').write_text(json.dumps({'engine':'pySHACL','inference':'none','examples':validation,'negativeChecks':tests},indent=2))

def val(g,s,p,default=''): return next(g.objects(s,p),default)
def name(g,n): return str(val(g,n,RDFS.label,n))
def esc(v): return html.escape(str(v))
def pct(v): return str(v).rstrip('0').rstrip('.') if '.' in str(v) else str(v)
def dl(items): return '<dl class="facts">'+''.join('<div><dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd></div>' for k,v in items)+'</dl>'
CSS='''
:root{--ink:#172d35;--muted:#526871;--paper:#f7f9f8;--line:#dbe4e2;--teal:#086e65;--pale:#e5f2ee;--amber:#805417;--gold:#fff3d9}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--teal);text-underline-offset:4px}header{border-bottom:1px solid var(--line);background:#fff}nav{max-width:1120px;margin:auto;display:flex;align-items:center;justify-content:space-between;padding:20px 28px;gap:20px}.brand{font-weight:750;letter-spacing:-.3px;text-decoration:none;color:var(--ink)}nav span{font-size:13px;color:var(--muted)}main{max-width:1120px;margin:auto;padding:40px 28px 70px}h1{font-size:clamp(32px,5vw,50px);line-height:1.12;letter-spacing:-1.5px;max-width:830px;margin:18px 0 18px}h2{font-size:24px;letter-spacing:-.5px;margin-top:35px}h3{font-size:20px;line-height:1.35;margin:6px 0 10px}.eyebrow{color:var(--teal);text-transform:uppercase;font-size:12px;font-weight:800;letter-spacing:1.5px}.lead{font-size:19px;color:var(--muted);max-width:850px}.notice{background:var(--gold);border-left:4px solid #bf8d39;padding:14px 18px;margin:24px 0;font-size:14px;color:#654716}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{display:block;background:white;border:1px solid var(--line);border-radius:14px;padding:26px;text-decoration:none;color:var(--ink)}a.card:hover{border-color:var(--teal);box-shadow:0 6px 20px #163f3510}.card p{color:var(--muted)}.card .open{color:var(--teal);font-weight:700;font-size:14px}.bar{display:flex;gap:16px;flex-wrap:wrap;margin:22px 0}.bar a{font-size:14px}.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;padding:22px;background:var(--pale);border-radius:12px}.facts dt{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);font-weight:700}.facts dd{margin:5px 0 0;font-size:15px;font-weight:650}.owner{background:white;border:1px solid var(--line);border-radius:12px;margin:16px 0;padding:24px}.owner-top{display:flex;justify-content:space-between;gap:20px;align-items:start}.owner h3{margin-top:0}.badge{font-size:12px;font-weight:700;color:var(--teal);background:var(--pale);border-radius:20px;padding:5px 11px;white-space:nowrap}.badge.warn{background:var(--gold);color:var(--amber)}.metric{font-size:30px;font-weight:750;letter-spacing:-1px}.owner .facts{background:var(--paper);margin-bottom:0;grid-template-columns:repeat(3,1fr);padding:16px}.takeaway{background:var(--ink);color:white;border-radius:12px;padding:24px;margin:24px 0}.takeaway strong{display:block;margin-bottom:8px}.takeaway p{margin:0;color:#d7e9e5}.path{border-left:3px solid var(--teal);padding:10px 18px;background:white;margin:12px 0}.path span{display:block;color:var(--muted)}details{border:1px solid var(--line);border-radius:9px;background:white;margin:12px 0;padding:14px 18px}summary{cursor:pointer;font-weight:650}details p{font-size:14px;color:var(--muted)}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;background:var(--paper);border-radius:6px;padding:16px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:12px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted)}.table-wrap{overflow:auto}.small{font-size:14px;color:var(--muted)}footer{max-width:1120px;padding:20px 28px 40px;margin:auto;color:var(--muted);font-size:13px}.next{display:flex;justify-content:space-between;margin-top:36px}button{font:inherit;font-size:14px;background:white;color:var(--teal);border:1px solid var(--line);border-radius:7px;padding:8px 14px;cursor:pointer}@media(max-width:700px){.grid,.facts,.owner .facts{grid-template-columns:1fr}main{padding:28px 18px}nav{padding:16px 18px}nav span{display:none}.owner-top{display:block}.metric{margin-top:12px}h1{letter-spacing:-1px}.badge{display:inline-block}}@media print{nav,.bar,.next,button{display:none}body{background:white}main{padding:0}.owner{break-inside:avoid}details{display:none}.facts{background:#f4f4f4}}
'''
(ROOT/'style.css').write_text(CSS)
def page(title,body): return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Fictional Ownership Attestation examples using EBWV and LAOC"><title>{esc(title)} · Ownership attestations</title><link rel="stylesheet" href="style.css"></head><body><header><nav><a class="brand" href="index.html">Ownership attestations</a><span>EBWV + LAOC · Content examples</span></nav></header><main>{body}</main><footer>Fictional, unsigned content examples · Proposed LAOC extension · Prepared 5 October 2026</footer></body></html>'''
notice='<div class="notice"><strong>Demonstration only.</strong> All people, companies, identifiers, addresses and evidence are fictional. These are unsigned EAA content examples, not usable credentials or independently verified ownership records.</div>'
cards=''.join(f'<a class="card" href="{e["slug"]}.html"><span class="eyebrow">{esc(e["tag"])}</span><h3>{esc(e["title"])}</h3><p>{esc(e["subtitle"])}</p><span class="open">Read the attestation →</span></a>' for e in examples)
index=page('Examples',f'''<div class="eyebrow">Who owns what — and on what basis?</div><h1>Ownership is more than a percentage.</h1><p class="lead">Four attestations show direct shares, an ownership chain, a trust’s separation of title and benefit, and a conditional control power. Read the business content first; supporting data and checks sit underneath.</p>{notice}<div class="grid">{cards}</div><h2>Read each attestation in the same way</h2><p>Start with the company being described. Then inspect the holder, the exact right, its legal basis, the date it became effective and the evidence the issuer relies on. A company can issue an EAA about its own structure; that self-issued statement still needs verification by a relying party.</p><div class="takeaway"><strong>Keep title, benefit and control distinct.</strong><p>A trustee can hold legal title while a beneficiary receives the economic benefit. A contractual power can exist without any shares. An indirect economic percentage does not by itself prove control.</p></div><details><summary>Semantic foundation and validation choices</summary><p>Original EBWV describes people, companies, identifiers, addresses, periods and the EAA category. LAOC adds qualified ownership/control relationships, arrangements, legal instruments and participation. Both use the EBWV namespace; LAOC is a proposed extension, not a separate adopted vocabulary.</p><p>The local <code>oa:</code> profile supplies the Rulebook’s record structure and fields that neither vocabulary currently defines. The SHACL layer implements a content projection of the linked draft Rulebook, with explicit adjustments for non-share rights. It does not validate cryptographic signatures or an SD-JWT token.</p><p><a href="profile.html">Read the profile, mappings and validation results</a> · <a href="{RB}">Pinned Ownership Rulebook</a> · <a href="{ORIGINAL}">Original EBWV source</a> · <a href="{LAOC}">LAOC proposal</a></p></details>''')
(ROOT/'index.html').write_text(index)

for ix,ex in enumerate(examples):
    g=ex['g']; att=ex['att']; subject=val(g,att,C.credentialSubject)
    body=f'<div class="eyebrow">{esc(ex["tag"])}</div><h1>{esc(ex["title"])}</h1><p class="lead">{esc(ex["summary"])}</p>{notice}'
    body+=dl([('Subject company',name(g,subject)),('Attestation category','EAA · company self-issued content'),('Assessed on','5 October 2026')])
    body+='<div class="bar"><button onclick="window.print()">Print reading view</button><a href="index.html">All examples</a></div>'
    body+='<h2>The issuer’s ownership statement</h2>'+dl(ex['facts'])
    body+=f'<p class="small"><strong>Scope:</strong> {esc(ex["scope"])}</p>'
    def reading_order(rec):
        r=val(g,rec,A.interest); level=str(val(g,r,A.level)).split('#')[-1]
        is_power=val(g,r,E.relationshipType)==code('appointmentPower')
        p=val(g,r,E.ownershipPercentage,val(g,r,E.economicEntitlementPercentage,0))
        return (2 if is_power else (0 if level=='direct' else 1),-float(p),name(g,val(g,rec,A.party)))
    for rec in sorted(g.objects(att,A.ownerRecord),key=reading_order):
        p=val(g,rec,A.party); r=val(g,rec,A.interest); own=val(g,r,E.ownershipPercentage,None); eco=val(g,r,E.economicEntitlementPercentage,None)
        metric=(pct(own)+'% shares') if own is not None else ((pct(eco)+'% economic benefit') if eco is not None else 'Conditional power')
        kind=str(val(g,r,E.relationshipType)).split('#')[-1]; level=str(val(g,r,A.level)).split('#')[-1]
        body+=f'<article class="owner"><div class="owner-top"><div><span class="badge{ " warn" if kind=="appointmentPower" else ""}">{esc(level)} · {esc("company" if (p,RDF.type,E.LegalPerson) in g else "person")}</span><h3>{esc(name(g,p))}</h3><div>{esc(name(g,r))}</div></div><div class="metric">{esc(metric)}</div></div>'
        items=[('Right in',name(g,val(g,r,E.relationshipTarget))),('Effective from',str(val(g,rec,A.effectiveDate))),('Legal basis',name(g,val(g,r,E.establishedUnder)) if val(g,r,E.establishedUnder) else 'Share register')]
        quantity=val(g,r,A.shareQuantity,None)
        if quantity is not None: items.append(('Share units',str(quantity)+(' economic equivalents' if val(g,r,A.quantityMeaning) else ' registered shares')))
        rights=list(g.objects(r,A.economicRight))
        if rights: items.append(('Economic rights',', '.join('dividends' if str(v).endswith('dividend_rights') else 'liquidation proceeds' for v in rights)))
        body+=dl(items)
        for note in [val(g,r,A.capacityNote),val(g,r,A.quantityMeaning)]:
            if note: body+='<p class="small">'+esc(note)+'</p>'
        if (p,RDF.type,E.NaturalPerson) in g:
            identity=[('Date of birth',val(g,p,E.dateOfBirth)),('Jurisdiction of this owner entry',val(g,rec,A.ownerJurisdiction))]
            addr=val(g,p,E.domicile)
        else:
            identity=[('Legal identifier',val(g,p,E.legalIdentifier)),('Legal form',val(g,p,E.legalForm)),('Registered jurisdiction',val(g,p,E.jurisdiction))]
            addr=val(g,p,E.registeredAddress)
        identity.append(('Fictional address',' '.join(str(val(g,addr,q)) for q in [E.thoroughfare,E.locatorDesignator,E.postCode,E.postName,E.adminUnitL1])))
        body+='<details><summary>Identity recorded for this holder</summary>'+dl(identity)+'</details>'
        path=val(g,r,E.hasRelationshipPath)
        if path:
            seq=list(Collection(g,path)); chain=[name(g,val(g,seq[0],E.rightHolder))]+[name(g,val(g,m,E.relationshipTarget)) for m in seq]
            body+='<div class="path">'+esc(' → '.join(chain))+'<span>'+esc(val(g,r,A.calculation))+'</span></div>'
        for cond in g.objects(r,E.conditions):
            body+='<div class="notice"><strong>Conditions for exercise</strong>'+dl([('Trigger',val(g,cond,A.trigger)),('Consent',val(g,cond,A.consentRequired)),('Satisfied at assessment','No' if not val(g,cond,A.conditionSatisfied).toPython() else 'Yes')])+'</div>'
        body+='</article>'
    for arrangement in g.subjects(RDF.type,E.LegalArrangement):
        body+='<h2>The legal arrangement</h2>'+dl([('Name',name(g,arrangement)),('Type','Express trust · fictional English-law scenario'),('Constituted by',name(g,val(g,arrangement,E.constitutedBy)))])
        body+='<p>'+esc(val(g,arrangement,DCTERMS.description))+'</p>'
        body+='<div class="table-wrap"><table><thead><tr><th>Participant</th><th>Position in the trust</th><th>What the position tells us</th></tr></thead><tbody>'
        notes={'settlor':'Settled the specified share block; the role does not assert current title.','trustee':'Administers the asset and holds its legal title in trustee capacity.','protector':'Can remove the trustee under clause 8; no personal share title is asserted.','beneficiaryOfLegalArrangement':'Receives the fixed economic benefit of the share block.'}
        role_order={'settlor':0,'trustee':1,'protector':2,'beneficiaryOfLegalArrangement':3}
        for part in sorted(g.objects(arrangement,E.hasParticipation),key=lambda p:role_order[str(val(g,p,E.participationRole)).split('#')[-1]]):
            role=str(val(g,part,E.participationRole)).split('#')[-1]
            body+=f'<tr><td>{esc(name(g,val(g,part,E.participatingParty)))}</td><td>{esc("beneficiary" if role=="beneficiaryOfLegalArrangement" else role)}</td><td>{esc(notes[role])}</td></tr>'
        body+='</tbody></table></div><p class="small">Trust participants are represented separately from the company’s owner records. No AML beneficial-owner conclusion is inferred solely from these roles.</p>'
    body+='<div class="takeaway"><strong>How to read this statement</strong><p>'+esc(ex['takeaway'])+'</p></div>'
    body+='<h2>Evidence the issuer relied on</h2><p class="small">These are readable fictional fixtures, embedded in the example data. Their titles indicate the kind of evidence a real issuer would need.</p>'
    used=set(g.objects(None,E.supportedBy))|set(g.objects(None,E.constitutedBy))
    for ev in sorted(used,key=str):
        body+='<details><summary>'+esc(name(g,ev))+'</summary><pre>'+esc(val(g,ev,DCTERMS.description))+'</pre></details>'
    strict_result=ex['strictValidation']; warn=any(r['severity']=='Warning' for r in strict_result['results'])
    strict_read='Mandatory content checks pass'+(' · IR-19 total warning' if warn else '') if strict_result['conforms'] else 'Does not pass literal IR-09/10/11 requirements'
    body+='<details><summary>Content checks and underlying data</summary><p><strong>LAOC-aware content profile:</strong> passes the implemented SHACL checks. <strong>Literal Rulebook projection:</strong> '+esc(strict_read)+'.</p><p>These results check structure and internal consistency. They do not establish truth, evidence authenticity, issuer authority, revocation or signature validity. This is unsigned content, with a placeholder holder key and status reference.</p><p>'+esc('Non-share rights omit artificial ownership percentages and share quantities; the profile deliberately departs from the Rulebook here.' if not ex['strict'] else 'Birth dates are included. This profile takes the stricter mandatory interpretation of the conflicting Rulebook text.')+'</p><div class="bar"><a href="'+ex['slug']+'.jsonld">JSON-LD content</a><a href="'+ex['slug']+'.ttl">Turtle content</a><a href="profile.html">SHACL profile and mapping</a><a href="validation-results.json">Validation report</a></div>'+dl([('Issued','5 October 2026 · 09:00 UTC'),('Content validity ends','4 November 2026 · 09:00 UTC'),('Issuer and subject',name(g,subject))])+'</details>'
    nex=examples[(ix+1)%len(examples)]
    body+=f'<div class="next"><a href="index.html">← All examples</a><a href="{nex["slug"]}.html">Next example →</a></div>'
    (ROOT/(ex['slug']+'.html')).write_text(page(ex['title'],body))

mapping=[
 ('Company / person identity','EBWV LegalPerson, EconomicOperator, NaturalPerson; legalName, legalIdentifier, givenName, familyName, dateOfBirth','Reuses the actual original EBWV signatures.'),
 ('Owner records and interests','oa:ownerRecord → oa:OwnerRecord → oa:party / oa:interest','Rulebook structure is local to this profile; ebwv:owner has a BankAccount domain and is not repurposed.'),
 ('Holder and target','LAOC rightHolder / relationshipTarget','One exact holder and target per qualified right; legal title, economic benefit and appointment powers remain distinct.'),
 ('Percentages and quantities','LAOC ownershipPercentage, votingRightsPercentage, economicEntitlementPercentage; oa:shareQuantity','LAOC replaces the old TBD/float ownershipPercentage definition. EBWV amount is MonetaryAmount, not a share count.'),
 ('Trust settlement / purpose / assets','LAOC constitutedBy / arrangementAsset; dct:description','No retyping of an arrangement as a legal person. Instrument, arrangement and property are separate resources.'),
 ('Trust participants','LAOC hasParticipation / participatingParty / participationRole / supportingParticipation','Trust positions are contextual. They do not automatically confer personal asset title.'),
 ('Indirect chain','LAOC hasRelationshipPath, an ordered RDF list','Path members, holder/target endpoints and adjacent intermediaries are checked.'),
 ('Evidence','LAOC supportedBy; oa:evidence; dct:identifier; oa:evidenceType / evidenceData','Embedded base64 fictional fixtures satisfy the evidence alternative in these examples. SHACL cannot establish URL accessibility or authenticity.'),
 ('Time and address','LAOC effectivePeriod → EBWV PeriodOfTime/startDate; EBWV Address and its fields','Business effectiveness is distinct from assessment time and credential validity.'),
 ('Conditional control','LAOC LegalInstrument, conditions → RelationshipCondition; oa:trigger / consentRequired / conditionSatisfied / powerState','Detailed condition fields are a local proposal; LAOC intentionally left this profile open.'),
 ('EAA metadata','EBWV ElectronicAttestationOfAttributes / attestationLegalCategory → EAA; cred:issuer / credentialSubject / validFrom / validUntil','An unsigned semantic content view, not a completed W3C credential or SD-JWT VC.')]
matrix=[('IR-01/02','Owner records and at least one Person','Implemented; keeps the Rulebook design choice, not a general AML legal conclusion.'),('IR-03/04','Person or Entity branch','Implemented using exclusive RDF class branches rather than JSON object absence.'),('IR-05','Legal-arrangement details','Implemented on linked arrangement nodes: instrument, purpose, asset, jurisdiction, address and participation.'),('IR-06','Entity identifier','Demo requires Euid legalIdentifier plus identifier. No actual registry validity is asserted.'),('IR-07/08/12/16/20','Interest, level, class, evidence and entity codes','Enumerated from §2.8; local concept schemes added for LAOC right/exercise types.'),('IR-09/10/11','Percentage, quantity and economic rights','Strict overlay requires them for every record. LAOC-aware profile makes these depend on the right; never fabricates them.'),('IR-13/14/15','Evidence presence and reference/data','Structural alternative implemented. Embedded data is used here; external URL accessibility requires a separate check.'),('IR-17/18/21','Dates, country and effective date','Datatype/cardinality checks; FI/GB are an explicit demo subset, not a complete ISO country list.'),('IR-19','Totals','Strict overlay warns on all-level totals. LAOC-aware profile caps direct shareholding totals only, avoiding cross-level double counting.'),('§2.5 / §3.2','Metadata, cnf and status','Issuer, category, dates, placeholder holder-key reference and structural status reference present. JWT cnf/key binding, signature and status lookup are outside these SHACL content checks.')]
def table(rows,heads): return '<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in heads)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
profilebody=f'''<div class="eyebrow">Supporting profile · Draft 0.1</div><h1>Semantic content, with explicit validation choices.</h1><p class="lead">The examples use original EBWV and proposed LAOC terms. A small local profile connects them to the Ownership Rulebook’s record structure.</p>{notice}<div class="bar"><a href="index.html">Reading examples</a><a href="laoc-content.shacl.ttl">LAOC-aware SHACL</a><a href="rulebook-strict-overlay.shacl.ttl">Strict Rulebook overlay</a><a href="profile-vocabulary.ttl">Local profile terms</a><a href="validation-results.json">Validation results</a></div><h2>Semantic mappings</h2>{table(mapping,['Content','Semantic mapping','Choice'])}<h2>Rulebook checks implemented</h2>{table(matrix,['Reference','Requirement','Implementation and limit'])}<h2>What passed</h2>{table([(e['title'],'Pass','Pass with total warning' if e['strictValidation']['conforms'] and e['strictValidation']['results'] else ('Pass' if e['strictValidation']['conforms'] else 'Does not pass: non-share rights omit mandated fields')) for e in examples],['Example','LAOC-aware content','Literal Rulebook projection'])}<p>Six negative fixtures were rejected: missing evidence, percentage above 100, a broken intermediary, a missing trust deed, a mismatched trustee participation, and satisfied conditions on a power labelled contingent. JSON-LD and Turtle graphs were checked for equivalent RDF content.</p><h2>Open decisions, not hidden defaults</h2><p>The linked Rulebook is a feedback draft, version 1.0.1. It contains inconsistent birth-date requirements, ambiguous Person jurisdiction mappings, pending references, and an identifier “other” value that one review note rejects. This demo includes birth dates, uses explicit profile jurisdiction fields on owner records, and uses no “other” identifier.</p><p>An arrangement is not treated as a legal person simply because the Rulebook puts it in the Entity branch. The trust is a separate resource, its trustee holds title, and its beneficiary’s economic entitlement is a separate right. A shareholder agreement is not automatically an AML legal arrangement.</p><p>IR-19 is a SHOULD rule, so the strict overlay reports a warning without failing mandatory content checks. Its all-level total is 160% in the indirect example because it mixes overlapping direct and indirect interests. A production profile should total only comparable rights at the same layer and define aggregation and calculation rules.</p><p>The SHACL shape accepts only the scenarios and country subset shown here. It checks chain connectivity, not general graph completeness, legal interpretation, general multi-path multiplication or prevention of all cycles. It does not validate an SD-JWT serialization, array order in JSON, disclosure proofs, key binding, evidence authenticity or issuer authority. The Rulebook’s W3C VC encoding section is unfinished; these RDF graphs are an encoding-independent semantic projection with no signature.</p><p>Full issuance validation runs against the complete graph. A selectively disclosed presentation needs a separate presentation profile; missing hidden values must not be confused with invalid original issuance.</p><h2>Sources and reproducibility</h2><p><a href="{RB}">Pinned Rulebook commit 5c9ace0</a> · <a href="{ORIGINAL}">Pinned EBWV commit a230684</a> · <a href="{LAOC}">Published LAOC proposal</a></p><p>The LAOC proposal retains the EBWV namespace. Its replacement ownershipPercentage definition is used here; do not load the old and revised domain/range axioms together.</p><div class="bar"><a href="build_examples.py">Generator and validation checks</a><a href="README.md">Rebuild instructions</a><a href="ownership-attestation-examples.zip">Download the complete examples</a></div>'''
(ROOT/'profile.html').write_text(page('Semantic and SHACL profile',profilebody))
readme='''# Ownership Attestation content examples — EBWV + LAOC

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
'''
(ROOT/'README.md').write_text(readme)
with zipfile.ZipFile(ROOT/'ownership-attestation-examples.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.iterdir():
        if p.is_file() and p.name not in ['rulebook.md','ebwv-source.yml'] and p.suffix in ['.html','.css','.jsonld','.ttl','.json','.py','.md']: z.write(p,p.name)
print(json.dumps({'examples':[{'slug':e['slug'],'laoc':e['validation']['conforms'],'strict':e['strictValidation']['conforms'],'strictResults':len(e['strictValidation']['results'])} for e in examples],'negativeChecks':len(tests)},indent=2))
