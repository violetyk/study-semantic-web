# coding:utf-8
import simplegraph

graph = simplegraph.SimpleGraph()
graph.load('movies.csv')

print '映画BladeRunnerのIDをしらべる'
bladerunnerId = graph.value(None, 'name', 'Blade Runner')
print bladerunnerId


print '\n出演している俳優IDすべてを調べる'
bladerunnerActorIds = [actorId for _, _, actorId in graph.triples((bladerunnerId, 'starring', None))]
print bladerunnerActorIds

print '\n俳優の名前をルックアップ'
print [graph.value(actorId, 'name', None) for actorId in bladerunnerActorIds]

print '\nHarrison Ford出演の映画を調べる'
harrisonfordId = graph.value(None, 'name', 'Harrison Ford')
print [graph.value(movieId, 'name', None) for movieId, _, _ in graph.triples((None, 'starring', harrisonfordId))]

print '\nHarrison Ford出演でSteven Spielberg監督の映画'
spielbergId = graph.value(None, 'name', 'Steven Spielberg')
spielbergMovieIds = set([movieId for movieId, _, _ in graph.triples((None, 'directed_by', spielbergId))])
# print spielbergMovieIds

harrisonfordId = graph.value(None, 'name', 'Harrison Ford')
harrisonfordMovieIds = set([movieId for movieId, _, _ in graph.triples((None, 'starring', harrisonfordId))])
# print harrisonfordMovieIds

print spielbergMovieIds.intersection(harrisonfordMovieIds)
print [graph.value(movieId, 'name', None) for movieId in spielbergMovieIds.intersection(harrisonfordMovieIds)]
