import cherrypy
from folders.folders import Folders

def application(environ, start_response):
	conf = {}
	cherrypy.config.update({
		'server.socket_port': 8084
	})
	app = cherrypy.tree.mount(Folders(), '/', config=conf)
	return cherrypy.tree(environ, start_response)
