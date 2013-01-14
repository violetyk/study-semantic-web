from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, BNode, Literal, RDF, URIRef
import csv
import pysesame

JOBS = Namespace("http://www.medev.ac.uk/interoperability/rss/1.0/modules/jobs/rss1.0jobsmodule#")
DC = Namespace("http://purl.org/dc/elements/1.1/")
JB = Namespace("http://semprog.com/schemas/jobboard#")
COMPANY = Namespace("http://purl.org/rss/1.0/modules/company/")
RDFS=Namespace('http://www.w3.org/2000/01/rdf-schema#')

jg=ConjunctiveGraph()
jg.bind('jobs',JOBS)
jg.bind('dc',DC)
jg.bind('jobboard',JB)
jg.bind('company',COMPANY)
jg.bind('rdfs',RDFS)

# Incremental counter for vacancy IDs
vid=0

for title,salary,location,company,crunchbase,ticker in csv.reader(file('joblist.csv')):
    # Create the vacancy
    vid+=1
    vacancy=JB[str(vid)]
    jg.add((vacancy,RDF.type,JOBS['Vacancy']))
    jg.add((vacancy,DC['title'],Literal(title)))
    
    location_id=location.lower().replace(' ','_').replace(',','')
    jg.add((vacancy,JB['location'],JB[location_id]))
    jg.add((JB[location_id],DC['title'],Literal(location)))
    
    # Salary range
    salaryrange=BNode()
    jg.add((vacancy,JOBS['salaryrange'],salaryrange))
    jg.add((salaryrange,JOBS['minimumsalary'],Literal(float(salary))))

    # Create the company
    cnode=JB[company.lower().replace(' ','_')]
    jg.add((vacancy,JOBS['vacancywith'],cnode))
    jg.add((cnode,RDF.type,JOBS['Organization']))
    
    # Ticker symbol
    if ticker!="":
        jg.add((cnode,COMPANY['symbol'],Literal(ticker)))
    jg.add((cnode,COMPANY['name'],Literal(company)))
    
    # Crunchbase (see also)
    if crunchbase!="":
        jg.add((cnode,RDFS['seeAlso'],
                Literal('http://api.crunchbase.com/v/1/company/%s.js' % crunchbase)))
    
# Print the serialized graph
data=jg.serialize(format='xml')
print data
#c=pysesame.connection('http://freerisk.org:8280/openrdf-sesame/')
#c.use_repository('joblistings')
#print c.postdata(data)


    
