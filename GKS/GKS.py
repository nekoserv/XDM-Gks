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

class GKS(Indexer):
    version = "0.2"
    identifier = "me.torf.gks"
    _config = {'enabled': True
               }

    types = ['de.lad1337.torrent']

    def _get_xml_text(self, node):
        text = ""
        for child_node in node.childNodes:
            if child_node.nodeType in (Node.CDATA_SECTION_NODE, Node.TEXT_NODE):
                text += child_node.data
        return text.strip()

    def _baseUrlRss(self):
        return "https://gks.gs/rss/search/"

    def searchForElement(self, element):
        payload = {'category': self._getCategory(element)}

        downloads = []
        terms = element.getSearchTerms()
        for term in terms:
            payload['q'] = term
            
            r = requests.get(self._baseUrlRss(), params=payload, verify=False)
            log.info("Gks final search for term %s url %s" % (term, r.url))
            
            response = unicodedata.normalize('NFKD', r.text).encode('ASCII', 'ignore')
            parsedXML = parseString(response)
            
            channel = parsedXML.getElementsByTagName('channel')[0]
            
            description = channel.getElementsByTagName('description')[0]
            description_text = self._get_xml_text(description).lower()
            
                       
            if "user can't be found" in description_text:
                log.error("Gks invalid digest, check your config")
                return downloads
            elif "invalid hash" in description_text:
                log.error("Gks invalid hash, check your config")
                return downloads
            else :
                items = channel.getElementsByTagName('item')
                hasItem = False
                for item in items:
                    hasItem = True
                    title = self._get_xml_text(item.getElementsByTagName('title')[0])
                    url = self._get_xml_text(item.getElementsByTagName('link')[0])
                    ex_id = self._get_xml_text(item.getElementsByTagName('guid')[0])
                
                    log.info("%s found on Gks.gs: %s" % (element.type, title))
                    d = Download()
                    d.url = url
                    d.name = title
                    d.element = element
                    d.size = 0
                    d.external_id = ex_id
                    d.type = 'de.lad1337.torrent'
                    downloads.append(d)
                if hasItem == False:
                    log.info("No search results for %s" % term)
                    
        return downloads



    config_meta = {'plugin_desc': 'Gks.gs torrent indexer.'}
