#!/usr/bin/env python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2016 Tom Wallroth & Tilman Boerner
#
# Project page:
#   http://fomori.org/cherrymusic/
# Sources on github:
#   http://github.com/devsnd/cherrymusic/
#
# CherryMusic is based on
#   jPlayer (GPL/MIT license) http://www.jplayer.org/
#   CherryPy (BSD license) http://www.cherrypy.org/
#
# licensed under GNU GPL version 3 (or later)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

import cmbootstrap
cmbootstrap.bootstrap()
import cherrymusicserver, cherrypy, os, sys, codecs
from cherrymusicserver.httphandler import HTTPHandler

import audiotranscode
MEDIA_MIMETYPES = audiotranscode.MIMETYPES.copy()
del audiotranscode

if not cherrymusicserver.pathprovider.configurationFileExists():
    filepath = cherrymusicserver.pathprovider.configurationFile()
    cherrymusicserver.create_default_config_file(filepath)

cherrymusicserver.run_general_migrations()

cherrymusicserver.setup_config()
cherrymusicserver.setup_services()

cherrypy.config.update({'log.screen': True})
resourcedir = os.path.abspath(cherrymusicserver.pathprovider.getResourcePath('res'))

cherrypy.config.update({
        'log.error_file': os.path.join(cherrymusicserver.pathprovider.getUserDataPath(), 'server.log'),
        'environment': 'production',
        'server.thread_pool': 30,
        'tools.sessions.on': True,
        'tools.sessions.timeout': int(cherrymusicserver.config.get('server.session_duration', 60 * 24)),
        'tools.sessions.locking': 'early'
    })

if cherrymusicserver.config['server.keep_session_in_ram']:
    pass
#        cherrypy.config.update({
#            'tools.sessions.storage_class': cherrypy.lib.sessions.MemcachedSession,
#            })
else:
    sessiondir = os.path.join(cherrymusicserver.pathprovider.getUserDataPath(), 'sessions')
    if not os.path.exists(sessiondir):
        os.mkdir(sessiondir)
    cherrypy.config.update({
            'tools.sessions.storage_class': cherrypy.lib.sessions.FileSession,
            'tools.sessions.storage_path': sessiondir,
        })

basedirpath = cherrymusicserver.config['media.basedir']
if sys.version_info < (3,0):
    basedirpath = codecs.encode(basedirpath, 'utf-8')
    scriptname = codecs.encode(cherrymusicserver.config['server.rootpath'], 'utf-8')
else:
    # fix cherrypy unicode issue (only for Python3)
    # see patch to cherrypy.lib.static.serve_file way above and
    # https://bitbucket.org/cherrypy/cherrypy/issue/1148/wrong-encoding-for-urls-containing-utf-8
    basedirpath = codecs.decode(codecs.encode(basedirpath, 'utf-8'), 'latin-1')
    scriptname = cherrymusicserver.config['server.rootpath']

httphandler = HTTPHandler(cherrymusicserver.config)
cherrypy.tree.mount(httphandler,
        scriptname,
        config={
            '/res': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': resourcedir,
                'tools.staticdir.index': 'index.html',
                'tools.caching.on': False,
                'tools.gzip.mime_types': ['text/html', 'text/plain', 'text/javascript', 'text/css'],
                'tools.gzip.on': True,
                },
            '/serve': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': basedirpath,
                # 'tools.staticdir.index': 'index.html',    if ever needed: in py2 MUST utf-8 encode
                'tools.staticdir.content_types': MEDIA_MIMETYPES,
                'tools.encode.on': True,
                'tools.encode.encoding': 'utf-8',
                'tools.caching.on': False,
                'tools.cm_auth.on': True,
                'tools.cm_auth.httphandler': httphandler,
                },
            '/favicon.ico': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': resourcedir + '/img/favicon.ico',
                }
            })
application = cherrypy.tree
