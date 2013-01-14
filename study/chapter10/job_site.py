import cherrypy
from rdflib import Namespace, BNode, Literal, RDF, URIRef
from pysesame import connection
from mako.template import Template
from mako.lookup import TemplateLookup
from urllib import quote_plus

lookup = TemplateLookup(directories=['templates'])
con=connection('http://freerisk.org:8280/openrdf-sesame/')
con.use_repository('joblistings')
DC = Namespace("http://purl.org/dc/elements/1.1/")
JB = Namespace("http://semprog.com/schemas/jobboard#")
COMPANY = Namespace("http://purl.org/rss/1.0/modules/company/")
namefields=set([str(DC['title']),str(COMPANY['name'])])

class Main(object):

    @cherrypy.expose
    def index(self):
        id=quote_plus('http://semprog.com/schemas/jobboard#tumblr')
        return 'Try visiting <a href="view?id=%s">here</a>' % id

    @cherrypy.expose
    def view(self,id):
        sa=con.query('select ?pred ?obj where {<%s> ?pred  ?obj .}' % id)
        oa=con.query('select ?pred ?sub where {?sub ?pred  <%s> .}' % id)
        name=id
        for row in sa:
            print row
            if row['pred']['value'] in namefields:
                name=row['obj']['value']

        t=lookup.get_template('viewgeneric.html')
        return t.render(name=name,sa=sa,oa=oa,qp=quote_plus)
 
cherrypy.quickstart(Main())
