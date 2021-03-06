import common, urllib2, redirect_follower
import desitvbox, desitashan, desirulez

global_request_timeout = 10

GOOD_RESPONSE_CODES = ['200','206']

BANNED_KEYWORDS = ['File Does not Exist','Has Been Removed','Content removed','Content rejected','Content removed','Content rejected','This video got removed','File was deleted','We are sorry','copyright violation','File Not Found']

####################################################################################################
# Get HTTP response code (200 == good)
@route(common.PREFIX + '/gethttpstatus')
def GetHttpStatus(url):
	try:
		conn = urllib2.urlopen(url, timeout = global_request_timeout)
		resp = str(conn.getcode())
	except StandardError:
		resp = '0'
	#Log(url +' : HTTPResponse = '+ resp)
	return resp


####################################################################################################
# Get HTTP response code (200 == good)
@route(common.PREFIX + '/followredirectgethttpstatus')
def FollowRedirectGetHttpStatus(url):
	try:
		response = GetRedirectingUrl(url, url)
		if response <> None:
			resp = str(response.getcode())
	except:
		resp = '0'
	#Log(url +' : HTTPResponse = '+ resp)
	return resp

####################################################################################################
# Gets the redirecting url
@route(common.PREFIX + '/getredirectingurl')
def GetRedirectingUrl(url, rurl):

	#Log("Url ----- : " + url)
	redirectUrl = url
	try:
		response = redirect_follower.GetRedirect(url, rurl, global_request_timeout)
		if response <> None:
			redirectUrl = response.geturl()
	except:
		redirectUrl = url

	#Log("Redirecting url ----- : " + redirectUrl)
	return redirectUrl

####################################################################################################
# checks if USS is installed or not
def is_uss_installed():
    """Check install state of UnSupported Services"""

    identifiers = list()
    plugins_list = XML.ElementFromURL('http://127.0.0.1:32400/:/plugins', cacheTime=0)

    for plugin_el in plugins_list.xpath('//Plugin'):
        identifiers.append(plugin_el.get('identifier'))

    if 'com.plexapp.system.unsupportedservices' in identifiers:
        return True
    return False

####################################################################################################
# search array item's presence in string
@route(common.PREFIX + "/isarrayiteminstring")
def IsArrayItemInString(arr, mystr, case_match=True, exact=False):

	for item in arr:
		if not case_match:
			item = item.lower()
			mystr = mystr.lower()
		if exact:
			if item == mystr and mystr.startswith(item):
				return True
		else:
			if item in mystr and mystr.startswith(item):
				return True

	return False

####################################################################################################
# search array item's presence in string
@route(common.PREFIX + "/isarrayiteminstring")
def IsArrayItemInString2(arr, mystr, case_match=True):

	for item in arr:
		if not case_match:
			item = item.lower()
			mystr = mystr.lower()
		if item in mystr:
			#Log('-------------------' + item)
			return True

	return False

####################################################################################################
# search array item's presence in string
@route(common.PREFIX + "/getarrayitemmatchinstring")
def GetArrayItemMatchInString(arr, mystr, case_match=True, exact=False):

	c=-1
	for item in arr:
		c=c+1
		if not case_match:
			item = item.lower()
			mystr = mystr.lower()
		if exact:
			if item == mystr:
				return item, c
		else:
			if item in mystr:
				return item, c

	return (None, -1)

####################################################################################################
def GetTvURLSource(url, referer, date='', key=None):

	#Log(url)
	# This will take care of Meta redirects
	url = GetRedirectingUrl(url, url)
	#Log(url)
	html = HTML.ElementFromURL(url=url, headers={'Referer': referer})
	string = HTML.StringFromElement(html)

	try:
		if string.find('dailymotion.com') != -1:
			#Log('dailymotion')
			url = html.xpath("//iframe[contains(@src,'dailymotion')]/@src")[0]
		elif string.find('vmg.') != -1:
			#Log('vmg')
			url = html.xpath("//iframe[contains(@src,'vmg.')]/@src")[0]
		elif string.find('vidshare.') != -1:
			#Log('vidshare')
			url = html.xpath("//iframe[contains(@src,'vidshare.')]/@src")[0]
		elif string.find('cloudy.ec') != -1:
			#Log('cloudy')
			url = html.xpath("//iframe[contains(@src,'cloudy')]/@src")[0]
		elif string.find('playwire.com') != -1:
			#Log('playwire')
			url = html.xpath("//script/@data-config")[0]
		elif string.find('playu.') != -1:
			#Log('playu')
			url = html.xpath("//iframe[contains(@src,'playu.')]/@src")[0]
		elif len(html.xpath("//iframe[contains(@src,'openload.')]/@src")) > 0:
			#Log('openload')
			url = html.xpath("//iframe[contains(@src,'openload.co')]/@src")[0]
		else:
			#Log('Undefined src')
			orig_url = url
			if key <> None:
				url = html.xpath("//iframe[contains(@src,'"+key+"')]/@src")
				if len(url) > 0:
					url = url[0]
				else:
					url = orig_url
			if orig_url == url:
				url = html.xpath("//iframe[contains(@src,'embed')]/@src")
				if len(url) > 0:
					url = url[0]
				else:
					url = orig_url
			if orig_url == url:
				url = html.xpath(".//iframe//@src")
				if len(url) > 0:
					url = url[0]
					url = GetTvURLSource(url,url,date)
				else:
					url = orig_url
			if orig_url == url:
				url = 'none'
			else:
				referer = orig_url
	except:
		pass

	#Log(url)
	if url.startswith('//'):
		url = 'http:' + url

	url = CheckURLSource(url=url, referer=referer, key=key, string=string, html=html)

	return url

####################################################################################################
def CheckURLSource(url, referer, key=None, string=None, html=None, stringMatch=False):

	if string == None:
		string = HTTP.Request(url=url, headers={'Referer': referer}).content

	#Log('string: ' + string)

	try:
		if string.find('dailymotion.com') != -1:
			#Log('dailymotion')
			page = HTTP.Request(url, headers={'Referer': referer}).content
			if 'Content removed' in page or 'Content rejected' in page:
				url = 'disabled'
		elif string.find('vmg.') != -1:
			#Log('vmg')
			page = HTTP.Request(url, headers={'Referer': referer}).content
			if 'Content removed' in page or 'Content rejected' in page or 'This video got removed' in page or 'ERROR' in page:
				url = 'disabled'
		elif string.find('vidshare.') != -1:
			#Log('vidshare')
			try:
				page_data = HTML.ElementFromURL(url, headers={'Referer': referer})
				img = page_data.xpath("//img/@src")
				if len(img) == 0:
					url = 'disabled'
			except:
				url = 'disabled'
		elif string.find('cloudy.ec') != -1:
			#Log('cloudy')
			if not isValidCloudyURL(url):
				url = 'disabled'
		elif string.find('playwire.com') != -1:
			#Log('playwire')
			json = JSON.ObjectFromURL(url, headers={'Referer': referer})
			try:
				disabled = json['disabled']['message']
				if 'disabled' in disabled:
					url = 'disabled'
			except:
				pass
		elif string.find('playu.') != -1:
			#Log('playu')
			page = HTTP.Request(url, headers={'Referer': referer}).content
			if 'File was deleted' in page:
				url = 'disabled'
		elif (html <> None and len(html.xpath("//iframe[contains(@src,'openload.')]/@src")) > 0) and (stringMatch and string.find('openload.') != -1):
			#Log('openload')
			page = HTTP.Request(url, headers={'Referer': referer}).content
			if 'We are sorry' in page or 'copyright violation' in page:
				url = 'disabled'
		else:
			#Log('Testing Undefined src')
			if url <> 'none':
				page = HTTP.Request(url, headers={'Referer': referer}).content
				#Log(page)
				if IsArrayItemInString2(BANNED_KEYWORDS, page, False):
					url = 'disabled'
	except:
		pass

	return url

####################################################################################################

def isValidCloudyURL(url):

	vurl = False
	try:
		# use api www.cloudy.ec/api/player.api.php?'user=undefined&pass=undefined&file={file}&key={key}
		# https://github.com/Eldorados/script.module.urlresolver/blob/master/lib/urlresolver/plugins/cloudy.py

		content = unicode(HTTP.Request(url).content)
		elems = HTML.ElementFromString(content)
		key = elems.xpath("substring-before(substring-after(//script[@type='text/javascript'][3]//text(),'key: '),',')").replace("\"",'')
		file = elems.xpath("substring-before(substring-after(//script[@type='text/javascript'][3]//text(),'file:'),',')").replace("\"",'')

		furl = "http://www.cloudy.ec/api/player.api.php?'user=undefined&pass=undefined&file="+file+"&key="+key

		content = unicode(HTTP.Request(furl).content)
		#Log(vurl)
		if 'error' not in content:
			vurl = True
	except:
		vurl = False

	#Log("bool --------" + str(vurl))
	return vurl

######### PINS #############################################################################
# Checks a show to the Pins list using the url as a key
@route(common.PREFIX + "/checkpin")
def CheckPin(url):

	bool = False
	url = Dict['Plex-Pin-Pin'+url]
	if url <> None and url <> 'removed':
		bool = True
	return bool

######################################################################################
# Adds a Channel to the Pins list using the url as a key
@route(common.PREFIX + "/addpin")
def AddPin(site, title, url):

	Dict['Plex-Pin-Pin'+url] = site + 'Key4Split' + title + 'Key4Split' + url
	Dict.Save()
	return ObjectContainer(header = title, message='This Show has been added to your Pins.', title1='Pin Added')

######################################################################################
# Removes a Channel from the Pins list using the url as a key
@route(common.PREFIX + "/removepins")
def RemovePin(url):

	title = 'Undefined'
	keys = Dict['Plex-Pin-Pin'+url]
	if 'Key4Split' in keys:
		values = keys.split('Key4Split')
		title = values[1]
		Dict['Plex-Pin-Pin'+url] = None
		Dict.Save()
	return ObjectContainer(header=title, message='This Show has been removed from your Pins.', title1='Pin Removed')

######################################################################################
# Clears the Dict that stores the Pins list
@route(common.PREFIX + "/clearpins")
def ClearPins():

	for each in Dict:
		keys = Dict[each]
		if keys <> None and 'Key4Split' in str(keys):
			Dict[each] = None
	Dict.Save()
	return ObjectContainer(header="My Pins", message='Your Pins list will be cleared soon.', title1='Pins Cleared')

######################################################################################
# Pins
@route(common.PREFIX + "/pins")
def Pins(title):

	oc = ObjectContainer(title1 = title)

	for each in Dict:
		try:
			keys = Dict[each]
			#Log("keys--------- " + str(keys))
			if keys <> None and 'Key4Split' in str(keys):
				values = keys.split('Key4Split')
				site = values[0]
				title = values[1]
				channelUrl = values[2]

				if site == desitvbox.SITETITLE:
					oc.add(DirectoryObject(key = Callback(desitvbox.EpisodesMenu, url = channelUrl, title = title), title = title, thumb = R(desitvbox.SITETHUMB)))
				elif site == desitashan.SITETITLE:
					oc.add(DirectoryObject(key = Callback(desitashan.EpisodesMenu, url = channelUrl, title = title), title = title, thumb = R(desitashan.SITETHUMB)))
				elif site == desirulez.SITETITLE:
					oc.add(DirectoryObject(key = Callback(desirulez.EpisodesMenu, url = channelUrl, title = title), title = title, thumb = R(desirulez.SITETHUMB)))
		except:
			pass

	if len(oc) == 0:
		return ObjectContainer(header='Pins', message='No Pinned Shows Available', title1='Pins Unavailable')

	oc.objects.sort(key=lambda obj: obj.title)
	#add a way to clear pin list
	oc.add(DirectoryObject(
		key = Callback(ClearPins),
		title = "Clear All Pins",
		thumb = R(common.ICON_PIN),
		summary = "CAUTION! This will clear your entire Pins list!"
		)
	)

	return oc