from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, BNode, Literal, RDF, URIRef
import IVAtoRDF

FB = Namespace("http://rdf.freebase.com/ns/")
DC = Namespace("http://purl.org/dc/elements/1.1/")
IVA_MOVIE= Namespace("http://www.videodetective.com/titledetails.aspx?publishedid=")
IVA_PERSON= Namespace("http://www.videodetective.com/actordetails.aspx?performerid=")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

movies=IVAtoRDF.get_in_theaters()
movie_graph=IVAtoRDF.make_rdf_graph(movies)
    
fq=movie_graph.query("""SELECT ?film ?act ?perf ?an ?fn WHERE
                        {?film fb:film.film.performances ?perf .
                         ?perf fb:film.performance.actor ?act . 
                         ?act dc:title ?an.                              
                         ?film dc:title ?fn .                              
                         }""",
                     initNs={'fb':FB,'dc':DC})

graphs={}
for film,act,perf,an,fn in fq:
    filmid=fn.split(',')[0].replace(' ','_')+'_'+str(film).split('=')[1]
    actid=an.replace(' ','_')+'_'+str(act).split('=')[1]
    
    graphs.setdefault(filmid,ConjunctiveGraph())
    graphs.setdefault(actid,ConjunctiveGraph())

    graphs[filmid].add((film,FB['film.film.performance.actor'],act))
    graphs[filmid].add((act,RDFS['seeAlso'],actid+'.xml'))
    graphs[filmid].add((film,DC['title'],fn))
    
    graphs[actid].add((act,FB['film.actor.performance.film'],film))
    graphs[actid].add((film,RDFS['seeAlso'],filmid+'.xml'))
    graphs[actid].add((act,DC['title'],an))

for id,graph in graphs.items():
    graph.serialize('open_films/%s.xml' % id)
    