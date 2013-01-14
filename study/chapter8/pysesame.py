from urllib import urlopen,quote_plus
from simplejson import loads

class connection:
    def __init__(self,url):
        self.baseurl=url
        self.sparql_prefix=""
    
    def addnamespace(self,id,ns):
        self.sparql_prefix+='PREFIX %s:<%s>\n' % (id,ns) 
    
    def __getsparql__(self,method):
        #print self.baseurl+method
        data=urlopen(self.baseurl+method).read()
        try:
            result=loads(data)['results']['bindings']
            return result
        except:
            return [{'error':data}];
    
    def repositories(self):
        return self.__getsparql__('repositories')
        
    def use_repository(self,r):
        self.repository=r
    
    def query(self,q):
        q='repositories/'+self.repository+'?query='+quote_plus(self.sparql_prefix+q)
        return self.__getsparql__(q)
        
    def construct_query(self,q):
        q='repositories/'+self.repository+'?query='+quote_plus(self.sparql_prefix+q)
        data=urlopen(self.baseurl+q).read()
        return data
    
    def postdata(self,data):
        #/openrdf-sesame/repositories/mem-rdf/statements
        host=baseurl+'/repositories/'+self.repository+'/statements'
        res=urlopen(host,data)
        return res
        
        
if __name__=='__main__':

    c=connection('http://localhost:8080/openrdf-sesame/')
    c.use_repository('Movies')
    c.addnamespace('fb','http://rdf.freebase.com/ns/')
    c.addnamespace('dc','http://purl.org/dc/elements/1.1/')
    
    res=c.query("""SELECT ?costar ?fn WHERE {?film fb:film.film.performances ?p1 .
                   ?film dc:title ?fn .
                   ?p1 fb:film.performance.actor ?a1 . 
                   ?a1 dc:title "John Malkovich".
                   ?film fb:film.film.performances ?p2 .
                   ?p2 fb:film.performance.actor ?a2 . 
                   ?a2 dc:title ?costar .}""")

    for r in res:
        print r