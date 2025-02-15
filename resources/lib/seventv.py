#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import json
import urllib, urllib2
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import ast
import re
from inputstreamhelper import Helper
from hashlib import sha1

addon = xbmcaddon.Addon()
addon_handle = None
apiKey = addon.getSetting('apiKey')
if not apiKey:
    apiKey = '255d97968f286ada2c90548e34230628'
    addon.setSetting('apiKey', apiKey)

userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'


def playVideo(video_id, client_location, source_id=None, infoLabels=None):
    # Inputstream and DRM
    helper = Helper(protocol='mpd', drm='widevine')
    isInputstream = helper.check_inputstream()

    if not isInputstream:
        access_token = 'h''b''b''t''v'
        salt = '0''1''r''e''e''6''e''L''e''i''w''i''u''m''i''e''7''i''e''V''8''p''a''h''g''e''i''T''u''i''3''B'
        client_name = 'h''b''b''t''v'
    else:
        access_token = 'seventv-web'
        salt = '01!8d8F_)r9]4s[qeuXfP%'
        client_name = ''

    if source_id is None:
        source_id = 0
        json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s?access_token=%s&client_location=%s&client_name=%s' % (video_id, access_token, client_location, client_name)
        json_data = getUrl(json_url)

        if isInputstream:
          for stream in json_data['sources']:
            if stream['mimetype'] == 'application/dash+xml':
              if int(source_id) < int(stream['id']):
                source_id = stream['id']
        else:
          if json_data["is_protected"] == True:
            xbmc.executebuiltin('Notification("Inputstream", "DRM geschützte Folgen gehen nur mit Inputstream")')
            return
          else:
            for stream in json_data['sources']:
              if  stream['mimetype'] == 'video/mp4':
                if int(source_id) < int(stream['id']):
                    source_id = stream['id']

    client_id_1 = salt[:2] + sha1(''.join([str(video_id), salt, access_token, client_location, salt, client_name]).encode('utf-8')).hexdigest()

    json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s/sources?access_token=%s&client_location=%s&client_name=%s&client_id=%s' % (video_id, access_token, client_location, client_name, client_id_1)
    json_data = getUrl(json_url)
    server_id = json_data['server_id']

    # client_name = 'kolibri-1.2.5'
    client_id = salt[:2] + sha1(''.join([salt, video_id, access_token, server_id, client_location, str(source_id), salt, client_name]).encode('utf-8')).hexdigest()
    url_api_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s/sources/url?%s' % (video_id, urllib.urlencode({
        'access_token': access_token,
        'client_id': client_id,
        'client_location': client_location,
        'client_name': client_name,
        'server_id': server_id,
        'source_ids': str(source_id),
    }))

    json_data = getUrl(url_api_url)
    max_id = 0
    for stream in json_data["sources"]:
        ul = stream["url"]
        try:
            sid = re.compile('-tp([0-9]+).mp4', re.DOTALL).findall(ul)[0]
            id = int(sid)
            if max_id < id:
                max_id = id
                data = ul
        except:
          data = ul

    li = xbmcgui.ListItem(path='%s|%s' % (data, userAgent))
    li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    li.setProperty('inputstreamaddon', 'inputstream.adaptive')

    try:
        lic = json_data['drm']['licenseAcquisitionUrl']
        token = json_data['drm']['token']
        li.setProperty('inputstream.adaptive.license_key', '%s?token=%s|%s|R{SSM}|' % (lic, token, userAgent))
    except:
        pass

    if infoLabels and len(infoLabels) > 0:
        li.setInfo('video', infoLabels)

    xbmcplugin.setResolvedUrl(addon_handle, True, li)


def playLiveTV(property_name, client_location, access_token, client_token, infoLabels={}):
    # Inputstream and DRM
    helper = Helper(protocol='mpd', drm='widevine')
    if helper.check_inputstream() == False:
        return

    url = 'https://vas-live-mdp.glomex.com/live/1.0/getprotocols?%s' % (urllib.urlencode({
        'access_token': access_token,
        'client_location': client_location,
        'property_name': property_name,
        'client_token': client_token,
        'secure_delivery': 'true'
    }))

    data = getUrl(url)

    server_token = data.get('server_token')
    salt = '01!8d8F_)r9]4s[qeuXfP%'
    client_token = salt[:2] + sha1(''.join([property_name, salt, access_token, server_token, client_location, 'dash:widevine']).encode('utf-8')).hexdigest()

    url = 'https://vas-live-mdp.glomex.com/live/1.0/geturls?%s' % (urllib.urlencode({
        'access_token': access_token,
        'client_location': client_location,
        'property_name': property_name,
        'protocols': 'dash:widevine',
        'server_token': server_token,
        'client_token': client_token,
        'secure_delivery': 'true'
    }))

    data = getUrl(url)['urls']['dash']['widevine']

    li = xbmcgui.ListItem(path=data['url'] + "|" + userAgent)
    li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    li.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
    li.setProperty('inputstreamaddon', 'inputstream.adaptive')

    try:
        lic = data['drm']['licenseAcquisitionUrl']
        token = data['drm']['token']
        li.setProperty('inputstream.adaptive.license_key', '%s?token=%s|%s|R{SSM}|' % (lic, token, userAgent))
    except:
        pass

    if infoLabels and len(infoLabels) > 0:
        li.setInfo('video', ast.literal_eval(infoLabels))

    xbmcplugin.setResolvedUrl(addon_handle, True, li)


def getUrl(url, data=None, header=None, key=apiKey):
    xbmc.log('Get Url: %s' % url)

    opener = urllib2.build_opener()
    if header:
        opener.addheaders = header
    else:
        opener.addheaders = [('User-Agent', userAgent), ('key', key)]
    try:
        if data:
            content = opener.open(url, data=data).read()
        else:
            content = opener.open(url).read()
    except urllib2.HTTPError as e:
        xbmc.log('Error : %s' % e.read())

    opener.close()

    return json.loads(content)
