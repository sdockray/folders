# -*- coding: utf-8 -*-
import os, sys, re  
import mimetypes
import ConfigParser

import PIL
from PIL import Image
import markdown2
import cherrypy
from cherrypy.lib.static import serve_file


config_filename = 'settings.cfg'

default_settings = {
	'site_title': 'folders',
	'files_dir': '.',
	'cache_dir': '.flattened',
	'max_size': 1024,
	'index_file': 'index.md',
	'template_file': '_template.html',
	'use_cache': "True",
}


def cache_set(path, content):
	''' Writes content to the cache '''
	if not path:
		path = (index_file,)
	cached_loc = os.path.join(files_dir, cache_dir, *path)
	if not os.path.exists(os.path.dirname(cached_loc)):
		os.makedirs(os.path.dirname(cached_loc))
	with open(cached_loc, 'w') as f:
		f.write(content.encode('utf-8').strip())


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


def serve_image(f, try_cache=True, max_dim=None):
	''' Serves an image, trying from a resized cache by default '''
	if not use_cache or not try_cache:
		return serve_file(f)
	else:
		cached_loc = os.path.join(files_dir, cache_dir, f.replace(files_dir+'/', ''))
		if os.path.exists(cached_loc):
			return serve_file(cached_loc)
		else:
			try:
				max_dim = max_dim or max_size
				image = Image.open(f)
				image.thumbnail((max_dim, max_dim), PIL.Image.ANTIALIAS)
				image.save(cached_loc)
				return serve_file(cached_loc)
			except:
				return serve_file(f)


def is_html(f):
	''' Is f an html file? '''
	try:
		return 'text/html' in mimetypes.guess_type(f)[0]
	except:
		return False


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


def try_file(path):
	''' Tries to return an existing file - html, static image, or download '''
	p = os.path.join(files_dir, *path)
	if is_image(p):
		return serve_image(p)
	elif is_html(p):
		return open(p)
	elif is_download(p):
		return serve_file(p, "application/x-download", "attachment")
	raise Exception("Failed to serve a file")


def read_md_as_html(f):
	''' Reads a markdown file as html '''
	if os.path.exists(f):
		return markdown2.markdown(open(f).read())
	return ''


def extract_title(f, default):
	''' Extracts a title from a markdown file (or directory containing an index file) '''
	if os.path.isdir(f):
		f = os.path.join(f, index_file)
	if os.path.isfile(f) and f.endswith('.md'):
		try:
			contents = open(f).read()
			m = re.search('^#{1}([^#].*)$', contents, re.MULTILINE)
			if m:
				return m.group(1).strip()
		except:
			pass
	return default


def extract_description(f, default):
	''' Extracts a description from a markdown file (or directory containing an index file) '''
	if os.path.isdir(f):
		f = os.path.join(f, index_file)
	if os.path.isfile(f) and f.endswith('.md'):
		try:
			contents = open(f).read()
			m = re.search('^#{2,6}([^#].*)$', contents, re.MULTILINE)
			if m:
				return m.group(1).strip()
		except:
			print 'exception'
			pass
	return default


def files_list_as_html(d, base=[]):
	''' Lists directories in a directory as an html list '''
	dirs = [o for o in os.listdir(d) if not is_image(os.path.join(d,o)) and not o.startswith('_') and not o.startswith('.') and not o==index_file]
	md = ''
	for dir in sorted(dirs):
		based = base + (dir,)
		md = "%s+ [%s](%s) %s\n" % (md, extract_title(os.path.join(d, dir),dir), "/"+'/'.join(based), extract_description(os.path.join(d, dir),''))
	return markdown2.markdown(md)


def list_images_as_html(d, base=[]):
	''' Lists directories in a directory as html '''
	imgs = [o for o in os.listdir(d) if is_image(os.path.join(d,o)) and not o.startswith('_')]
	md = ''
	for i in sorted(imgs):
		based = base + (i,)
		md = "%s+ ![%s](%s)\n" % (md, i, "/"+'/'.join(based))
	return markdown2.markdown(md)


def every_image_as_link():
	''' Show every image (recursively to a maximum depth?) as a link to the 1st level directory '''
	# First grab every image 
	images = []
	for dirpath, dirnames, filenames in os.walk(files_dir):
		for filename in [f for f in filenames if is_image(f) and not f.startswith('_')]:
			images.append((os.path.join(dirpath, filename), dirpath.replace(files_dir,'')))
	print images


def breadcrumb_as_html(path, separator=' / '):
	''' Spits out a ul style breadcrumb '''
	p_so_far = []
	breadcrumb = ['[%s](/)' % site_title]
	for p in path:
		p_so_far.append(p)
		title = extract_title(os.path.join(files_dir, *p_so_far),p)
		url = '/' + '/'.join(p_so_far)
		breadcrumb.append('[%s](%s)'%(title, url))
	return markdown2.markdown(separator.join(breadcrumb))


def merge_template(title, content, files, images, body_classes=None, breadcrumb=None):
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
	if body_classes:
		html = html.replace('{{body_classes}}', body_classes)
	if breadcrumb:
		html = html.replace('{{breadcrumb}}', breadcrumb)
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
	# build body classes
	body_classes = ' '.join([p.lower().replace(' ','-') for p in path]) or 'hohohome'
	# add in breadcrumb
	breadcrumb = breadcrumb_as_html(path)
	try:
		html = merge_template(title, md, files, imgs, body_classes=body_classes, breadcrumb=breadcrumb)
		if use_cache:
			cache_set(cache_path, html)
		return html
	except:
		raise Exception("Failed to build page")


def page_404():
	''' A 404 page '''
	# @todo: make this like template, where it can be overridden
	return '404'


def load_config():
	''' Try and load a configuration file '''
	import traceback
	for s in default_settings:
		globals()[s] = default_settings[s]
	config_loc = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_filename)
	print "Attempting to load configuration settings from ",config_loc
	try:
		config = ConfigParser.RawConfigParser(default_settings)
		config.read(config_loc)
		for s in default_settings:
			if s=='use_cache':
				globals()[s] = config.getboolean('app', s)
			else:
				globals()[s] = config.get('app', s)
			print "Setting ",s," to ",config.get('app', s)
		print "Loading config, setting directory to ",files_dir
	except:
		#print(traceback.format_exc())
		print "Failed to load from external config file... using defaults"


# Gives liberated content to the masses
class Folders(object):
	@cherrypy.expose
	def default(self, *args, **kwargs):
		# First check if it's an image (or downloadable file)
		try:
			return try_file(args)
		except:
			pass
		# Try to get the markup page from cache
		if use_cache:
			try:
				return cache_get(args)
			except:
				pass
		# If it's not in cache, it needs to be generated - and if it can't be, then 404!
		try:
			return make_page(args)
		except:
			return page_404() 


# Starting things up
if __name__ == '__main__':
	load_config()
	try:
		app = cherrypy.tree.mount(Folders(), '/')
		cherrypy.quickstart(app)
	except:
		print "Folders server couldn't start :("
