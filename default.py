
# Fox News Live - by Rooster

import xbmcplugin,xbmcgui,xbmcaddon,time,urllib,urllib2,re,calendar,xml.sax.saxutils,random,sys
from urllib2 import HTTPError, URLError

# Constants
POLLING_INTERVAL_SECONDS = 300

# Settings
urls = []
__settings__ = xbmcaddon.Addon( id='plugin.video.fox.news.live' )
if __settings__.getSetting( "inc_latest_news" ) == "true":
    urls += [ '87185', '87249', '87485', '164000' ]
if __settings__.getSetting( "inc_buisiness" ) == "true":
    urls += [ '86883', '87013', '87061', '87308' ]
if __settings__.getSetting( "inc_entertainment" ) == "true":
    urls += [ '86871', '87261' ]
if __settings__.getSetting( "inc_sports" ) == "true":
    urls += [ '87484', '87857' ]
if __settings__.getSetting( "inc_science_and_tech" ) == "true":
    urls += [ '86861', '86976', '87019', '87079', '87090', '87264' ]

# Start the progress dialog
progress = xbmcgui.DialogProgress()
progress.create( "Fox News Live", "Finding videos..." )
progressPercent = 0

# Global vars
playListNames = []
atEndOfPlaylist = False

class MyPlayer( xbmc.Player ):
        polling = True
        
        def __init__ ( self ):
            xbmc.Player.__init__( self )
            MyPlayer.polling = True
        
        # Manually stopped by user
        def onPlayBackStopped( self ):
            xbmc.log( "script.fox.news.live: Playback stopped" )
            MyPlayer.polling = False
            # Show the queue
            xbmc.executebuiltin( 'XBMC.ActivateWindow(10028 )' )
        
        # Last item in the queue has finished playing
        # Restart the queue from the first item
        def onPlayBackEnded( self ):
            global atEndOfPlaylist
            if atEndOfPlaylist == True:
                atEndOfPlaylist = False
                xbmc.log( "script.fox.news.live: Restarting playlist" )
                xbmc.sleep( 1000 ) # Let things catch up.  Is there a better way to do this?
                play()

# Global player
player = MyPlayer()

def zuluToLocalDateTime( zdate, ztime ):
    zuluDateTime = time.strptime( zdate + ' ' + ztime, "%m/%d/%Y %H:%M:%S" )
    zuluSec = calendar.timegm( zuluDateTime )
    localDateTime = time.localtime( zuluSec )
    ltime = time.strftime( "%a %I:%M%p", localDateTime )
    
    return ltime

def getItems( url ):
    req = urllib2.Request( 'http://video.foxnews.com/v/feed/playlist/'+url+'.xml' )
    req.add_header( 'User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14' )
    try:
        response = urllib2.urlopen( req )
        link = response.read()
        response.close()
        a = re.compile( '<title>(.+?)</title>\n          <media:content url="(.+?)">\n            <media:player url=".+?" />\n            <media:description>(.+?)</media:description>\n            <media:thumbnail><!\[\CDATA\[(.+?)]\]\></media:thumbnail>\n            <media:keywords>.+?</media:keywords>\n            <media:credit role=".+?" scheme=".+?">.+?</media:credit>\n            <mvn:assetUUID>.+?</mvn:assetUUID>\n            <mvn:mavenId></mvn:mavenId>\n            <mvn:creationDate>.+?</mvn:creationDate>\n            <mvn:airDate>(.+?)-(.+?)-(.+?)T(.+?)Z</mvn:airDate>\n' )
        match = a.findall( link )
    except HTTPError, code:
        match = []
        xbmc.log( "script.fox.news.live: " + str( code ) + "  url=" + url )
    
    return match

def doPolling():
    global playListNames
    global urls
    
    if( MyPlayer.polling == False ):
        return
    
    xbmc.log( "script.fox.news.live: doPolling" )
    
    newCount = 0
    for url in urls:
        match = getItems( url )
        if len( match ) == 0:
            return
        
        newCount += addItems( match, True )
            
    xbmc.log( "script.fox.news.live: Inserted " + str( newCount ) + " new items to the playlist" )
    
    if newCount > 0:
        xbmc.executebuiltin( 'Notification(Fox Top News,Found ' + str( newCount ) + ' new videos.,10000)' )
    
def play():
    global player
    
    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    if playlist.size() > 0:
        xbmc.log( "script.fox.news.live: Playing playlist (queue)" )
        player.play( playlist )

def addItems( items, insert = False ):
    global progress, progressPercent
    
    addCount = 0
    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    curIndex = playlist.getposition()
    for name,url,desc,thumbnail,Year,Month,Day,Time in items:
        name = xml.sax.saxutils.unescape( name )
        localTime = zuluToLocalDateTime( Month + '/' + Day + '/' + Year, Time )
        label = localTime + ' - ' + name
        if label not in playListNames:
            name = xml.sax.saxutils.unescape( name )
            localTime = zuluToLocalDateTime( Month + '/' + Day + '/' + Year, Time )
            label = localTime + ' - ' + name
            li = xbmcgui.ListItem( label, iconImage="DefaultVideo.png" )
            li.setInfo('video', {'Title': label, 'Description':label} )
            li.setThumbnailImage( thumbnail )
            playListNames.append( label )
            if insert == True:
                playlist.add( url, li, curIndex + addCount + 1 )
            else:
                playlist.add( url, li )
                if progress.iscanceled():
                    sys.exit( 0 )
                progressPercent += 1
                progress.update( progressPercent )
            
            addCount += 1
    return addCount

def startQueue():
    global progress, progressPercent
    global playListNames
    global urls
    
    xbmc.log( "script.fox.news.live: Building playlist (queue)" )
    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    playlist.clear()
    
    addCount = 0
    match = []
    for url in urls:
        match += getItems( url )
        if progress.iscanceled():
            sys.exit( 0 )
        progressPercent += 1
        progress.update( progressPercent )
    
    random.shuffle( match )
    addCount += addItems( match, False )
    
    if addCount == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok( 'Fox Top News', 'No videos were found.  The feed might be down. Exiting script.' )
        MyPlayer.polling = False
        sys.exit( 0 )
    
    xbmc.log( "script.fox.news.live: Added " + str( addCount ) + " items to the playlist" )

# Initialize the queue and start playing
try:
    startQueue()
    progress.close()
    if MyPlayer.polling == True:
        play()
# sys.exit( 0 ) produces an error for some reason. This except is here to ignore it.
except:
    progress.close()
    pass

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
        doPolling()
        lastTime = thisTime
        xbmc.log( "script.fox.news.live: " + str( len( playListNames ) ) + ":" + str( playlist.size() ) + " items in the playlist" )

xbmc.log( "script.fox.news.live: Done" )