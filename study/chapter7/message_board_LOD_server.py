import os
from wsgiref import simple_server

import rdflib
from rdflib import Namespace

import message_board_to_sioc
from message_board_to_sioc import SIOC, DC, DCTERMS, FOAF, RDFS, MB

"""
A very simple Linked Open Data server
It does not implement content negotiation (among other things)
...and only serves rdf+xml
"""

server_addr =  "127.0.0.1"
server_port = 8000
infores_uri_component = "/rdf"

def rewrite(environ):
	#add infores first path segment
	return "http://" + environ["HTTP_HOST"] + infores_uri_component + environ["PATH_INFO"]

def test_handler(environ):
	resp = {"status":"200 OK"}
	resp["headers"] = [("Content-type", "text/html")]
	outstr = ""
	for k in environ.keys():
		outstr += str(k) + ": " + str(environ[k]) + "<br>"
	resp["body"] = [outstr]
	return resp

def redirect(environ):
	resp = {"status":"303 See Other"}
	resp["headers"] = [("Location", rewrite(environ))]
	return resp

def servedata(environ):
	#Additional ns' for the queries 
	ourserver = "http://" + server_addr + ":" + str(server_port) + "/"
        MBMSG = Namespace(ourserver + "messages/")
	MBUSR = Namespace(ourserver + "users/")

	path = environ["PATH_INFO"]
	
	resp = {"status":"200 OK"}	
	resp["headers"] = [("Content-type", "application/rdf+xml")]

	if environ["PATH_INFO"].find("users") != -1:
		#user request query
		userid = "mbusr:" + path[path.rindex("/") + 1:]
		query = """CONSTRUCT { 
                       """ + userid + """ sioc:creator_of ?msg .
		       ?msg dc:title ?title .
                       """ + userid + """ foaf:name ?name .
		   } WHERE { 
		       ?msg sioc:has_creator """ + userid + """ .
                       ?msg dc:title ?title .
                       """ + userid + """ foaf:name ?name .
                   } """
	else:
                #message request query                                            
		msgid = "mbmsg:" + path[path.rindex("/") + 1:]
		query = """CONSTRUCT {
                        """ + msgid + """ dc:title ?title .
                        """ + msgid + """ sioc:has_creator ?user .
                        """ + msgid + """ sioc:content ?content .
                    } WHERE { 
                        """ + msgid + """ dc:title ?title .
                        """ + msgid + """ sioc:has_creator ?user .
                        """ + msgid + """ sioc:content ?content .  
		    } """

	bindingdict = {'sioc':SIOC,
                       'dc':DC,
                       'dcterms':DCTERMS,
                       'foaf':FOAF,
                       'rdfs':RDFS,
                       'mb':MB,
		       'mbmsg':MBMSG,
		       'mbusr':MBUSR}

	resp["body"] = [sg.query(query, initNs=bindingdict).serialize(format='xml')]
	
	return resp

def error(environ, errormsg):
	resp = {"status":"400 Error"}
	resp["headers"] = [("Content-type", "text/plain")]
	resp["body"] = [errormsg]

def application(environ, start_response):
	"""Dispatch based on first path component"""
	path = environ["PATH_INFO"]

	if path.startswith(infores_uri_component):
		resp = servedata(environ)

	elif path.startswith("/messages/") or \
	     path.startswith("/users/"):

	        resp = redirect(environ)
		
	elif path.startswith("/test/"):
		resp = test_handler(environ)
	else:
		resp = error(environ, "Path not supported")
	
	start_response(resp["status"], resp["headers"])
	if resp.has_key("body"):
		return resp["body"]
	else:
		return ""


if __name__ == "__main__":
        #initialize the graph
	if not os.path.exists('message_board.db'):
		message_board_to_sioc.load_data('message_board.sql','message_board.db')

	serverlocation = server_addr + ":" + str(server_port)

        #change the MB namespace to the base URI for this server
	message_board_to_sioc.MB = Namespace("http://" + serverlocation + "/")
	sg=message_board_to_sioc.message_board_to_sioc('message_board.db')

	httpd=simple_server.WSGIServer((server_addr, server_port),simple_server.WSGIRequestHandler)
	httpd.set_app(application)
	print "Serving on: " + serverlocation + "..."
	httpd.serve_forever()
