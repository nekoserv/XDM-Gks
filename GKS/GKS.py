# Author: Torf
# URL: https://github.com/torf/XDM-Gks
#
# This file is part of XDM: eXtentable Download Manager.
#
# XDM: eXtentable Download Manager. Plugin based media collection manager.
# Copyright (C) 2013  Dennis Lutter
#
# XDM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# XDM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

from xdm.plugins import *
from lib import requests
from xdm import helper
from xml.dom.minidom import parseString
from xml.dom.minidom import Node
import unicodedata
import re

class GKS(Indexer):
    version = "0.4"
    identifier = "me.torf.gks"
    _config = {'authkey': '',
               'enabled': True }

    types = ['de.lad1337.torrent']

    def _get_xml_text(self, node):
        text = ""
        for child_node in node.childNodes:
            if child_node.nodeType in (Node.CDATA_SECTION_NODE, Node.TEXT_NODE):
                text += child_node.data
        return text.strip()

    def _baseUrlMobile(self):
        return "https://gks.gs/mob/"

    def _baseUrlTorrent(self):
        return self._baseUrlMobile() + "gettorrents.php"

    def _baseUrlRss(self):
        return "https://gks.gs/rss/search/"

    def searchForElement(self, element):
        payload = {'category': '16'}

        downloads = []
        terms = '+'.join(element.getSearchTerms())
        
        payload['q'] = terms
        
        r = requests.get(self._baseUrlRss(), params=payload, verify=False)
        log.info("Gks final search for terms %s url %s" % (terms, r.url))
        
        response = unicodedata.normalize('NFKD', r.text).encode('ASCII', 'ignore')
        parsedXML = parseString(response)
        
        channel = parsedXML.getElementsByTagName('channel')[0]
        items = channel.getElementsByTagName('item')
        
        hasItem = False
        
        for item in items:
            title = self._get_xml_text(item.getElementsByTagName('title')[0])
            url = self._get_xml_text(item.getElementsByTagName('link')[0])
            ex_id = self._getTorrentId(url)
            
            if not ex_id == '':
                log.info("%s found on Gks.gs: %s" % (element.type, title))
                hasItem = True
                d = Download()
                d.url = self._getTorrentUrl(ex_id)
                d.name = title
                d.element = element
                d.size = 0
                d.external_id = ex_id
                d.type = 'de.lad1337.torrent'
                downloads.append(d)
            
        if hasItem == False:
            log.info("No search results for %s" % term)
                    
        return downloads

    def _testConnection(self, authkey):
        payload = {'k': authkey }
        
        try:
            r = requests.get(self._baseUrlMobile(), params=payload, verify=False)
        except:
            log.error("Error during test connection on $s" % self)
            return (False, {}, 'Please check network!')
        
        response = unicodedata.normalize('NFKD', r.text).encode('ASCII', 'ignore')
        if response == "Bad Key":
            return (False, {}, 'Wrong AuthKey !')
        
        return (True, {}, 'Connection made!')
    _testConnection.args = ['authkey']

    def _getTorrentId(self, uploadLink):
        match = re.search(r'torrent/(\d+)/', uploadLink)
        if match:
            return match.group(1)
        else:
            log.error("Can't find id of the torrent in %s" % uploadLink)
        return ''
    
    def _getTorrentUrl(self, torrentId):
        return "%s?k=%s&id=%s" % (self._baseUrlTorrent(), self.c.authkey, torrentId)
    
    config_meta = {'plugin_desc': 'Gks.gs torrent indexer.',
                   'plugin_buttons': {'test_connection': {'action': _testConnection, 'name': 'Test connection'}}}