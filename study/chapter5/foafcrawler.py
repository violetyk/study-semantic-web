from rdflib.Graph import Graph
from rdflib import Namespace,BNode

FOAF = Namespace("http://xmlns.com/foaf/0.1/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

def make_foaf_graph(starturi, steps=3):

    # Initialize the graph
    foafgraph = Graph()
    
    # Keep track of where we've already been
    visited = set()
    
    # Keep track of the current crawl queue
    current = set([starturi])
    
    # Crawl steps out
    for i in range(steps):
        nextstep = set()
        
        # Visit and parse every URI in the current set, adding it to the graph
        for uri in current:
            visited.add(uri)
            tempgraph = Graph()

            # Construct a request with an ACCEPT header
            # This tells pages you want RDF/XML
            try:
                reqObj = urllib2.Request(uri, None, {"ACCEPT":"application/rdf+xml"})
                urlObj = urllib2.urlopen(reqObj)
                tempgraph.parse(urlObj,format='xml')
                urlObj.close()
            except:
                print "Couldn't parse %s" % uri
                continue
            
            # Work around for FOAF's anonymous node problem
            # Map blank node IDs to their seeAlso URIs
            nm = dict([(str(s), n) for s, _, n in tempgraph.triples((None, RDFS['seeAlso'], None))])

            # Identify the root node (the one with an image for hi5, or the one called "me")
            imagelist=list(tempgraph.triples((None, FOAF['img'], None)))
            if len(imagelist) >0:
                nm[imagelist[0][0]]=uri
            else:
                nm[''],nm['#me']=uri,uri
            
            # Now rename the blank nodes as their seeAlso URIs
            for s, p, o in tempgraph:
                if str(s) in nm: s = nm[str(s)]
                if str(o) in nm: o = nm[str(o)]
                foafgraph.add((s, p, o))                
            
            # Now look for the next step
            newfriends = tempgraph.query('SELECT ?burl ' +\
                                         'WHERE {?a foaf:knows ?b . ?b rdfs:seeAlso ?burl . }',
                                         initNs={'foaf':FOAF,'rdfs':RDFS})
    
            # Get all the people in the graph. If we haven't added them already, add them
            # to the crawl queue
            for friend in newfriends:
                if friend[0] not in current and friend[0] not in visited:
                    nextstep.add(friend[0])
                    visited.add(friend[0])
        
        # The new queue becomes the current queue
        current = nextstep
    return foafgraph
    
if __name__ == '__main__':

    # Seed the network with Robert Cook, creator of D/Generation
    g = make_foaf_graph('http://api.hi5.com/rest/profile/foaf/241057043', steps=4)

    # Print who knows who in our current graph
    for row in g.query('SELECT ?anick ?bnick '+\
                       'WHERE { ?a foaf:knows ?b . ?a foaf:nick ?anick . ?b foaf:nick ?bnick . }',
                       initNs={'foaf':FOAF}):
        print "%s knows %s" % row
