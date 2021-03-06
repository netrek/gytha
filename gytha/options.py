from optparse import OptionParser

parser = OptionParser()
parser.add_option("-F", "--fullscreen",
                  action="store_true", dest="fullscreen", default=True,
                  help="force fullscreen mode on")
parser.add_option("--no-fullscreen", "--no-full-screen",
                  action="store_false", dest="fullscreen",
                  help="force fullscreen mode off")
parser.add_option("-s", "--server", "--host", dest="server",
                  help="netrek server to connect to")
parser.add_option("-p", "--port", type="int", dest="port", default="2592",
                  help="netrek player port number to connect to")
parser.add_option("--name", dest="name", default="",
                  help="character name, default guest")
parser.add_option("--password", dest="password", default="",
                  help="password for character name")
parser.add_option("--login", dest="login", default="gytha",
                  help="username to show on player list")
parser.add_option("--team", dest="team",
                  help="team to join")
parser.add_option("--mercenary",
                  action="store_true", dest="mercenary", default=False,
                  help="automatically join the least represented team")
parser.add_option("--ship", dest="ship",
                  help="ship class to request")
parser.add_option("--updates",
                  type="int", dest="updates", default="10",
                  help="updates per second from server, default 10")
parser.add_option("--tcp-only",
                  action="store_true", dest="tcp_only", default=False,
                  help="only use TCP, avoid UDP")
parser.add_option("--dump-server",
                  action="store_true", dest="sp", default=False,
                  help="dump server packet stream")
parser.add_option("--dump-client",
                  action="store_true", dest="cp", default=False,
                  help="dump client packet stream")
parser.add_option("--screenshots",
                  action="store_true", dest="screenshots", default=False,
                  help="generate publicity screenshots")
parser.add_option("--metaserver", action="store",
                  default='metaserver.netrek.org',
                  help="metaserver to query for games.")
parser.add_option("--metaserver-refresh-interval",
                  type="int", dest="metaserver_refresh_interval", default="30",
                  help="how many seconds between metaserver queries, default 30")
parser.add_option("--splash-time",
                  type="int", dest="splashtime", default="1000",
                  help="viewing delay for splash screen in milliseconds")
parser.add_option("--width",
                  type="int", dest="manual_width",
                  help="force specific resolution for testing")
parser.add_option("--height",
                  type="int", dest="manual_height",
                  help="force specific resolution for testing")
parser.add_option("--no-backgrounds",
                  action="store_true", dest="no_backgrounds", default=False,
                  help="turn off the background images")
parser.add_option("--halos",
                  action="store_true", dest="halos", default=False,
                  help="show experimental target navigation halos")
parser.add_option("--debug",
                  action="store_true", dest="debug", default=False,
                  help="display debugging data")
parser.add_option("--ubertweak",
                  action="store_true", dest="ubertweak", default=False,
                  help="enable ubertweak modifications")
parser.add_option("--sounds", dest="sounds", default="/usr/share/gytha/sounds",
                  help="path to sound effects")
