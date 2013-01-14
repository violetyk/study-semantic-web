from rdflib import Namespace, URIRef, Literal, BNode
from rdflib.Graph import Graph
from urllib import quote_plus
from httplib import HTTPConnection
from cStringIO import StringIO
import xml.dom

owlNS = Namespace("http://www.w3.org/2002/07/owl#")
owlClass = owlNS["Class"]
owlObjectProperty = owlNS["ObjectProperty"]
owlDatatypeProperty = owlNS["DatatypeProperty"]
rdfNS = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfProperty = rdfNS["Property"]
rdfType = rdfNS["type"]
rdfsNS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
rdfsSubClassOf = rdfsNS["subClassOf"]
rdfsDomain = rdfsNS["domain"]
rdfsRange = rdfsNS["range"]

class SesameTransaction:
    def __init__(self):
        self.trans = xml.dom.getDOMImplementation().createDocument(None, "transaction", None)

    def add(self, statement):
        self.__addAction("add", statement)

    def remove(self, statement):
        self.__addAction("remove", statement)

    def toXML(self):
        return self.trans.toxml()

    def __addAction(self, action, statement):
        element = self.trans.createElement(action)
        for item in statement:
            if isinstance(item, Literal):
                literal = self.trans.createElement("literal")
                if item.datatype is not None: literal.setAttribute("datatype", str(item.datatype))
                if item.language is not None: literal.setAttribute("xml:lang", str(item.language))
                literal.appendChild(self.trans.createTextNode(str(item)))
                element.appendChild(literal)
            elif isinstance(item, URIRef):
                uri = self.trans.createElement("uri")
                uri.appendChild(self.trans.createTextNode(str(item)))
                element.appendChild(uri)
            elif isinstance(item, BNode):
                bnode = self.trans.createElement("bnode")
                bnode.appendChild(self.trans.createTextNode(str(item)))
                element.appendChild(bnode)
            else:
                raise Exception("Unknown element: " + item)
        self.trans.childNodes[0].appendChild(element)

class SesameConnection:
    def __init__(self, host, repository=None):
        self.host = host
        self.repository = repository
        self.sparql_prefix=""

    def addnamespace(self, id, ns):
        self.sparql_prefix+='PREFIX %s:<%s>\n' % (id,ns)

    def repositories(self):
        return self.__getsparql__('repositories')

    def use_repository(self, r):
        self.repository = r

    def __request__(self, method, path, data, headers):
        conn = HTTPConnection(self.host)
        conn.request(method, path, data, headers)
        response = conn.getresponse()
        if response.status != 200 and response.status != 204:
            raise Exception("Sessame connection error " + str(response.status) + " " + response.reason)
        response = response.read()
        conn.close()
        return response

    def query(self, query, graph):
        path = '/openrdf-sesame/repositories/' + self.repository + '?query=' + quote_plus(self.sparql_prefix + query)
        data = self.__request__("GET", path, None, {"accept":"application/rdf+xml"})
        graph.parse(StringIO(data))
        return graph

    def update(self, add=None, remove=None):
        path = '/openrdf-sesame/repositories/' + self.repository + "/statements"
        trans = SesameTransaction()
        if remove is not None:
            for statement in remove: trans.remove(statement)
        if add is not None:
            for statement in add: trans.add(statement)
        data = self.__request__("POST", path, trans.toXML(), {"content-type":"application/x-rdftransaction"})

class OWLOntology:
    """
    This class loads the mappings from simple property names
    to OWL property URIs.
    """

    def __init__(self, sesameConnection):
        # query for all OWL classes and properties:
        self._ontGraph = Graph()
        sesameConnection.query(
            """construct {
             ?c rdf:type owl:Class .
             ?c rdfs:subClassOf ?sc .
             ?p rdfs:domain ?c .
             ?p rdfs:range ?d  .
             ?p rdf:type ?pt .
            } where
            {
             ?c rdf:type owl:Class .
            OPTIONAL {
             ?c rdfs:subClassOf ?sc .
            }
            OPTIONAL {
             ?p rdfs:domain ?c .
             ?p rdfs:range ?d .
             ?p rdf:type ?pt .
            }
            }""", self._ontGraph)
        # map type properties to simplified names:
        self.propertyMaps = {}
        for ontClass in self._ontGraph.subjects(rdfType, owlClass):
            propertyMap = self.propertyMaps[ontClass] = {}
            for property in self._ontGraph.subjects(rdfsDomain, ontClass):
                propertyName = self.getSimplifiedName(property)
                propertyMap[propertyName] = property
            for property in self._ontGraph.subjects(rdfsRange, ontClass):
                propertyName = "r_" + self.getSimplifiedName(property)
                propertyMap[propertyName] = property
        # recursivley copy property mappings across the class hierarchy:
        def copySuperclassProperties(ontClass, propertyMap):
            for superclass in self._ontGraph.objects(ontClass, rdfsSubClassOf):
                copySuperclassProperties(superclass, propertyMap)
            propertyMap.update(self.propertyMaps[ontClass])
        for ontClass in self._ontGraph.subjects(rdfType, owlClass):
            copySuperclassProperties(ontClass, self.propertyMaps[ontClass])

    def getSimplifiedName(self, uri):
        if "#" in uri: return uri[uri.rfind("#") + 1:]
        return uri[uri.rfind("/") + 1:]

class RDFObjectGraphFactory:
    """
    A factory for RDFObjects.
    """
    def __init__(self, connection):
        self.connection = connection
        self.connection.addnamespace("xsd", "http://www.w3.org/2001/XMLSchema#")
        self.connection.addnamespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.connection.addnamespace("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
        self.connection.addnamespace("owl", "http://www.w3.org/2002/07/owl#")
        self.ontology = OWLOntology(connection)

    def createGraph(self):
        return RDFObjectGraph(self.connection, self.ontology)

class RDFObjectGraph:
    """
    The RDFObjectGraph caches object values for populating RDFObject values.
    """
    def __init__(self, connection, ontology):
        self._connection = connection
        self._ontology = ontology
        self._rdfObjects = {}
        self._graph = Graph()
        self._added = Graph()
        self._removed = Graph()

    def get(self, uri):
        """
        Gets an RDFObject for the specified URI.
        """
        if uri not in self._rdfObjects:
            self._load(uri)
            self._rdfObjects[uri] = RDFObject(uri, self)
        return self._rdfObjects[uri]

    def _load(self, uri):
        """
        This method ensures that the data for a uri is loaded into
        the local graph.
        """
        if uri not in self._rdfObjects:
            self._connection.query(
            "construct { <" + uri + "> ?p ?o . " +
            "?rs ?rp <" + uri + "> .} where { " +
            "OPTIONAL { <" + uri + "> ?p ?o } " +
            "OPTIONAL { ?rs ?rp <" + uri + "> } }", self._graph)

    def _subjects(self, prop, uri):
        """
        Retrieves all subjects for a property and object URI.
        """
        for triple in self._graph.triples((None, prop, uri)):
            if triple not in self._removed:
                yield triple[0]
        for triple in self._added.triples((None, prop, uri)):
            yield triple[0]

    def _objects(self, uri, prop):
        """
        Retrieves all objects for a subject URI and property.
        """
        for triple in self._graph.triples((uri, prop, None)):
            if triple not in self._removed:
                yield triple[2]
        for triple in self._added.triples((uri, prop, None)):
            yield triple[2]

    def _predicates(self, subject=None, object=None):
        """
        Retrieves all unique predicates for a subject or object URI.
        """
        result = set()
        for triple in self._graph.triples((subject, None, object)):
            if triple not in self._removed:
                result.add(triple[1])
        for triple in self._added.triples((subject, None, object)):
            result.add(triple[1])
        return result

    def _setSubjects(self, values, prop, uri):
        """
        Sets all subjects for a property and uri.
        """
        newValues = set(values)
        existingValues = set(self._graph.subjects(prop, uri))
        for value in existingValues - newValues:
            removed = (value, prop, uri)
            self._added.remove(removed)
            self._removed.add(removed)
        for value in newValues - existingValues:
            added = (value, prop, uri)
            self._removed.remove(added)
            self._added.add(added)

    def _setObjects(self, uri, prop, values):
        """
        Sets all objects for a uri and property.
        """
        newValues = set(values)
        existingValues = set(self._graph.objects(uri, prop))
        for value in existingValues - newValues:
            removed = (uri, prop, value)
            self._added.remove(removed)
            self._removed.add(removed)
        for value in newValues - existingValues:
            added = (uri, prop, value)
            self._removed.remove(added)
            self._added.add(added)

    def commit(self):
        """
        Commits changes to the remote graph and flushes local caches.
        """
        self._connection.update(add=self._added, remove=self._removed)
        self._rdfObjects = {}
        self._graph = Graph()
        self._added = Graph()
        self._removed = Graph()

class RDFObject:
    """
    The RDFObject wraps an RDF URI and automatically retrieves property values
    as they are referenced as object attributes.
    """
    def __init__(self, uri, objectGraph):
        self.__dict__["uri"] = uri
        self.__dict__["_objectGraph"] = objectGraph

    def __repr__(self):
        return "<RDFObject " + self.uri + ">"

    def __str__(self):
        return self.uri

    def __getattr__(self, name):
        self._objectGraph._load(self.uri)
        prop = self._getProp(name)
        if name.startswith("r_"):
            values = self._objectGraph._subjects(prop, self.uri)
        else:
            values = self._objectGraph._objects(self.uri, prop)
        results = self._wrapResults(values)
        return results

    def __setattr__(self, name, values):
        self._objectGraph._load(self.uri)
        unwrappedValues = []
        for value in values:
            # unwrap rdfobjects:
            if isinstance(value, RDFObject):
                unwrappedValues.append(value.uri)
            # pass through rdflib objects:
            elif isinstance(value, URIRef) or isinstance(value, BNode) or isinstance(value, Literal):
                unwrappedValues.append(value)
            # wrap literals:
            else:
                unwrappedValues.append(Literal(value))
        # look for a property mapping for this name:
        prop = self._getProp(name)
        if name.startswith("r_"):
            self._objectGraph._setSubjects(unwrappedValues, prop, self.uri)
        else:
            self._objectGraph._setObjects(self.uri, prop, unwrappedValues)

    def _getProp(self, name):
        if name == "type": return rdfType
        for type in self._objectGraph._objects(self.uri, rdfType):
            propertyMap = self._objectGraph._ontology.propertyMaps[type]
            if name in propertyMap: return propertyMap[name]
        raise AttributeError("Unknown property '" + name + "'")

    def __getitem__(self, key):
        self._objectGraph._load(self.uri)
        # iterate over predicates and look for a matching name:
        reverse = key.startswith("r_")
        if reverse:
            preds = self._objectGraph._predicates(object=self.uri)
            name = key[2:]
        else:
            preds = self._objectGraph._predicates(subject=self.uri)
            name = key
        for pred in preds:
            if self._objectGraph._ontology.getSimplifiedName(pred) == name:
                if reverse:
                    values = self._objectGraph._subjects(pred, self.uri)
                else:
                    values = self._objectGraph._objects(self.uri, pred)
                return self._wrapResults(values)
        raise KeyError("Property '" + key + "' not found")

    def _wrapResults(self, results):
        ret = []
        for result in results:
            if isinstance(result, Literal): ret.append(result)
            else: ret.append(self._objectGraph.get(result))
        return ret

if __name__ == "__main__":
    sc = SesameConnection("localhost:8080", "semprog")
    factory = RDFObjectGraphFactory(sc)
    objectGraph = factory.createGraph()
    filmNs = Namespace("http://www.semprog.com/film#")
    bladerunner = objectGraph.get(filmNs["blade_runner"])
    harrisonford = objectGraph.get(filmNs["harrison_ford"])
    print bladerunner.type
    print bladerunner.name[0]
    print bladerunner.starring[0].has_actor[0].name[0]
    print bladerunner.starring[0].has_actor[0].r_has_actor[0].r_starring

    print harrisonford.name[0]
    print harrisonford.r_has_actor[0].r_starring
    print bladerunner["name"][0]
    print bladerunner["starring"][0]["has_actor"][0]["name"][0]
    names = bladerunner.name
    names.append("Do Androids Dream of Electric Sheep?")
    bladerunner.name = names
    print bladerunner.name
    objectGraph.commit()
    print bladerunner.name
    bladerunner.name = ["Blade Runner"]
    objectGraph.commit()
    print bladerunner.name

    raiders = objectGraph.get(filmNs["raiders_of_the_lost_ark"])
    raiders.type = [filmNs["Film"]]
    raiders.name = ["Raiders of the Lost Ark"]
    perf2 = objectGraph.get(filmNs["perf2"])
    perf2.type = [filmNs["Performance"]]
    indy = objectGraph.get(filmNs["indy"])
    indy.type = [filmNs["Role"]]
    indy.name = ["Indiana Jones"]
    perf2.r_starring = [raiders, bladerunner]
    perf2.has_actor = [harrisonford]
    perf2.has_role = [indy]
    objectGraph.commit()
    print indy.name
    print raiders.name
    perf2.r_starring = [raiders]
    objectGraph.commit()
    print perf2.r_starring
    print raiders.starring[0].has_actor[0].uri
    print harrisonford.r_has_actor
