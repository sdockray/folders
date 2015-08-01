#Folders#

This software run http://folders.e-rat.org

I wrote this in order to automatically generate a website from a Dropbox folder.
It uses CherryPy as the web server and it can be run under wsgi. 

The basic idea is that for any particular folder, a webpage can be generated that shows some text, a list of folders and files, and all the images. It is very rudimentary (for example, there are no image captions) but it is also very quick. Just add content into a folder.

_Guide_
+ You need to create folders/folders/settings.cfg and set the following:
```
[app]
files_dir=/absolute/path/to/your/content
title=Your Site Title
```
+ If you create an index.md file, its contents will be the text.
+ Any .md file will be parsed as Markdown.
+ Any image will be served as an image.
+ Other files will be sent for download.
+ You can create your own _template.html file and put it into your content directory to override the included template.
+ Any folders, files, or images that begin with a . or an _ will not appear in listings.
+ Listings will be alphabetical.
+ When listing a folder, the folder title will be used. If there is an index.md file in that folder and there is a heading, then that heading will be used as the title.
+ To install:
```
coming soon ...
```