# branch newscategories

# Fox News Live - by Rooster

import xbmcplugin,xbmcgui,xbmcaddon,time,urllib,urllib2,re,calendar,xml.sax.saxutils

# Constants
POLLING_INTERVAL_SECONDS = 300
URL = '87249' # Latest Videos

# Global vars
insertAtIndex = 0
playListNames = []
atEndOfPlaylist = False

class MyPlayer(xbmc.Player):
        polling = True
        
        def __init__ (self):
            xbmc.Player.__init__(self)
            MyPlayer.polling = True
        
        # Manually stopped by user
        def onPlayBackStopped(self):
            xbmc.log( "script.fox.news.live: Playback stopped" )
            MyPlayer.polling = False
            # Show the queue
            xbmc.executebuiltin( 'XBMC.ActivateWindow(10028 )' )
        
        # Last item in the queue has finished playing
        # Restart the queue from the first item
        def onPlayBackEnded(self):
            global atEndOfPlaylist
            if atEndOfPlaylist == True:
                atEndOfPlaylist = False
                xbmc.log( "script.fox.news.live: Restarting playlist" )
                xbmc.sleep(100) # Let things catch up
                play()

# Global player
player = MyPlayer()

def zuluToLocalDateTime(zdate,ztime):
    # TODO: Make this simpler by modifying the regex
    zuluDateTime = time.strptime(zdate + ' ' + ztime, "%m/%d/%Y %H:%M:%S")
    zuluSec = calendar.timegm(zuluDateTime)
    localDateTime = time.localtime(zuluSec)
    ltime = time.strftime("%a %I:%M%p", localDateTime)
    
    return ltime

def getItems(url):
    req = urllib2.Request('http://video.foxnews.com/v/feed/playlist/'+url+'.xml')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    a = re.compile('<title>(.+?)</title>\n          <media:content url="(.+?)">\n            <media:player url=".+?" />\n            <media:description>(.+?)</media:description>\n            <media:thumbnail><!\[\CDATA\[(.+?)]\]\></media:thumbnail>\n            <media:keywords>.+?</media:keywords>\n            <media:credit role=".+?" scheme=".+?">.+?</media:credit>\n            <mvn:assetUUID>.+?</mvn:assetUUID>\n            <mvn:mavenId></mvn:mavenId>\n            <mvn:creationDate>.+?</mvn:creationDate>\n            <mvn:airDate>(.+?)-(.+?)-(.+?)T(.+?)Z</mvn:airDate>\n')
    match = a.findall(link)
    return match

def doPolling(url):
    global insertAtIndex
    global playListNames
    
    if( MyPlayer.polling == False ):
        return
    
    xbmc.log( "script.fox.news.live: doPolling" )
    
    # Get the latest news from fox news
    match = getItems(url)
    if len( match ) == 0:
        return
    
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    newCount = 0
    curIndex = playlist.getposition()
    for name,url,desc,thumbnail,Year,Month,Day,Time in match:
        name = xml.sax.saxutils.unescape(name)
        localTime = zuluToLocalDateTime(Month + '/' + Day + '/' + Year, Time)
        label = localTime + ' - ' + name
        try:
            itemIndex = playListNames.index(label)
        except ValueError:
            # Insert the item next in the playlist (after what's currently playing)
            li = xbmcgui.ListItem(label, iconImage="DefaultVideo.png")
            li.setInfo('video', {'Title': label, 'Description':label})
            li.setThumbnailImage(thumbnail)
            playlist.add( url, li, curIndex + newCount + 1 )
            playListNames.append( label )
            
            curName = playlist[ curIndex + newCount ].getdescription()
            xbmc.log( "script.fox.news.live: Added '" + label + "' after '" + curName + "'" )
            
            # TODO: Remove the item after the insert (2nd item from what's currently playing) ??? or just let the playlist grow ???
            # Keep 20 videos in the queue.  If > 20 remove the oldest video.
            
            newCount += 1
            
    xbmc.log( "script.fox.news.live: Added " + str( newCount ) + " new items to the playlist" )
    
    if newCount > 0:
        xbmc.executebuiltin( 'Notification(Fox Top News,Found ' + str( newCount ) + ' new videos.,10000)' )
    
def play():
    global player
    global insertAtIndex
    
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    if playlist.size() > 0:
        xbmc.log( "script.fox.news.live: Playing playlist (queue)" )
        player.play(playlist)

def startQueue(url):
    global playListNames
    
    xbmc.log( "script.fox.news.live: Building playlist (queue)" )
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    
    match = getItems(url)
    if len( match ) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok('Fox Top News', 'No videos were found.  The feed might be down.')
        return
    
    addCount = 0
    for name,url,desc,thumbnail,Year,Month,Day,Time in match:
        name = xml.sax.saxutils.unescape(name)
        localTime = zuluToLocalDateTime(Month + '/' + Day + '/' + Year, Time)
        label = localTime + ' - ' + name
        li = xbmcgui.ListItem(label, iconImage="DefaultVideo.png")
        li.setInfo('video', {'Title': label, 'Description':label})
        li.setThumbnailImage(thumbnail)
        playlist.add( url, li )
        playListNames.append( label )
        addCount += 1
    
    xbmc.log( "script.fox.news.live: Added " + str( addCount ) + " items to the playlist" )
    
    insertAtIndex = 0

startQueue(URL)
play()

# Start the polling loop
# When onPlayBackStopped is detected the loop breaks and the script ends.
lastTime = time.time()
while MyPlayer.polling == True:
    xbmc.sleep(10)
    
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    
    # Check to see if we are at the end of the playlist
    # This will trigger onPlayBackEnded to restart the queue
    curPos = playlist.getposition()
    if curPos == playlist.size() - 1:
        atEndOfPlaylist = True
        
    # Check the time, if it's been POLLING_INTERVAL_SECONDS since the last polling then doPolling
    thisTime = time.time()
    if thisTime - lastTime >= POLLING_INTERVAL_SECONDS:
        doPolling(URL)
        lastTime = thisTime
        xbmc.log( "script.fox.news.live: " + str( len( playListNames ) ) + ":" + str( playlist.size() ) + " items in the playlist" )

xbmc.log( "script.fox.news.live: Done" )