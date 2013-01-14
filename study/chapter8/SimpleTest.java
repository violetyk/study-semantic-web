import java.util.List;

import org.openrdf.model.URI;
import org.openrdf.model.Value;

public class SimpleTest {

	public static void main(String[] args) {
	
		//a test of graph operations
		
		SimpleGraph g = new SimpleGraph();
		
		//get LOD from a URI -  Jamie's FOAF profile from Hi5
		g.addURI("http://api.hi5.com/rest/profile/foaf/241087912");
		
		//manually add a triple/statement with a URIref object
		URI s1 = g.URIref("http://semprog.com/people/toby");
		URI p1 = g.URIref(SimpleGraph.RDFTYPE);
		URI o1 = g.URIref("http://xmlns.com/foaf/0.1/person");
		g.add(s1, p1, o1);
		
		//manually add with an object literal
		URI s2 = g.URIref("http://semprog.com/people/toby");
		URI p2 = g.URIref("http://xmlns.com/foaf/0.1/nick");
		Value o2 = g.Literal("kiwitobes");
		g.add(s2, p2, o2);
		
		//parse a string of RDF and add to the graph
		String rdfstring = "<http://semprog.com/people/jamie> <http://xmlns.com/foaf/0.1/nick> \"jt\" .";
		g.addString(rdfstring, SimpleGraph.NTRIPLES);
		
		System.out.println("\n==TUPLE QUERY==\n");
		List rlist = g.tuplePattern(null, g.URIref("http://xmlns.com/foaf/0.1/nick"), null);
		System.out.print(rlist.toString());
		
		//dump the graph in the specified format
		System.out.println("\n==GRAPH DUMP==\n");
		g.dumpRDF(System.out, SimpleGraph.NTRIPLES);
		
		//run a SPARQL query - get back solution bindings
		System.out.println("\n==SPARQL SELECT==\n");
		List solutions = g.runSPARQL("SELECT ?who ?nick " +
				"WHERE { " +
					"?x <http://xmlns.com/foaf/0.1/knows> ?y . " +
					"?x <http://xmlns.com/foaf/0.1/nick> ?who ." +
					"?y <http://xmlns.com/foaf/0.1/nick> ?nick ."   +
				"}");
		System.out.println("SPARQL solutions: " + solutions.toString());
		
		//run a CONSTUCT SPARQL query 
		System.out.println("\n==SPARQL CONSTRUCT==\n");
		String newgraphxml = g.runSPARQL("CONSTRUCT { ?x <http://semprog.com/simple#friend> ?nick . } " +
				"WHERE { " +
					"?x <http://xmlns.com/foaf/0.1/knows> ?y . " +
					"?x <http://xmlns.com/foaf/0.1/nick> ?who ." +
					"?y <http://xmlns.com/foaf/0.1/nick> ?nick ."   +
				"}", SimpleGraph.RDFXML);
		System.out.println("SPARQL solutions: \n" + newgraphxml);
		
	//run a CONSTUCT SPARQL query 
	System.out.println("\n==SPARQL DESCRIBE==\n");
	String describexml = g.runSPARQL("DESCRIBE ?x  " +
			"WHERE { " +
				"?x <http://xmlns.com/foaf/0.1/knows> ?y . " +
				"?x <http://xmlns.com/foaf/0.1/nick> ?who ." +
				"?y <http://xmlns.com/foaf/0.1/nick> ?nick ."   +
			"}", SimpleGraph.N3);
	System.out.println("SPARQL solutions: \n" + describexml);
	
}
	
}
