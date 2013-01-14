from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, BNode, Literal, RDF, URIRef
from pysesame import connection
import urllib
from simplejson import loads

# Connecion to Sesame
con=connection('http://freerisk.org:8280/openrdf-sesame/')
con.use_repository('joblistings')
con.addnamespace('rdfs','http://www.w3.org/2000/01/rdf-schema#')

JB = Namespace("http://semprog.com/schemas/jobboard#")
DC = Namespace("http://purl.org/dc/elements/1.1/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

cg=ConjunctiveGraph()
cg.bind('dc',DC)
cg.bind('jobboard',JB)
cg.bind('foaf',FOAF)

# Find seeAlso URLs containing Crunchbase
res=con.query('select ?id ?url where {?id rdfs:seeAlso ?url . FILTER regex(?url, "crunchbase")}')

# Loop over the results
for row in res:
    company=URIRef(row['id']['value'])
    url=row['url']['value']
    data=urllib.urlopen(url).read()
    record=loads(data)

    # Add company locations
    for loc in record['offices']:
        if loc['city'] and loc['state_code']:
            cityid='%s_%s' % (loc['city'].lower().replace(' ','_'),loc['state_code'].lower())
            cg.add((company,JB['location'],JB[cityid]))

    # Add URL
    cg.add((company,FOAF['homepage'],Literal(record['homepage_url'])))

    # Add funding rounds
    for fr in record['funding_rounds']:
        round=BNode()
        cg.add((company,JB['funding_round'],round))
        cg.add((round,JB['amount'],Literal(fr['raised_amount'])))
        cg.add((round,DC['date'], Literal(str(fr['funded_year']))))


data=cg.serialize(format='xml')
print data
#c=pysesame.connection('http://freerisk.org:8280/openrdf-sesame/')
#c.use_repository('joblistings')
#print c.postdata(data)
