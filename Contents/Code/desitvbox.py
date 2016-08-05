
import common

SITETITLE = 'DesiTvBox'
SITEURL = 'http://www.desitvbox.me/'
SITETHUMB = 'icon-desitvbox.png'

PREFIX = common.PREFIX
NAME = common.NAME
ART = common.ART
ICON = common.ICON

####################################################################################################

@route(PREFIX + '/desitvbox/channels')
def ChannelsMenu(url):
	oc = ObjectContainer(title2=SITETITLE)

	html = HTML.ElementFromURL(url)


	for item in html.xpath("//ul[@rel='Main Menu']//li//a"):
		try:
			# Channel title
			channel = item.xpath("text()")[0]

			# Channel link
			link = item.xpath("@href")[0]
			if link.startswith("http") == False:
				link = SITEURL + link
			
			#Log("Channel Link: " + link)
		except:
			continue

		try:
			image = common.GetThumb(channel.lower())
		except:
			continue

		if channel.lower() in common.GetSupportedChannels():
			oc.add(DirectoryObject(key=Callback(ShowsMenu, url=link, title=channel), title=channel, thumb=image))
		
	# If there are no channels, warn the user
	if len(oc) == 0:
		return ObjectContainer(header=SITETITLE, message=L('ChannelWarning'))

	return oc
	
####################################################################################################

@route(PREFIX + '/desitvbox/showsmenu')
def ShowsMenu(url, title):
	oc = ObjectContainer(title2=title)
	#Log("Shows Menu: " + url + ":" + title)
	html = HTML.ElementFromURL(url)
	
	for item in html.xpath("//li[contains(@class, 'cat-item')]/a"):
		try:
			# Show title
			show = item.xpath("text()")[0]
			#Log("show name: " + show)
			# Show link
			link = item.xpath("@href")[0]
			if "completed-shows" in link:
				continue
			#Log("show link: " + link)
			if link.startswith("http") == False:
				link = SITEURL + link
			#og("final show link: " + link)	
		except:
			#Log("In Excpetion")
			continue

		# Add the found item to the collection
		oc.add(DirectoryObject(key=Callback(EpisodesMenu, url=link, title=show), title=show))
		
	# If there are no channels, warn the user
	if len(oc) == 0:
		return ObjectContainer(header=title, message=L('ShowWarning'))

	return oc

####################################################################################################

@route(PREFIX + '/desitvbox/episodesmenu')
def EpisodesMenu(url, title):
	oc = ObjectContainer(title2 = unicode(title))

	pageurl = url

	html = HTML.ElementFromURL(pageurl)
	
	for item in html.xpath("//div[@class='item_content']//h4//a"):
		try:
			# Episode title
			episode = unicode(str(item.xpath("text()")[0].strip()))
			
			# episode link
			link = item.xpath("@href")[0]
			if link.startswith("http") == False:
				link = SITEURL + link
			#Log("Episode: " + episode + " Link: " + link)
		except:
			continue

		# Add the found item to the collection
		if 'Watch Online' in episode:
			oc.add(PopupDirectoryObject(key=Callback(PlayerLinksMenu, url=link, title=episode, type=L('Tv')), title=episode))
	
	# Find the total number of pages
	pages = ' '
	try:
		pages = html.xpath("//ul[@class='page-numbers']//li//a[@class='page-numbers']/@href")[0]
	except:
		pass

	# Add the next page link if exists
	if ' ' not in pages:
		oc.add(DirectoryObject(key=Callback(EpisodesMenu, url=pages, title=title), title=L('Pages')))
	
	# If there are no channels, warn the user
	if len(oc) == 0:
		return ObjectContainer(header=title, message=L('EpisodeWarning'))

	return oc

####################################################################################################

@route(PREFIX + '/desitvbox/playerlinksmenu')
def PlayerLinksMenu(url, title, type):
	oc = ObjectContainer(title2 = unicode(title))
	
	# Add the item to the collection
	content = HTTP.Request(url).content
	#Log("PlayerLinksMenu " + url + ":" + title + ":" +  type)
	if type == "TV":
		if content.find('Flash HD') != -1:
			oc.add(DirectoryObject(key=Callback(EpisodeLinksMenu, url=url, title=title, type='Flash'), title='Flash', thumb=R('icon-playwire.png')))
		if content.find('Playu HD') != -1:
			oc.add(DirectoryObject(key=Callback(EpisodeLinksMenu, url=url, title=title, type='Playu'), title='PlayU HD', thumb=R('icon-playu.png')))
		if content.find('Letwatch HD') != -1:
			oc.add(DirectoryObject(key=Callback(EpisodeLinksMenu, url=url, title=title, type='Letwatch'), title='Letwatch HD', thumb=R('icon-letwatchus.png')))

	# If there are no channels, warn the user
	if len(oc) == 0:
		return ObjectContainer(header=title, message=L('PlayerWarning'))

	return oc

####################################################################################################

@route(PREFIX + '/desitvbox/episodelinksmenu')
def EpisodeLinksMenu(url, title, type):
	oc = ObjectContainer(title2 = unicode(title))

	html = HTML.ElementFromURL(url)
	
	# Summary
	summary = GetSummary(html)
	#Log("Summary:" + summary)
	items = GetParts(html, type)

	links = []

	for item in items:
		
		try:
			# Video site
			videosite = item.xpath("./text()")[0]
			Log("Video Site: " + videosite)
			# Video link
			link = item.xpath("./@href")[0]
			if link.startswith("http") == False:
				link = link.lstrip('htp:/')
				link = 'http://' + link
			if len(links) > 1 and link.find('Part 1') != -1:
				break

			# Get video source url and thumb
			link, thumb = GetTvURLSource(link,url,date)
			Log("Video Site: " + videosite + " Link: " + link + " Thumb: " + thumb)
		except:
			continue

		# Add the found item to the collection
		if link.find('playu') != -1 or link.find('vidshare') != -1  or link.find('playwire') != -1:
			links.append(URLService.NormalizeURL(link))
			#Log ('Link: ' + link)
			oc.add(VideoClipObject(
				url = link,
				title = videosite,
				thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)),
				summary = summary))
	
	# If there are no channels, warn the user
	if len(oc) == 0:
		return ObjectContainer(header=title, message=L('SourceWarning'))

	return oc

####################################################################################################

def GetTvURLSource(url, referer, date=''):

	if 'xpressvids.info' in url:
		url = url.replace('xpressvids.info','dramatime.me')
		
	html = HTML.ElementFromURL(url=url, headers={'Referer': referer})
	string = HTML.StringFromElement(html)

	if string.find('playu.net') != -1:
		url = html.xpath("//iframe[contains(@src,'playu.net')]/@src")[0]
		url = url.replace('playu.net','playu.me',1)
	elif string.find('vidshare.us') != -1:
		url = html.xpath("//iframe[contains(@src,'vidshare.us')]/@src")[0]
	elif string.find('playwire') != -1:
		url = html.xpath("//script/@data-config")[0]

	thumb = GetThumb(html)

	return url, thumb
	
####################################################################################################

def GetParts(html, keyword):
	items = html.xpath("//span[contains(text(),'"+keyword+"')]//following::p[1]//a")
	#Log("GetParts" + str(len(items)))
	if len(items) == 0:
		items = html.xpath("//span[contains(text(),'"+keyword+"')]//following::p[1]//a")
	return items



####################################################################################################

def GetSummary(html):
	try:
		summary = html.xpath("//h1[@class='entry_title entry-title']/text()")[0]
		#summary = summary.replace(" preview: ","",1)
		#summary = summary.replace("Find out in","",1)
	except:
		summary = None
	return summary

####################################################################################################

def GetThumb(html):
	try:
		thumb = html.xpath("//ul[@class='singlecontent']/li/p/img/@src")[0]
		#Log ('Thumb: ' + thumb)
	except:
		thumb = R(ICON)
	return thumb

