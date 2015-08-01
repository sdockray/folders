# -*- coding: utf-8 -*-
import os, sys, re  
import mimetypes
import ConfigParser

import markdown2
import cherrypy
from cherrypy.lib.static import serve_file


site_title = 'folders'
config_filename = 'settings.cfg'
files_dir = '/dir/to/content/here'
cache_dir = '.flattened'
index_file = 'index.md'
template_file = '_template.html'


def cache_set(path, content):
	''' Writes content to the cache '''
	if not path:
		path = (index_file,)
	cached_loc = os.path.join(files_dir, cache_dir, *path)
	if not os.path.exists(os.path.dirname(cached_loc)):
		os.makedirs(os.path.dirname(cached_loc))
	with open(cached_loc, 'w') as f:
		f.write(content)


def cache_get(path):
	''' Checks if the request is cached already '''
	if not path:
		path = (index_file,)
	cached_loc = os.path.join(files_dir, cache_dir, *path)
	if os.path.exists(cached_loc) and os.path.isdir(cached_loc):
		return cache_get(path + (index_file,))
	elif os.path.exists(cached_loc):
		return open(cached_loc)
	raise


def is_image(f):
	''' Is f an image? '''
	try:
		return 'image/' in mimetypes.guess_type(f)[0]
	except:
		return False


def is_download(f):
	''' Does this file need to be sent as a download '''
	try:
		return 'application/' in mimetypes.guess_type(f)[0]
	except:
		return False


def try_image(path):
	''' Tries to return a static image '''
	p = os.path.join(files_dir, *path)
	if is_image(p):
		return serve_file(p)
	elif is_download(p):
		return serve_file(p, "application/x-download", "attachment")
	raise


def read_md_as_html(f):
	''' Reads a markdown file as html '''
	if os.path.exists(f):
		return markdown2.markdown(open(f).read())
	return ''


def extract_title(f, default):
	''' Extracts a title from a markdown file (or directory containing an index file) '''
	if os.path.isdir(f):
		f = os.path.join(f, index_file)
	if os.path.isfile(f) and '.md' in f:
		try:
			contents = open(f).read()
			m = re.search('#{1,2}([^#.]*)#{1,2}', contents)
			if m:
				return m.group(1)
		except:
			pass
	return default


def files_list_as_html(d, base=[]):
	''' Lists directories in a directory as an html list '''
	dirs = [o for o in os.listdir(d) if not is_image(os.path.join(d,o)) and not o.startswith('_') and not o.startswith('.') and not o==index_file]
	md = ''
	for dir in sorted(dirs):
		based = base + (dir,)
		md = "%s+ [%s](%s)\n" % (md, extract_title(os.path.join(d, dir),dir), "/"+'/'.join(based))
	return markdown2.markdown(md)


def list_images_as_html(d, base=[]):
	''' Lists directories in a directory as an html list '''
	imgs = [o for o in os.listdir(d) if is_image(os.path.join(d,o)) and not o.startswith('_')]
	md = ''
	for i in sorted(imgs):
		based = base + (i,)
		md = "%s+ ![%s](%s)\n" % (md, i, "/"+'/'.join(based))
	return markdown2.markdown(md)


def merge_template(title, content, files, images):
	''' Merges 3 variables into a template - looks for a custom template in content folder '''
	custom_template = os.path.join(files_dir, template_file)
	if not os.path.exists(custom_template):
		custom_template = os.path.join(os.path.dirname(os.path.abspath(__file__)), template_file)
	tmpl = open(custom_template).read()
	html = tmpl.replace('{{site_title}}', site_title)
	html = html.replace('{{title}}', title)
	html = html.replace('{{content}}', content)
	html = html.replace('{{files}}', files)
	html = html.replace('{{images}}', images)
	return html
	

def make_page(path):
	''' Creates the page '''
	content_loc = os.path.join(files_dir, *path)
	# A directory index
	if os.path.exists(content_loc) and os.path.isdir(content_loc):
		file_loc = os.path.join(content_loc, index_file)
		cache_path = path + (index_file,)
		title = extract_title(file_loc, '/'.join(path))
		md = read_md_as_html(file_loc)
		files = files_list_as_html(content_loc, path)
		imgs = list_images_as_html(content_loc, path)
	# Assume a markdown file
	elif os.path.exists(content_loc) and os.path.isfile(content_loc):
		cache_path = path
		title = extract_title(content_loc, '/'.join(path))
		md = read_md_as_html(content_loc)
		imgs = ''
		files = ''
	try:
		html = merge_template(title, md, files, imgs)
		cache_set(cache_path, html)
		return html
	except:
		raise


def load_config():
	''' Try and load a configuration file '''
	try:
		global files_dir 
		global site_title
		config = ConfigParser.RawConfigParser({'title':site_title,'files_dir':files_dir})
	config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), config_filename))
		files_dir = config.get('app', 'files_dir')
		site_title = config.get('app', 'title')
		print "Loading config, setting directory to ",files_dir
	except:
		print "Failed to load from external config file... using defaults"


# Gives liberated content to the masses
class Folders(object):
	@cherrypy.expose
	def default(self, *args, **kwargs):
		# First check if it's an image
		try:
			return try_image(args)
		except:
			pass
		try:
			return cache_get(args)
		except:
			pass
		try:
			return make_page(args)
		except:
			return '404' 


# Starting things up
if __name__ == '__main__':
	load_config()
		
	try:
		app = cherrypy.tree.mount(Folders(), '/')
		cherrypy.quickstart(app)
	except:
		print "Folders server couldn't start :("
