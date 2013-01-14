from rdflib import Namespace
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

from foafcrawl import make_foaf_graph
import networkx as nx

if __name__=='__main__':
    # Build the social network from FOAF files
    rdf_graph=make_foaf_graph('http://api.hi5.com/rest/profile/foaf/241057043',steps=3)
    
    # Get nicknames by ID
    nicknames={}    
    for id,nick in rdf_graph.query('SELECT ?a ?nick '+\
                                       'WHERE { ?a foaf:nick ?nick . }',
                               initNs={'foaf':FOAF,'rdfs':RDFS}):
        nicknames[str(id)]=str(nick)
    
    # Build a NetworkX graph of relationships
    nx_graph=nx.Graph()    
    for a,b in rdf_graph.query('SELECT ?a ?b '+\
                               'WHERE { ?a foaf:knows ?b . }',
                               initNs={'foaf':FOAF,'rdfs':RDFS}):
        nx_graph.add_edge(str(a),str(b))
    
    # Calculate the centrality of every node    
    cent=nx.betweenness_centrality(nx_graph)
    
    # Rank the most central people (the influencers)
    most_connected=sorted([(score,id) for id,score in cent.items()],reverse=True)[0:5]
    
    print 'Most Central'
    for score,id in most_connected:
        print nicknames[id],score
    
    print
   
    # Calculate the cluster-coefficient of every node
    clust=nx.clustering(nx_graph,with_labels=True)
   
    # Rank the most cliquish people
    most_clustered=sorted([(score,id) for id,score in clust.items()],reverse=True)[0:5]
    print 'Most Clustered'
    for score,id in most_clustered:
        print nicknames[id],score
    
    print
    for clique in nx.find_cliques(nx_graph):
        if len(clique)>2:
            print [nicknames[id] for id in clique]
