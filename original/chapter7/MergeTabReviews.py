from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, BNode, Literal, RDF, URIRef
from IVAtoRDF import FB,DC,get_in_theaters,make_rdf_graph
from csv import reader

# Reviews Namespace
REV=Namespace('http://www.purl.org/stuff/rev#')

if __name__=='__main__':

    # Create a graph of movies currently in theaters
    movies=get_in_theaters()
    movie_graph=make_rdf_graph(movies)
    
    # Loop over all reviews in the CSV file
    for title,rating,review in reader(open('MovieReviews.csv','U')):
    
        # Find a movie with this title
        match=movie_graph.query('SELECT ?movie WHERE {?movie dc:title "%s" .}' % title,
                                initNs={'dc':DC})
        
        for movie_node, in match:
            # Create a blank review node 
            review_node=BNode()
            
            # Connect the review to the movie
            movie_graph.add((movie_node,REV['hasReview'],review_node))
            
            # Connect the details of the review to the review node
            movie_graph.add((review_node,REV['rating'],Literal(int(rating))))
            movie_graph.add((review_node,DC['descripton'],Literal(review)))
            movie_graph.add((review_node,REV['reviewer'],URIRef('http://semprog.com/people/toby')))
    
    # Search for movies that have a rating of 4 or higher and the directors
    res=movie_graph.query("""SELECT ?title ?rating ?dirname
                             WHERE {?m rev:hasReview ?rev .
                                    ?m dc:title ?title .
                                    ?m fb:film.film.directed_by ?d .
                                    ?d dc:title ?dirname .
                                    ?rev rev:rating ?rating .
                                    FILTER (?rating >= 4)
                                   }""", initNs={'rev':REV,'dc':DC,'fb':FB})

    for title,rating,dirname in res:
        print '%s\t%s\t%s' % (title,dirname,rating)
                    
