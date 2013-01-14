from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, BNode, Literal, RDF, URIRef
from pysesame import connection
import urllib
from simplejson import loads
from csv import reader

JB = Namespace("http://semprog.com/schemas/jobboard#")
DC = Namespace("http://purl.org/dc/elements/1.1/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
COMPANY = Namespace("http://purl.org/rss/1.0/modules/company/")

# Connecion to Sesame
con=connection('http://freerisk.org:8280/openrdf-sesame/')
con.use_repository('joblistings')
con.addnamespace('company',str(COMPANY))

cg=ConjunctiveGraph()
cg.bind('dc',DC)
cg.bind('jobboard',JB)

# Find companies with ticker symbols
res=con.query('select ?id ?ticker where {?id company:symbol ?ticker .}')

# Loop over the results
for row in res:
    company=URIRef(row['id']['value'])
    ticker=row['ticker']['value']
    
    url='http://ichart.finance.yahoo.com/table.csv?s=%s&a=00&b=28&c=2008&d=00&e=28&f=2009&g=m&ignore=.csv' % ticker
    
    rows=[row for row in reader(urllib.urlopen(url))]

    current=float(rows[1][6])
    yearago=float(rows[-1][6])
    
    # Calculate percent change
    change=((current-yearago)/current)*100

    cg.add((company,JB['stockpricechange'],Literal(change)))

print cg.serialize(format='xml')
