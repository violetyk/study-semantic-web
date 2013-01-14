from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, BNode, Literal, RDF, URIRef
import csv
import pysesame

JB = Namespace("http://semprog.com/schemas/jobboard#")
GEO = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')

lg=ConjunctiveGraph()
lg.bind('geo',GEO)

for city,lat,long in csv.reader(file('city_locations.csv','U')):
    lg.add((JB[city],GEO['lat'],Literal(float(lat))))
    lg.add((JB[city],GEO['long'],Literal(float(long))))
    
data=lg.serialize(format='xml')
print data
c=pysesame.connection('http://semprog.com:8280/openrdf-sesame/')
c.use_repository('joblistings')
print c.postdata(data)


    
