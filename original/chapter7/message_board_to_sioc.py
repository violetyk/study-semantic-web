import sqlite3,os
from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, BNode, Literal, RDF, URIRef
from urllib import urlopen

SIOC=Namespace('http://rdfs.org/sioc/ns#')
DC = Namespace("http://purl.org/dc/elements/1.1/")
DCTERMS = Namespace('http://purl.org/dc/terms/')
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

# Fake namespace for this message board
MB = Namespace('http://messageboard.com/')

# load the SQL file into a database
def load_data(sqlfile,dbfile):
    conn=sqlite3.connect(dbfile)
    cur=conn.cursor()
    
    f=file(sqlfile)
    for line in f:
        cur.execute(line)
    f.close()
    conn.commit()
    conn.close()

# convert the message board SQL database to SIOC
def message_board_to_sioc(dbfile):
    sg=ConjunctiveGraph()
    sg.bind('foaf',FOAF)
    sg.bind('sioc',SIOC)
    sg.bind('dc',DC)
    
    conn=sqlite3.connect(dbfile)
    cur=conn.cursor()

    # Get all the messages and add them to the graph
    cur.execute('SELECT id,title,content,user FROM messages')
    
    for id,title,content,user in cur.fetchall():
        mnode=MB['messages/%d' % id]
        sg.add((mnode,RDF.type,SIOC['Post']))
        sg.add((mnode,DC['title'],Literal(title)))
        sg.add((mnode,SIOC['content'],Literal(content)))
        sg.add((mnode,SIOC['has_creator'],MB['users/%s' % user]))        

    # Get all the users and add them to the graph
    cur.execute('SELECT id,name,email FROM users')
    for id,name,email in cur.fetchall():
        sg.add((mnode,RDF.type,SIOC['User']))
        unode=MB['users/%d' % id]
        sg.add((unode,FOAF['name'],Literal(name)))
        sg.add((unode,FOAF['email'],Literal(email)))        

    # Get subjects
    cur.execute('SELECT id,description FROM subjects')
    for id,description in cur.fetchall():
        sg.add((mnode,RDF.type,DCTERMS['subject']))
        sg.add((MB['subjects/%d' % id],RDFS['label'],Literal(description)))
    
    # Link subject to messages
    cur.execute('SELECT message_id,subject_id FROM message_subjects')
    for mid,sid in cur.fetchall():
        sg.add((MB['messages/%s' % mid],SIOC['topic'],MB['subjects/%s'] % sid))

    conn.close()

    return sg

if __name__=="__main__":
    if not os.path.exists('message_board.db'):
        load_data('message_board.sql','message_board.db')
    sg=message_board_to_sioc('message_board.db')
    
    print sg.serialize(format='xml')