import cherrypy
from folders.server import Folders, load_config

def application(environ, start_response):
	load_config()
	conf = {}
	cherrypy.config.update({
		'server.socket_port': 8084
	})
	app = cherrypy.tree.mount(Folders(), '/', config=conf)
	return cherrypy.tree(environ, start_response)
