from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, BNode, Literal, RDF, URIRef
from urllib import urlopen
from xml.dom.minidom import parse

FB = Namespace("http://rdf.freebase.com/ns/")
DC = Namespace("http://purl.org/dc/elements/1.1/")
IVA_MOVIE= Namespace("http://www.videodetective.com/titledetails.aspx?publishedid=")
IVA_PERSON= Namespace("http://www.videodetective.com/actordetails.aspx?performerid=")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

# Returns the text inside the first element with this tag
def getdata(node,tag):
    datanode=node.getElementsByTagName(tag)[0]
    if not datanode.hasChildNodes(): return None
    return datanode.firstChild.data

# Creates a list of movies in theatres right now
def get_in_theaters():
    #stream=urlopen('http://www.videodetective.com/api/intheaters.aspx?DeveloperId={KEY}')
    #stream=urlopen('http://semprog.com/data/intheaters.xml')
    stream=file('intheaters.xml')

    root=parse(stream)
    stream.close()
    
    movies=[]
    
    for item in root.getElementsByTagName('item'):
        movie={}
        
        # Get the ID, title, and director
        movie['id']=getdata(item,'PublishedId')
        movie['title']=getdata(item,'Title')
        movie['director']={'id':getdata(item,'DirectorID'),'name':getdata(item,'Director')}
        
        # Actor tags are numbered: Actor1, Actor2, etc.
        movie['actors']=[]    
        for i in range(1,6):
            actor=getdata(item,'Actor%d' % i)
            actorid=getdata(item,'ActorId%d' % i)
            
            if actor!=None and actorid!=None:
                movie['actors'].append({'name':actor,'id':actorid})
        
        movies.append(movie)
    
    return movies

# Generate an RDF Graph from the Movie Data
def make_rdf_graph(movies):
    mg=ConjunctiveGraph()

    mg.bind('fb',FB)
    mg.bind('dc',DC)
    for movie in movies:
        
        # Make a movie node
        movie_node=IVA_MOVIE[movie['id']]    
        mg.add((movie_node,DC['title'],Literal(movie['title'])))
        
        # Make the director node, give it a name and link it to the movie
        dir_node=IVA_PERSON[movie['director']['id']]
        mg.add((movie_node,FB['film.film.directed_by'],dir_node))
        mg.add((dir_node,DC['title'],Literal(movie['director']['name'])))

        for actor in movie['actors']:
            # The performance node is a blank node -- it has no URI
            performance=BNode()
            
            # The performance is connected to the actor and the movie
            actor_node=IVA_PERSON[actor['id']]
            
            mg.add((actor_node,DC['title'],Literal(actor['name'])))
            mg.add((performance,FB['film.performance.actor'],actor_node))
            # If you had the name of the role, you could also add it to the
            # performance node, e.g.
            # mg.add((performance,FB['film.performance.role'],Literal('Carrie Bradshaw')))

            mg.add((movie_node,FB['film.film.performances'],performance))

    return mg

if __name__=='__main__':
    movies=get_in_theaters()
    movie_graph=make_rdf_graph(movies)
    
    print movie_graph.serialize(format='xml')
    
    #res=movie_graph.query("""SELECT ?fn  WHERE {?film fb:film.film.performances ?perf .
    #                                            ?perf fb:film.performance.actor ?act . 
    #                                            ?act dc:title "John Malkovich".
    #                                            ?film fb:type.object.name ?fn . }""",
    #                      initNs={'fb':FB,'dc':DC})
    #for row in res:
    #    print row

    