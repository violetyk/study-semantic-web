
def triplestodot(triples,filename):
    out=file(filename,'w')
    out.write('graph "SimpleGraph" {\n')
    
    out.write('overlap = "scale";\n')
    for t in triples:
         out.write('"%s" -- "%s" [label="%s"]\n' % (t[0].encode('utf-8'),
                                                    t[2].encode('utf-8'),
                                                    t[1].encode('utf-8')))
                
    out.write('}')
    
def querytodot(graph,query,b1,b2,filename):

    out=file(filename,'w')
    out.write('graph "SimpleGraph" {\n')
    
    out.write('overlap = "scale";\n')
    results=graph.query(query)
    donelinks=set()
    for binding in results:
        if binding[b1]!=binding[b2]:
            n1,n2=binding[b1].encode('utf-8'),binding[b2].encode('utf-8')
            if (n1,n2) not in donelinks and (n2,n1) not in donelinks:
                out.write('"%s" -- "%s"\n' % (n1,n2))
                donelinks.add((n1,n2))
                
    out.write('}')
