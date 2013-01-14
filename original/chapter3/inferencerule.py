        
class InferenceRule:
    def getqueries(self):
        return None
    
    def maketriples(self,binding):
        return self._maketriples(**binding)


class WestCoastRule(InferenceRule):
    def getqueries(self):
        sfoquery=[('?company','headquarters','San_Francisco_California')]
        seaquery=[('?company','headquarters','Seattle_Washington')]
        laxquery=[('?company','headquarters','Los_Angelese_California')]
        porquery=[('?company','headquarters','Portland_Oregon')]
        
        return [sfoquery,seaquery,laxquery,porquery]

    def _maketriples(self,company):
        return [(company,'on_coast','west_coast')]

class EnemyRule(InferenceRule):
    def getqueries(self):
        partner_enemy=[('?person','enemy','?enemy'),
                       ('?rel','with','?person'),
                       ('?rel','with','?partner')]
        
        return [partner_enemy]

    def _maketriples(self,person,enemy,rel,partner):
        return [(partner,'enemy',enemy)]


import urllib
class GeocodeRule(InferenceRule):
    def getqueries(self):
         address_query=[('?place','address','?address')]
         
         return [address_query]
    
    def _maketriples(self,place,address):
    
        url='http://rpc.geocoder.us/service/csv?address=%s' % urllib.quote(address)
        con=urllib.urlopen(url)
        data=con.read()
        con.close()
        
        parts=data.split(',')
        if len(parts)>=5:
            return [(place,'longitude',parts[0]),
                    (place,'latitude',parts[1])]
        else:
            # Couldn't geocode this address
            return []

class CloseToRule(InferenceRule):
    
    def __init__(self,place,graph):
        self.place=place
        laq=list(graph.triples((place,'latitude',None)))
        loq=list(graph.triples((place,'longitude',None)))
        
        if len(laq)==0 or len(loq)==0:
            raise "Exception","%s is not geocoded in the graph" % place
        
        self.lat=float(laq[0][2])
        self.long=float(loq[0][2])
    
    def getqueries(self):
        geoq=[('?place','latitude','?lat'),('?place','longitude','?long')]
        return [geoq]
    
    def _maketriples(self,place,lat,long):
        # Formula for distance in miles from geocoordinates
        distance=((69.1*(self.lat-float(lat)))**2 + (53*(self.lat-float(lat)))**2)**.5
        
        # Are they less than a mile apart
        if distance<1:
            return [(self.place,'close_to',place)]
        else:
            return [(self.place,'far_from',place)]

class TouristyRule(InferenceRule):
    def getqueries(self):
        tr=[('?ta','is_a','Tourist Attraction'),
            ('?ta','close_to','?restaurant'),
            ('?restaurant','is_a','restaurant'),
            ('?restaurant','cost','cheap')] 
        return [tr]
    def _maketriples(self,ta,restaurant):
        return [(restaurant,'is_a','touristy restaurant')]

