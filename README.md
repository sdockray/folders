#Folders#

This software runs http://folders.e-rat.org

I wrote this in order to automatically generate a website from a Dropbox folder.
It uses CherryPy as the web server and it can be run under wsgi. 

The basic idea is that for any particular folder, a webpage can be generated that shows some text, a list of folders and files, and all the images. It is very rudimentary (for example, there are no image captions) but it is also very quick. Just add content into a folder.

_Guide_
+ You need to create folders/settings.cfg and set the following:
```
[app]
files_dir=/absolute/path/to/your/content
site_title=Your Site Title
```
+ If you create an index.md file, its contents will be the text.
+ Any .md file will be parsed as Markdown.
+ Any image will be served as an image.
+ Other files will be sent for download.
+ You can create your own _template.html file and put it into your content directory to override the included template.
+ Any folders, files, or images that begin with a . or an _ will not appear in listings.
+ Listings will be alphabetical.
+ When listing a folder, the folder title will be used. If there is an index.md file in that folder and there is a heading, then that heading will be used as the title.
+ A subheading will be used for text after the title link.
+ The site is cached in .flattened - you should delete that directory after you've made changes 


_To install_
```
git clone https://github.com/sdockray/folders.git
cd folders
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
Figure out where the folder is that you want to make a website from.
Make sure the app will have permissions on that directory!
```
nano folders/settings.cfg (see Guide above)
```
You can run this in two ways; good for testing:
```
python folders/server.py
```
Or, I run this with nginx and uwsgi (emperor). Here is my ini file:
```
[uwsgi]
#application's base folder
base = /where/you/installed/this/app
chdir = /where/you/installed/this/app

#python module to import
module = folders.uwsgi

master = True
vacuum = True
processes = 4

venv = %(base)/venv
home = %(base)/venv
pythonpath = %(base)

#socket file's location
socket = /tmp/%n.sock

#permissions for the socket file
chmod-socket    = 666

#location of log files
logto = /var/log/uwsgi/%n.log
```
And my nginx server config is just this:
```
server {
    listen      80;
    server_name folders.e-rat.org;
    charset     utf-8;

    location / { try_files $uri @app; }

    location @app {
        include uwsgi_params;
        uwsgi_pass unix:/tmp/whatever.your.socket.is.above.sock;
        uwsgi_read_timeout 300;
    }
}
```