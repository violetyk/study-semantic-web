/*
 *  Creates an RDFS inferencing repository
 *  Loads the film ontology which declares Actor and Director as rdfs:subTypeOf Person
 *  Runs a query to see what individuals are typed Person
 */

import java.util.List;

import org.openrdf.model.URI;
import org.openrdf.model.Value;

public class TypeTest {
    public static void main(String[] args) {
        
        //create a graph with type inferencing
        SimpleGraph g = new SimpleGraph(true); 
        
        //load the film schema and the example data
        g.addFile("film-ontology.owl", SimpleGraph.RDFXML);
        
        List solutions = g.runSPARQL("SELECT ?who WHERE  { " +
          "?who <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://semprog.com/Person> ." +
                "}");
        System.out.println("SPARQL solutions: " + solutions.toString());
    }
}
