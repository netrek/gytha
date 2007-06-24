#!/usr/bin/python
"""
    pygame netrek
    Copyright (C) 2007  James Cameron (quozl@us.netrek.org)

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

http://www.cs.cmu.edu/afs/cs.cmu.edu/user/jch/netrek/humor

From: markiel@callisto.pas.rochester.edu (Andrew Markiel)
Newsgroups: rec.games.netrek
Subject: Re: Beginer!
Date: Thu, 4 Nov 93 00:33:05 GMT

STHOMAS@utcvm.utc.edu wrote:
>      I read many of the netrek postings and it seems real intresting.  Would
> anyone be willing to post instructions on how to get onto Netrek and begin
> playinf.  Particularly comand cods to get in.

Certainly! Most of them you can fish out of the code (it's written in sea),
but I can give you some pointers.

The idea behind netrek is that your race starts with 10 oysters, which
produce pearls (certain "agricultural" oysters produce pearls much faster
and thus are very valuable). The object of the game is to capture all of
the enemy's oysters by destroying all of their pearls and capturing them
with your own pearls. Each team has 8 fish attacking and defending the
oysters.

One of the most important ideas is to destroy enemy pearls (once you
destroy all the pearls on an enemy oyster, it becomes uncontrolled and
you can capture it by delivering one of your own pearls). You do this
by perching on the oyster and hitting 'b' (for bash), which causes
you to destroy the enemy pearls there.

If the oyster has more than 4 pearls, then it will be open and you
can attack all of them; however, once the oyster has less than 5, it
will close up with the pearls inside and you can't bash them anymore
(however, if you get lucky, you can bash several pearls in one swing
and thus reduce the number of pearls to below 4 before it closes up..
lobsters are very good at this).

Once the oyster is closed up, the only way to destroy the rest of the
pearls inside is to deliver your own pearls to the oyster. When you
put one of your own pearls next to the oyster, it will open up slightly
to crush it, which allows you to grab one of the ones inside and destroy
it before it closes again. Thus, for an oyster with 4 pearls, you need
to deliver 4 of your own pearls to be able to destroy all of the ones
inside, which makes the oyster uncontrolled. Then, if you put another
one of your own pearls inside, you will capture the oyster and it will
start making pearls for you.

The tricky bit is that to carry pearls around, you have to have a net
to carry them in. You make the net out of the scales of the enemy fish
that you defeat. Defeating one enemy fish gives you enough scales to
carry 2 pearls (unless you are in a lobster, in which case you have
enough to carry three pearls). They maximum number of pearls you can
carry depends on fish type. When your fish is defeated in combat,
you lose all your scales and any pearls you are carrying, and get sent
back to your spawning grounds to get a new fish. 

You fight either by tossing pebbles at the enemy fish, or by using
your scraper to scrape the scales off of them; note that after a
lot of fighting you get tired, and can't attack until you get more food
(indicated by your food stat, note that many other things, including
movement, consume food). You can get a little food anywhere, but certain
oysters provide food, which means that if you perch on a freindly food
oyster you will replace your food reserves much faster.

There are six types of fish you can control: salmon, dogfish, crabs,
bluefin, lobsters, and the mighty bass. You can always switch to
another fish by going back to your spawning ground and requesting
a new fish (and you keep whatever scales you had).

Salmon are small and fast. The have fast pebbles but very weak
scrapers, and they are too weak for most combat. They are best used
either for carrying pearls, or for bashing enemy pearls in their
backfield (every good team needs a salmon basher).

Dogfish are a little tougher than salmon, and also conserve food well.
However, they also have weak scrapers and thus aren't so useful in combat.
In fact, these fish tend to be seldom seen anymore.

Crabs are the workfish. They have lots of food and really good
scrapers, which makes them good for fighting enemy fish. Nowadays
these fish are used more than any other.

Bluefin are very big fish, but are slow and don't use food effectively,
so they tend to be useful only in close range fights near a food oyster.

Lobsters are an intersting sort of fish. They are very slow, but are
very good at bashing enemy pearls (if they get lucky, they can bash
4 pearls in one swing). They also can carry three pearls for each
enemy fish destroyed, which can be quite useful.

The bass is a very special fish. You side only can have one at a time,
and if it gets defeated it takes 30 minutes to put it back together
again. You also have a certain rank to take one. However, they are
very big and tough, and serve as a repository for pearls (where they
can't be bashed).

An interesting tactic is the bass og (it's short for ogtopus). This
is where your 8 fish surround the enemy bass (like the 8 arms of an
ogtopus). Then you wade in and beat the carp out of him. You can do
it with less fish, but it's not as effective.


Hope this helps. If you have more questions, the FAQ should be posted
in a few days.

> Stephen Thomas  University of Tennesee at Chattanooga

-Grey Elf
markiel@callisto.pas.rochester.edu

------------------------------

temporary release instructions

mkdir /tmp/netrek-client-pygame
cp -p try.py /tmp/netrek-client-pygame/netrek
cp `grep IMAGERY try.py|grep -v grep|cut -f2 -d:|sort|uniq` /tmp/netrek-client-pygame

"""
import sys, time, socket, select, struct, pygame, math

from optparse import OptionParser
parser= OptionParser()
parser.add_option("-s", "--server", "--host", dest="server",
                  help="netrek server to connect to")
parser.add_option("-p", "--port", type="int", dest="port", default="2592",
                  help="netrek player port number to connect to")
parser.add_option("--name", dest="name", default="",
                  help="character name, default guest")
parser.add_option("--password", dest="password", default="",
                  help="password for character name")
parser.add_option("--login", dest="login", default="pynt",
                  help="username to show on player list")
parser.add_option("--updates",
                  type="int", dest="updates", default="5",
                  help="updates per second from server, default 5")
parser.add_option("--dump",
                  action="store_true", dest="dump", default=False,
                  help="dump packet stream")
(opt, args) = parser.parse_args()
# FIXME: [--theme name] [--metaserver] [host]

# artwork specifications

# galaxy is 100000 x 100000 pixels
# tactical dimensions are one fifth of galactic dimensions

# tactical is 20000 x 20000 galactic pixels,
# shown by regular client on 500 x 500,
# therefore a ratio of 40

# ships are 20 x 20 on regular client,
# therefore ships are 800 x 800 galactic pixels

# regular client galactic of 500 x 500 means a ratio of 200,
# therefore a ship size of 4 x 4 pixels (text shown instead)

# torpedo explosion range is 350 galactic pixels,
# therefore 8.75 regular client pixels,
# which is just inside the drawn shield radius

# upscaling to 1000 x 1000 tactical means a new ratio of 80,
# therefore a ship size of 40 x 40 pixels

# upscaling to 1000 x 1000 galactic means a new ratio of 100,
# therefore a ship size of 8 x 8 pixels

# planet orbital radius is 800 galactic pixels (ORBDIST)
# planet attack radius is 1500 galactic pixels (PFIREDIST)
# on regular client, tactical planets are 28 pixels diameter
# on regular client, galactic planets are 14 pixels diameter
# planets are 30 x 30 on regular client tactical
# planets are 60 x 60 on this tactical

GWIDTH=100000

IND=0x0
FED=0x1
ROM=0x2
KLI=0x4
ORI=0x8

teams = {IND: 'ind', FED: 'fed', ROM: 'rom', KLI: 'kli', ORI: 'ori'}

teams_long = { IND: 'independent',
               FED: 'federation',
               ROM: 'romulan',
               KLI: 'klingon',
               ORI: 'orion'
             }

teams_numeric = {IND: -1, FED: 0, ROM: 1, KLI: 2, ORI: 3}

PFREE=0
POUTFIT=1
PALIVE=2
PEXPLODE=3
PDEAD=4
POBSERV=5

TFREE=0
TMOVE=1
TEXPLODE=2
TDET=3
TOFF=4
TSTRAIGHT=5

MAXTORP = 8

PFSHIELD           = 0x0001 # displayed on tactical
PFREPAIR           = 0x0002 # FIXME: display
PFBOMB             = 0x0004 # FIXME: display
PFORBIT            = 0x0008 # FIXME: display
PFCLOAK            = 0x0010 # FIXME: display
PFWEP              = 0x0020 # FIXME: display
PFENG              = 0x0040 # FIXME: display
PFROBOT            = 0x0080 # FIXME: display
PFBEAMUP           = 0x0100 # FIXME: display
PFBEAMDOWN         = 0x0200 # FIXME: display
PFSELFDEST         = 0x0400 # FIXME: display
PFGREEN            = 0x0800 # FIXME: display
PFYELLOW           = 0x1000 # FIXME: display
PFRED              = 0x2000 # FIXME: display
PFPLOCK            = 0x4000 # FIXME: display
PFPLLOCK           = 0x8000 # FIXME: display
PFCOPILOT         = 0x10000 # not to be displayed
PFWAR             = 0x20000 # FIXME: display
PFPRACTR          = 0x40000 # FIXME: display
PFDOCK            = 0x80000 # FIXME: display
PFREFIT          = 0x100000 # not to be displayed
PFREFITTING      = 0x200000 # FIXME: display
PFTRACT          = 0x400000 # FIXME: display
PFPRESS          = 0x800000 # FIXME: display
PFDOCKOK        = 0x1000000 # FIXME: display
PFSEEN          = 0x2000000 # FIXME: display
PFOBSERV        = 0x8000000 # not to be displayed
PFTWARP        = 0x40000000 # FIXME: display
PFBPROBOT      = 0x80000000 # FIXME: display

SCOUT=0
DESTROYER=1
CRUISER=2
BATTLESHIP=3
ASSAULT=4
STARBASE=5
SGALAXY=6
ATT=7

ships = { SCOUT:      'sc',
          DESTROYER:  'dd',
          CRUISER:    'ca',
          BATTLESHIP: 'bb',
          ASSAULT:    'as',
          STARBASE:   'sb',
          SGALAXY:    'ga',
          ATT:        'at'
        }

ships_long = { SCOUT:      'scout',
               DESTROYER:  'destroyer',
               CRUISER:    'cruiser',
               BATTLESHIP: 'battleship',
               ASSAULT:    'assault',
               STARBASE:   'starbase',
               SGALAXY:    'galaxy',
               ATT:        'ATT'
             }

ships_use = { SCOUT:      'very fast, very weak',
              DESTROYER:  'fast but weak',
              CRUISER:    'general purpose',
              BATTLESHIP: 'slow but strong',
              ASSAULT:    'bombs planets well',
              STARBASE:   'point defense',
              SGALAXY:    'for stuffing around',
              ATT:        'for cheating'
            }

PLREPAIR = 0x010
PLFUEL = 0x020
PLAGRI = 0x040
PLREDRAW = 0x080
PLHOME = 0x100
PLCOUP = 0x200
PLCHEAP = 0x400
PLCORE = 0x800
PLCLEAR = 0x1000

PHFREE=0x00
PHHIT =0x01 # ship
PHMISS=0x02 # whiff
PHHIT2=0x04 # plasma

def strnul(input):
    """ convert a NUL terminated string to a normal string
    """
    return input.split('\000')[0]

def galactic_scale(x, y):
    """ temporary coordinate scaling, galactic to screen
    """
    return (x/100, y/100)

def tactical_scale(x, y):
    """ temporary coordinate scaling, tactical to screen
    """
    return ((x - me.x) / 20 + 500, (y - me.y) / 20 + 500)

def galactic_descale(x, y):
    """ temporary coordinate scaling, screen to galactic
    """
    return (x*100, y*100)

def tactical_descale(x, y):
    """ temporary coordinate scaling, screen to tactical
    """
    return ((x - 500) * 20 + me.x, (y - 500) * 20 + me.y)

def descale(x, y):
    if ph_flight == ph_galactic:
        return galactic_descale(x, y)
    else:
        return tactical_descale(x, y)
    
def dir_to_angle(dir):
    """ convert netrek direction to angle, approximate
    (determines how many different ship rotation images are held)
    """
    return dir * 360 / 256 / 5 * 5

def xy_to_dir(x, y):
    global me
    if ph_flight == ph_galactic:
        (mx, my) = galactic_scale(me.x, me.y)
        return int((math.atan2(x - mx, my - y) / math.pi * 128.0 + 0.5))
    else:
        return int((math.atan2(x - 500, 500 - y) / math.pi * 128.0 + 0.5))
            
def team_decode(input):
    """ convert a team mask to a list
    """
    x = []
    if input & FED: x.append(teams[FED])
    if input & ROM: x.append(teams[ROM])
    if input & KLI: x.append(teams[KLI])
    if input & ORI: x.append(teams[ORI])
    return x

def race_decode(input):
    """ convert a race number to letter
    """
    if input == 0: return 'F'
    elif input == 1: return 'R'
    elif input == 2: return 'K'
    elif input == 3: return 'O'
    return 'I'

class Planet:
    """ netrek planets
        each server has a number of planets
        instances created as packets about the planets are received
        instances are listed in a dictionary of planets in the galaxy instance
    """
    def __init__(self, n):
        self.n = n
        self.sp_planet_loc(-10000, -10000, '')
        self.sp_planet(0, 0, 0, 0)
        self.tactical = PlanetTacticalSprite(self)
        self.galactic = PlanetGalacticSprite(self)

    def sp_planet_loc(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name

    def sp_planet(self, owner, info, flags, armies):
        self.owner = owner
        self.info = info
        self.flags = flags
        self.armies = armies

class Ship:
    """ netrek ships
        each server has a number of netrek ships, normally 32 (MAXPLAYER)
        instances created as packets about the ships are received
        instances are listed in a dictionary of ships in the galaxy instance
    """
    def __init__(self, n):
        self.n = n
        self.sp_flags_cumulative_flags = 0
        self.sp_you_cumulative_flags = 0
        self.sp_pl_login(0, '', '', '')
        self.sp_hostile(0, 0)
        self.sp_player_info(0, 0)
        self.sp_kills(0)
        self.sp_player(0, 0, -10000, -10000)
        self.sp_flags(0, 0)
        self.sp_pstatus(PFREE)
        self.tactical = ShipTacticalSprite(self)
        self.galactic = ShipGalacticSprite(self)

    def sp_you(self, hostile, swar, armies, tractor, flags, damage, shield,
               fuel, etemp, wtemp, whydead, whodead):
        # FIXME: handle other arguments
        self.flags = flags
        self.sp_you_cumulative_flags |= flags
        global me
        if not me:
            me = self
            print "SP_YOU me is set"
        else:
            if me != self:
                me = self
                print "SP_YOU me has changed"

    def sp_pl_login(self, rank, name, monitor, login):
        self.rank = rank
        self.name = name
        self.monitor = monitor
        self.login = login
        # FIXME: display this data

    def sp_hostile(self, war, hostile):
        self.war = war
        self.hostile = hostile
        # FIXME: display this data
    
    def sp_player_info(self, shiptype, team):
        self.shiptype = shiptype
        self.team = team
        # FIXME: display this data

    def sp_kills(self, kills):
        self.kills = kills
        # FIXME: display this data

    def sp_player(self, dir, speed, x, y):
        self.dir = dir_to_angle(dir)
        self.speed = speed
        self.x = x
        self.y = y
        # FIXME: display speed

    def sp_flags(self, tractor, flags):
        self.tractor = tractor
        self.flags = flags
        self.sp_flags_cumulative_flags |= flags
        # FIXME: display this data
        # FIXME: figure out if flags in SP_FLAGS is same as flags in SP_YOU

    def sp_pstatus(self, status):
        self.status = status
        # ship sprite visibility is brutally controlled by status
        # FIXME: PEXPLODE needs to be shown as an explosion
        # FIXME: do not show cloaked ships
        # FIXME: move visibility check to sprite class
        try:
            if status == PALIVE or status == PEXPLODE:
                self.galactic.show()
                self.tactical.show()
            else:
                self.galactic.hide()
                self.tactical.hide()
        except:
            # sprites do not exist on first call from own __init__
            # FIXME: check for attribute existence rather that use
            # brute force of exception handling
            pass

class Torp:
    """ netrek torps
        each netrek ship has eight netrek torps
        instances created as packets about the torps are received
        instances are listed in a dictionary of torps in the galaxy instance
    """
    def __init__(self, n):
        self.n = n
        self.ship = galaxy.ship(n / MAXTORP)
        self.explode = 0
        self.status = TFREE
        self.sp_torp_info(0, self.status)
        self.sp_torp(0, 0, 0)
        self.tactical = TorpTacticalSprite(self)
        #self.galactic = TorpGalacticSprite(self)

    def sp_torp_info(self, war, status):
        old = self.status
        
        self.war = war
        self.status = status
        
        try:
            if old == TFREE:
                if status != TFREE:
                    self.tactical.show()
            else:
                if status == TFREE:
                    self.tactical.hide()
                elif status == TEXPLODE:
                    self.explode = nt.time + 2
        except:
            pass

    def sp_torp(self, dir, x, y):
        self.dir = dir
        self.x = x
        self.y = y

class Phaser:
    """ netrek phasers
        each netrek ship has one netrek phaser
        instances created as packets about the phasers are received
        instances are listed in a dictionary of phasers in the galaxy instance
    """
    def __init__(self, n):
        self.n = n
        self.ship = galaxy.ship(n)
        self.status = PHFREE
        self.want = False
        self.have = False
        self.sp_phaser(0, 0, 0, 0, 0)

    def draw(self):
        self.have = True
        if self.status == PHMISS:
            s_phaserdamage = 100 # FIXME: CA is 100, others are different
            phasedist = 6000
            factor = phasedist * s_phaserdamage / 100
            angle = ( self.dir - 64 ) / 128.0 * math.pi
            tx = factor * math.cos(angle)
            ty = factor * math.sin(angle)
            (fx, fy) = (self.ship.x, self.ship.y)
            (tx, ty) = tactical_scale(fx + tx, fy + ty)
            (fx, fy) = tactical_scale(fx, fy)
        elif self.status == PHHIT2:
            (fx, fy) = (self.ship.x, self.ship.y)
            plasma.x = 100000 # FIXME: track plasma packets
            plasma.y = 100000
            (tx, ty) = tactical_scale(plasma.x, plasma.y)
        elif self.status == PHHIT:
            target = galaxy.ship(self.target)
            (tx, ty) = tactical_scale(target.x, target.y)
            (fx, fy) = tactical_scale(self.ship.x, self.ship.y)
        self.txty = (tx, ty)
        self.fxfy = (fx, fy)
        return pygame.draw.line(screen, (255, 255, 255), (fx, fy), (tx, ty))

    def undraw(self):
        self.have = False
        return pygame.draw.line(screen, (0, 0, 0), self.fxfy, self.txty)
        
    def sp_phaser(self, status, dir, x, y, target):
        old = self.status
        
        self.status = status
        self.dir = dir
        self.x = x
        self.y = y
        self.target = target

        if old == PHFREE:
            if self.status != PHFREE: self.want = True
        else:
            if self.status == PHFREE: self.want = False
        
class Galaxy:
    def __init__(self):
        self.planets = {}
        self.ships = {}
        self.torps = {}
        self.phasers = {}

    def planet(self, n):
        if not self.planets.has_key(n):
            planet = Planet(n)
            self.planets[n] = planet
        return self.planets[n]

    def ship(self, n):
        if not self.ships.has_key(n):
            self.ships[n] = Ship(n)
        return self.ships[n]

    def torp(self, n):
        if not self.torps.has_key(n):
            self.torps[n] = Torp(n)
        return self.torps[n]

    def phaser(self, n):
        if not self.phasers.has_key(n):
            self.phasers[n] = Phaser(n)
        return self.phasers[n]

    def phasers_undraw(self):
        r = []
        for n, phaser in self.phasers.iteritems():
            if phaser.have: r.append(phaser.undraw())
        return r
            
    def phasers_draw(self):
        r = []
        for n, phaser in self.phasers.iteritems():
            if phaser.want: r.append(phaser.draw())
        return r
    
    def nearest(self, x, y, things):
        """ return the nearest thing to input screen coordinates
        """
        x, y = descale(x, y)
        nearest = None
        minimum = GWIDTH**2
        for n, thing in things.iteritems():
            distance = (thing.x - x)**2 + (thing.y - y)**2
            if distance < minimum:
                nearest = thing
                minimum = distance
        return nearest

    def nearest_planet(self, x, y):
        """ return the nearest planet to input screen coordinates
        """
        return self.nearest(x, y, self.planets)

    def nearest_ship(self, x, y):
        """ return the nearest ship to input screen coordinates
        """
        return self.nearest(x, y, self.ships)

galaxy = Galaxy()
me = None

class IC:
    """ an image cache
    """
    def __init__(self):
        self.cache = {}
        self.cache_rotated = {}

    def read(self, name):
        try:
            path = '/usr/share/netrek-client-pygame/images/' 
            image = pygame.image.load(path + name)
        except:
            image = pygame.image.load(name)
        return pygame.Surface.convert_alpha(image)

    def get(self, name):
        if name not in self.cache:
            self.cache[name] = self.read(name)
        return self.cache[name]

    def get_rotated(self, name, angle):
        if (name, angle) not in self.cache_rotated:
            unrotated = self.get(name)
            rotated = pygame.transform.rotate(unrotated, -angle)
            self.cache_rotated[(name, angle)] = rotated
        return self.cache_rotated[(name, angle)]
        
ic = IC()
    
class FC:
    """ a font cache
    """
    def __init__(self):
        self.cache = {}

    def read(self, name, size):
        font = pygame.font.Font(name, size)
        return font

    def get(self, name, size):
        key = (name, size)
        if key not in self.cache:
            self.cache[key] = self.read(name, size)
        return self.cache[key]

fc = FC()

class MultipleImageSprite(pygame.sprite.Sprite):
    """ a sprite class consisting of multiple images overlaid
        the images are blitted over each other in the order they are added
    """
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

    def mi_begin(self):
        self.ml = []
        self.mr = None

    def mi_add(self, image, rect):
        self.ml.append((image, rect))
        if self.mr == None:
            self.mr = rect
        else:
            self.mr = pygame.Rect.union(self.mr, rect)
            
    def mi_add_image(self, image):
        rect = image.get_rect()
        self.mi_add(image, rect)

    def mi_commit(self):
        width = self.mr.width
        height = self.mr.height
        self.image = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        for x in self.ml:
            (image, rect) = x
            rect.center = (width/2, height/2)
            self.image.blit(image, rect)
        self.rect = self.image.get_rect()
    
class PlanetSprite(MultipleImageSprite):
    """ netrek planet sprites
    """
    def __init__(self, planet):
        self.planet = planet
        self.old_armies = planet.armies
        self.old_name = planet.name
        self.old_flags = planet.flags
        self.old_x = planet.x
        self.old_y = planet.y
        self.old_owner = planet.owner
        MultipleImageSprite.__init__(self)

class PlanetGalacticSprite(PlanetSprite):
    def __init__(self, planet):
        PlanetSprite.__init__(self, planet)
        self.pick()
        galactic.add(self)

    def pick(self):
        # IMAGERY: planet-???-30x30.png
        self.image = ic.get("planet-" + teams[self.planet.owner] + "-30x30.png")
        self.rect = self.image.get_rect()
        # FIXME: render planet name on screen
        # FIXME: render planet owner, flags and armies on screen

    def update(self):
        if self.planet.owner != self.old_owner:
            self.pick()
            self.rect.center = galactic_scale(self.planet.x, self.planet.y)
            self.old_owner = self.planet.owner
        if self.planet.x != self.old_x or self.planet.y != self.old_y:
            self.rect.center = galactic_scale(self.planet.x, self.planet.y)
            self.old_x = self.planet.x
            self.old_y = self.planet.y
            
class PlanetTacticalSprite(PlanetSprite):
    def __init__(self, planet):
        self.me_old_x = -1
        self.me_old_y = -1
        PlanetSprite.__init__(self, planet)
        self.pick()
        t_planets.add(self)

    def pick(self):
        self.mi_begin()
        # IMAGERY: planet-???.png
        image = ic.get("planet-" + teams[self.planet.owner] + ".png")
        self.mi_add_image(image)

        # IMAGERY: planet-overlay-*.png
        if self.planet.armies > 4 and self.planet.owner != me.team:
            self.mi_add_image(ic.get('planet-overlay-attack.png'))
            # FIXME: show attack ring for unscanned planets as well?
        if self.planet.armies > 4:
            self.mi_add_image(ic.get('planet-overlay-army.png'))
        if self.planet.flags & PLREPAIR:
            self.mi_add_image(ic.get('planet-overlay-repair.png'))
        if self.planet.flags & PLFUEL:
            self.mi_add_image(ic.get('planet-overlay-fuel.png'))
        # FIXME: cache the static flags surfaces here, they will rarely change

        image = pygame.Surface((120, 120), pygame.SRCALPHA, 32)
        font = fc.get(None, 24)
        message = "%s" % (self.planet.name)
        text = font.render(message, 1, (92, 92, 92))
        rect = text.get_rect(centerx=60, bottom=120)
        # FIXME: cache this surface here, it will rarely change
        image.blit(text, rect)
        self.mi_add_image(image)
        self.mi_commit()
        
    def update(self):
        if self.planet.owner != self.old_owner or \
               self.planet.name != self.old_name or \
               self.planet.flags != self.old_flags or \
               self.planet.armies != self.old_armies:
            self.pick()
            self.old_owner = self.planet.owner
            self.old_name = self.planet.name
            self.old_flags = self.planet.flags
            self.old_armies = self.planet.armies
            self.rect.center = tactical_scale(self.planet.x, self.planet.y)
        if self.planet.x != self.old_x or \
               self.planet.y != self.old_y or \
               me.x != self.me_old_x or \
               me.y != self.me_old_y:
            self.rect.center = tactical_scale(self.planet.x, self.planet.y)
            self.old_x = self.planet.x
            self.old_y = self.planet.y
            self.me_old_x = me.x
            self.me_old_y = me.y
        # FIXME: performance note, all planets are on the tactical
        # sprite list, but are off the screen, so there is processing
        # for all planets happening.  it may prove worthwhile to only
        # include planets on the tactical sprite list if they are
        # nearby.
            
class ShipSprite(MultipleImageSprite):
    def __init__(self, ship):
        self.ship = ship
        self.old_dir = ship.dir
        self.old_team = ship.team
        self.old_shiptype = ship.shiptype
        self.old_status = ship.status
        self.old_flags = ship.flags
        MultipleImageSprite.__init__(self)

class ShipGalacticSprite(ShipSprite):
    """ netrek ship sprites
    """
    def __init__(self, ship):
        ShipSprite.__init__(self, ship)
        self.pick()

    def update(self):
        if self.ship.dir != self.old_dir or self.ship.team != self.old_team or self.ship.shiptype != self.old_shiptype or self.ship.status != self.old_status:
            self.old_dir = self.ship.dir
            self.old_team = self.ship.team
            self.old_shiptype = self.ship.shiptype
            self.old_status = self.ship.status
            self.pick()
        self.rect.center = galactic_scale(self.ship.x, self.ship.y)

    def pick(self):
        # FIXME: obtain imagery for galactic view
        # IMAGERY: ???-8x8.png
        if self.ship.team != IND:
            self.image = ic.get_rotated(teams[self.ship.team]+"-8x8.png", self.ship.dir)
            self.rect = self.image.get_rect()
        
    def show(self):
        galactic.add(self)

    def hide(self):
        galactic.remove(self)

class ShipTacticalSprite(ShipSprite):
    """ netrek ship sprites
    """
    def __init__(self, ship):
        ShipSprite.__init__(self, ship)
        self.pick()

    def update(self):
        if self.ship.dir != self.old_dir or self.ship.team != self.old_team or self.ship.shiptype != self.old_shiptype or self.ship.status != self.old_status or self.ship.flags != self.old_flags:
            self.old_dir = self.ship.dir
            self.old_team = self.ship.team
            self.old_shiptype = self.ship.shiptype
            self.old_status = self.ship.status
            self.old_flags = self.ship.flags
            self.pick()
        self.rect.center = tactical_scale(self.ship.x, self.ship.y)

    def pick(self):
        self.mi_begin()
        if self.ship.status == PEXPLODE:
            # FIXME: animate explosion
            # FIXME: initial frames to show explosion developing over ship
            # IMAGERY: explosion.png
            self.mi_add_image(ic.get('explosion.png'))
        else:
            # FIXME: obtain imagery for galactic view
            # IMAGERY: ???-??-40x40.png
            try:
                self.mi_add_image(ic.get_rotated(teams[self.ship.team]+'-'+ships[self.ship.shiptype]+"-40x40.png", self.ship.dir))
            except:
                self.mi_add_image(ic.get('netrek.png'))

        # FIXME: filter for visibility by distance from me
        
        # ship number
        image = pygame.Surface((40, 40), pygame.SRCALPHA, 32)
        font = fc.get(None, 24)
        message = "%d" % (self.ship.n)
        text = font.render(message, 1, (255, 255, 255))
        rect = text.get_rect(center=(20, 20))
        # FIXME: cache this surface here, it will never change
        image.blit(text, rect)
        self.mi_add_image(image)
        
        if self.ship.status == PALIVE and self.ship.flags & PFSHIELD:
            # IMAGERY: shield-80x80.png
            self.mi_add_image(ic.get('shield-80x80.png'))
        
        if self.ship.status == PALIVE and self.ship.flags & PFCLOAK:
            # IMAGERY: ship-cloak.png
            self.mi_add_image(ic.get('ship-cloak.png'))
        
        # FIXME: show flag for PFROBOT, PFPRACTR or PFBPROBOT
        # FIXME: show flag for PFDOCKOK
        # FIXME: not show or show differently if PFCLOAK
        self.mi_commit()
        
    def show(self):
        t_players.add(self)

    def hide(self):
        t_players.remove(self)

class TorpSprite(pygame.sprite.Sprite):
    def __init__(self, torp):
        self.torp = torp
        self.old_status = torp.status
        pygame.sprite.Sprite.__init__(self)

class TorpTacticalSprite(TorpSprite):
    """ netrek torp sprites
    """
    def __init__(self, torp):
        TorpSprite.__init__(self, torp)
        self.teams = { FED: 'torp-fed.png', ROM: 'torp-rom.png', KLI: 'torp-kli.png', ORI: 'torp-ori.png' }
        self.types = { TFREE: 'netrek.png',
                       TEXPLODE: 'torp-explode.png',
                       TDET: 'torp-det.png',
                       TOFF: 'torp-off.png',
                       TSTRAIGHT: 'torp-straight.png' }
        self.pick()

    def update(self):
        if self.torp.status != self.old_status:
            self.old_status = self.torp.status
            self.pick()
        self.rect.center = tactical_scale(self.torp.x, self.torp.y)
        if self.torp.status == TEXPLODE:
            if nt.time > self.torp.explode:
                self.hide()
    
    def pick(self):
        if self.torp.status == TMOVE:
            if self.torp.ship == me:
                # IMAGERY: torp-me.png
                self.image = ic.get('torp-me.png')
            else:
                # IMAGERY: torp-???.png
                self.image = ic.get(self.teams[self.torp.ship.team])
        else:
            # IMAGERY: torp-explode.png
            image = self.types[self.torp.status]
            self.image = ic.get(image)
        
        # FIXME: animate torps
        # FIXME: server does not inform us when exploded torps are
        # finished exploding, so we have to run a counter of some
        # sort.
        self.rect = self.image.get_rect()
        
    def show(self):
        t_weapons.add(self)

    def hide(self):
        t_weapons.remove(self)

""" netrek protocol documentation, from server include/packets.h

	general protocol state outline

	starting state

	CP_SOCKET
	CP_FEATURE, optional, to indicate feature packets are known
	SP_MOTD
	SP_FEATURE, only if CP_FEATURE was seen
	SP_QUEUE, optional, repeats until slot is available
	SP_YOU, indicates slot number assigned

	login state, player slot status is POUTFIT
	client shows name and password prompt and accepts input

	CP_LOGIN
	CP_FEATURE
	SP_LOGIN
	SP_YOU
	SP_PLAYER_INFO
	various other server packets

	outfit state, player slot status is POUTFIT
	client shows team selection window

	SP_MASK, sent regularly during outfit

	client accepts team selection input
	CP_OUTFIT
	SP_PICKOK, signals server acceptance of alive state

	alive state,
	server places ship in game and play begins

	SP_PSTATUS, indicates PDEAD state
	client animates explosion

	SP_PSTATUS, indicates POUTFIT state
	clients returns to team selection window

	CP_QUIT
	CP_BYE
"""

""" client originated packets
"""

class CP:
    def tabulate(self, number, format):
        global cp_table
        cp_table[number] = (struct.calcsize(format), format)

cp_table = {}

class CP_SOCKET(CP):
    def __init__(self):
        self.code = 27
        self.format = '!bbbxI'
        self.tabulate(self.code, self.format)

    def data(self):
        if opt.dump: print "CP_SOCKET"
        return struct.pack(self.format, self.code, 4, 10, 0)

cp_socket = CP_SOCKET()

class CP_BYE(CP):
    def __init__(self):
        self.code = 29
        self.format = '!bxxx'
        self.tabulate(self.code, self.format)

    def data(self):
        print "CP_BYE"
        return struct.pack(self.format, self.code)

cp_bye = CP_BYE()

class CP_LOGIN(CP):
    def __init__(self):
        self.code = 8
        self.format = '!bbxx16s16s16s' 
        self.tabulate(self.code, self.format)

    def data(self, query, name, password, login):
        print "CP_LOGIN query=",query,"name=",name
        return struct.pack(self.format, self.code, query, name, password, login)

cp_login = CP_LOGIN()

class CP_OUTFIT(CP):
    def __init__(self):
        self.code = 9
        self.format = '!bbbx'
        self.tabulate(self.code, self.format)

    def data(self, race, ship=ASSAULT):
        print "CP_OUTFIT team=",race_decode(race),"ship=",ship
        return struct.pack(self.format, self.code, race, ship)

cp_outfit = CP_OUTFIT()

class CP_SPEED(CP):
    def __init__(self):
        self.code = 2
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, speed):
        print "CP_SPEED speed=",speed
        return struct.pack(self.format, self.code, speed)

cp_speed = CP_SPEED()

class CP_DIRECTION(CP):
    def __init__(self):
        self.code = 3
        self.format = '!bBxx'
        self.tabulate(self.code, self.format)

    def data(self, direction):
        print "CP_DIRECTION direction=",direction
        return struct.pack(self.format, self.code, direction)

cp_direction = CP_DIRECTION()

class CP_PLANLOCK(CP):
    def __init__(self):
        self.code = 15
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, pnum):
        print "CP_PLANLOCK pnum=",pnum
        return struct.pack(self.format, self.code, pnum)

cp_planlock = CP_PLANLOCK()

class CP_PLAYLOCK(CP):
    def __init__(self):
        self.code = 16
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, pnum):
        print "CP_PLAYLOCK pnum=",pnum
        return struct.pack(self.format, self.code, pnum)

cp_playlock = CP_PLAYLOCK()

class CP_UPDATES(CP):
    def __init__(self):
        self.code = 31
        self.format = '!bxxxI'
        self.tabulate(self.code, self.format)

    def data(self, usecs):
        print "CP_UPDATES usecs=",usecs
        return struct.pack(self.format, self.code, usecs)

cp_updates = CP_UPDATES()

class CP_BOMB(CP):
    def __init__(self):
        self.code = 17
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, state=1):
        print "CP_BOMB state=",state
        return struct.pack(self.format, self.code, state)

cp_bomb = CP_BOMB()

class CP_BEAM(CP):
    def __init__(self):
        self.code = 18
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, state=1):
        print "CP_BEAM state=",state
        return struct.pack(self.format, self.code, state)

cp_beam = CP_BEAM()

class CP_CLOAK(CP):
    def __init__(self):
        self.code = 19
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, state=1):
        print "CP_CLOAK state=",state
        return struct.pack(self.format, self.code, state)

cp_cloak = CP_CLOAK()

class CP_REPAIR(CP):
    def __init__(self):
        self.code = 13
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, state=1):
        print "CP_REPAIR state=",state
        return struct.pack(self.format, self.code, state)

cp_repair = CP_REPAIR()

class CP_SHIELD(CP):
    def __init__(self):
        self.code = 12
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, state=1):
        print "CP_SHIELD state=",state
        return struct.pack(self.format, self.code, state)

cp_shield = CP_SHIELD()

class CP_MESSAGE(CP):
    def __init__(self):
        self.code = 1
        self.format = "!bBBx80s"
        self.tabulate(self.code, self.format)

    def data(self, group, indiv, mesg):
        print "CP_MESSAGE group=",group,"indiv=",indiv,"mesg=",mesg
        return struct.pack(self.format, self.code, group, indiv, mesg)

cp_message = CP_MESSAGE()

class CP_PHASER(CP):
    def __init__(self):
        self.code = 4
        self.format = '!bBxx'
        self.tabulate(self.code, self.format)

    def data(self, direction):
        print "CP_PHASER direction=",direction
        return struct.pack(self.format, self.code, direction)

cp_phaser = CP_PHASER()

class CP_PLASMA(CP):
    def __init__(self):
        self.code = 5
        self.format = '!bBxx'
        self.tabulate(self.code, self.format)

    def data(self, direction):
        print "CP_PLASMA direction=",direction
        return struct.pack(self.format, self.code, direction)

cp_plasma = CP_PLASMA()

class CP_TORP(CP):
    def __init__(self):
        self.code = 6
        self.format = '!bBxx'
        self.tabulate(self.code, self.format)

    def data(self, direction):
        print "CP_TORP direction=",direction
        return struct.pack(self.format, self.code, direction)

cp_torp = CP_TORP()

class CP_QUIT(CP):
    def __init__(self):
        self.code = 7
        self.format = '!bxxx'
        self.tabulate(self.code, self.format)

    def data(self):
        print "CP_QUIT"
        return struct.pack(self.format, self.code)

cp_quit = CP_QUIT()

class CP_WAR(CP):
    def __init__(self):
        self.code = 10
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, newmask):
        print "CP_WAR newmask=",newmask
        return struct.pack(self.format, self.code, newmask)

cp_war = CP_WAR()

class CP_PRACTR(CP):
    def __init__(self):
        self.code = 11
        self.format = '!bxxx'
        self.tabulate(self.code, self.format)

    def data(self):
        print "CP_PRACTR"
        return struct.pack(self.format, self.code)

cp_practr = CP_PRACTR()

class CP_ORBIT(CP):
    def __init__(self):
        self.code = 14
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, state=1):
        print "CP_ORBIT =",state
        return struct.pack(self.format, self.code, state)

cp_orbit = CP_ORBIT()

class CP_DET_TORPS(CP):
    def __init__(self):
        self.code = 20
        self.format = '!bxxx'
        self.tabulate(self.code, self.format)

    def data(self):
        print "CP_DET_TORPS"
        return struct.pack(self.format, self.code)

cp_det_torps = CP_DET_TORPS()

class CP_DET_MYTORP(CP):
    def __init__(self):
        self.code = 21
        self.format = '!bxh'
        self.tabulate(self.code, self.format)

    def data(self, tnum):
        print "CP_DET_MYTORP"
        return struct.pack(self.format, self.code, tnum)

cp_det_mytorp = CP_DET_MYTORP()

class CP_COPILOT(CP):
    def __init__(self):
        self.code = 22
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, state=1):
        print "CP_COPILOT"
        return struct.pack(self.format, self.code, state)

cp_copilot = CP_COPILOT()

class CP_REFIT(CP):
    def __init__(self):
        self.code = 23
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, ship):
        print "CP_REFIT ship=",ship
        return struct.pack(self.format, self.code, ship)

cp_refit = CP_REFIT()

class CP_TRACTOR(CP):
    def __init__(self):
        self.code = 24
        self.format = '!bbbx'
        self.tabulate(self.code, self.format)

    def data(self, state, pnum):
        print "CP_TRACTOR state=",state,"pnum=",pnum
        return struct.pack(self.format, self.code, state, pnum)

cp_tractor = CP_TRACTOR()

class CP_REPRESS(CP):
    def __init__(self):
        self.code = 25
        self.format = '!bbbx'
        self.tabulate(self.code, self.format)

    def data(self, state, pnum):
        print "CP_REPRESS state=",state,"pnum=",pnum
        return struct.pack(self.format, self.code, state, pnum)

cp_repress = CP_REPRESS()

class CP_COUP(CP):
    def __init__(self):
        self.code = 26
        self.format = '!bxxx'
        self.tabulate(self.code, self.format)

    def data(self):
        print "CP_COUP"
        return struct.pack(self.format, self.code)

cp_coup = CP_COUP()

class CP_OPTIONS(CP):
    def __init__(self):
        self.code = 28
        self.format = "!bxxxI96s"
        self.tabulate(self.code, self.format)

    def data(self, flags, keymap):
        print "CP_OPTIONS flags=",flags,"keymap=",keymap
        return struct.pack(self.format, self.code, flags, keymap)

cp_options = CP_OPTIONS()

class CP_DOCKPERM(CP):
    def __init__(self):
        self.code = 30
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, state):
        print "CP_DOCKPERM state=",state
        return struct.pack(self.format, self.code, state)

cp_dockperm = CP_DOCKPERM()

class CP_RESETSTATS(CP):
    def __init__(self):
        self.code = 32
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, verify):
        print "CP_RESETSTATS verify=",verify
        return struct.pack(self.format, self.code, verify)

cp_resetstats = CP_RESETSTATS()

class CP_RESERVED(CP):
    def __init__(self):
        self.code = 33
        self.format = "!bxxx16s16s" 
        self.tabulate(self.code, self.format)

    def data(self, data, resp):
        print "CP_RESERVED"
        return struct.pack(self.format, self.code, data, resp)

cp_reserved = CP_RESERVED()

class CP_SCAN(CP):
    def __init__(self):
        self.code = 34
        self.format = '!bbxx'
        self.tabulate(self.code, self.format)

    def data(self, pnum):
        print "CP_SCAN pnum=",pnum
        return struct.pack(self.format, self.code, pnum)

cp_scan = CP_SCAN()

""" server originated packets
"""

class SP:
    def tabulate(self, number, format, instance):
        global sp_table
        sp_table[number] = (struct.calcsize(format), instance)

    def find(self, number):
        """ given a packet type return a tuple consisting of
            (size, instance)
        """
        global sp_table
        if not sp_table.has_key(number):
            return (1, self)
        return sp_table[number]

sp_table = {}
sp = SP()

class SP_MOTD(SP):
    def __init__(self):
        self.code = 11
        self.format = '!bxxx80s'
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, message) = struct.unpack(self.format, data)
        print strnul(message)
        # FIXME: present MOTD on pygame screen

sp_motd = SP_MOTD()

class SP_YOU(SP):
    def __init__(self):
        self.code = 12
        self.format = '!bbbbbbxxIlllhhhh'
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        global opt
        (ignored, pnum, hostile, swar, armies, tractor, flags, damage,
         shield, fuel, etemp, wtemp, whydead, whodead) = struct.unpack(self.format, data)
        if opt.dump: print "SP_YOU pnum=",pnum,"hostile=",team_decode(hostile),"swar=",team_decode(swar),"armies=",armies,"tractor=",tractor,"flags=",flags,"damage=",damage,"shield=",shield,"fuel=",fuel,"etemp=",etemp,"wtemp=",wtemp,"whydead=",whydead,"whodead=",whodead
        ship = galaxy.ship(pnum)
        ship.sp_you(hostile, swar, armies, tractor, flags, damage, shield, fuel, etemp, wtemp, whydead, whodead)
        if opt.name:
            nt.send(cp_updates.data(1000000/opt.updates))
            nt.send(cp_login.data(0, opt.name, opt.password, opt.login))
            opt.name = None

sp_you = SP_YOU()

class SP_QUEUE(SP):
    def __init__(self):
        self.code = 13
        self.format = '!bxh'
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pos) = struct.unpack(self.format, data)
        if opt.dump: print "SP_QUEUE pos=",pos
        # FIXME: present on pygame screen

sp_queue = SP_QUEUE()

class SP_PL_LOGIN(SP):
    def __init__(self):
        self.code = 24
        self.format = "!bbbx16s16s16s" 
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, rank, name, monitor,
         login) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PL_LOGIN pnum=",pnum,"rank=",rank,"name=",strnul(name),"monitor=",strnul(monitor),"login=",strnul(login)
        ship = galaxy.ship(pnum)
        ship.sp_pl_login(rank, name, monitor, login)

sp_pl_login = SP_PL_LOGIN()

class SP_HOSTILE(SP):
    def __init__(self):
        self.code = 22
        self.format = "!bbbb"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, war, hostile) = struct.unpack(self.format, data)
        if opt.dump: print "SP_HOSTILE pnum=",pnum,"war=",team_decode(war),"hostile=",team_decode(hostile)
        ship = galaxy.ship(pnum)
        ship.sp_hostile(war, hostile)

sp_hostile = SP_HOSTILE()

class SP_PLAYER_INFO(SP):
    def __init__(self):
        self.code = 2
        self.format = "!bbbb"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, shiptype, team) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PLAYER_INFO pnum=",pnum,"shiptype=",shiptype,"team=",team_decode(team)
        ship = galaxy.ship(pnum)
        ship.sp_player_info(shiptype, team)

sp_player_info = SP_PLAYER_INFO()

class SP_KILLS(SP):
    def __init__(self):
        self.code = 3
        self.format = "!bbxxI"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, kills) = struct.unpack(self.format, data)
        if opt.dump: print "SP_KILLS pnum=",pnum,"kills=",kills
        ship = galaxy.ship(pnum)
        ship.sp_kills(kills)

sp_kills = SP_KILLS()

class SP_PSTATUS(SP):
    def __init__(self):
        self.code = 20
        self.format = "!bbbx"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, status) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PSTATUS pnum=",pnum,"status=",status
        ship = galaxy.ship(pnum)
        ship.sp_pstatus(status)

sp_pstatus = SP_PSTATUS()

class SP_PLAYER(SP):
    def __init__(self):
        self.code = 4
        self.format = "!bbBbll"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, dir, speed, x, y) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PLAYER pnum=",pnum,"dir=",dir,"speed=",speed,"x=",x,"y=",y
        ship = galaxy.ship(pnum)
        ship.sp_player(dir, speed, x, y)

sp_player = SP_PLAYER()

class SP_FLAGS(SP):
    def __init__(self):
        self.code = 18
        self.format = "!bbbxI"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, tractor, flags) = struct.unpack(self.format, data)
        if opt.dump: print "SP_FLAGS pnum=",pnum,"tractor=",tractor,"flags=",flags
        ship = galaxy.ship(pnum)
        ship.sp_flags(tractor, flags)

sp_flags = SP_FLAGS()

class SP_PLANET_LOC(SP):
    def __init__(self):
        self.code = 26
        self.format = "!bbxxll16s" 
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, x, y, name) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PLANET_LOC pnum=",pnum,"x=",x,"y=",y,"name=",strnul(name)
        planet = galaxy.planet(pnum)
        planet.sp_planet_loc(x, y, name)

sp_planet_loc = SP_PLANET_LOC()

class SP_LOGIN(SP):
    def __init__(self):
        self.code = 17
        self.format = "!bbxxl96s"
        self.tabulate(self.code, self.format, self)
        self.uncatch()

    def uncatch(self):
        self.callback = None

    def catch(self, callback):
        self.callback = callback

    def handler(self, data):
        (ignored, accept, flags, keymap) = struct.unpack(self.format, data)
        if opt.dump: print "SP_LOGIN accept=",accept,"flags=",flags
        if self.callback:
            self.callback(accept, flags, keymap)
            self.uncatch()

sp_login = SP_LOGIN()

class SP_MASK(SP):
    def __init__(self):
        self.code = 19
        self.format = "!bbxx"
        self.tabulate(self.code, self.format, self)
        self.uncatch()

    def uncatch(self):
        self.callback = None

    def catch(self, callback):
        self.callback = callback

    def handler(self, data):
        (ignored, mask) = struct.unpack(self.format, data)
        if opt.dump: print "SP_MASK mask=",team_decode(mask)
        global pending_outfit
        if pending_outfit:
            nt.send(cp_outfit.data(0))
            pending_outfit = False
        if self.callback:
            self.callback(mask)
        # FIXME: note protocol phase change
        # FIXME: update team selection icons

sp_mask = SP_MASK()

class SP_PICKOK(SP):
    def __init__(self):
        self.code = 16
        self.format = "!bbxx"
        self.tabulate(self.code, self.format, self)
        self.uncatch()

    def uncatch(self):
        self.callback = None

    def catch(self, callback):
        self.callback = callback

    def handler(self, data):
        (ignored, state) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PICKOK state=",state
        if self.callback:
            self.callback(state)
            self.uncatch()
        # FIXME: handle bad state reply
        # FIXME: note protocol phase change

sp_pickok = SP_PICKOK()

class SP_RESERVED(SP):
    def __init__(self):
        self.code = 25
        self.format = "!bxxx16s"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, data) = struct.unpack(self.format, data)
        data = struct.unpack('16b', data)
        if opt.dump: print "SP_RESERVED data=",data
        # FIXME: handle the request by returning a CP_RESERVED

sp_reserved = SP_RESERVED()

class SP_TORP_INFO(SP):
    def __init__(self):
        self.code = 5
        self.format = "!bbbxhxx"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, war, status, tnum) = struct.unpack(self.format, data)
        if opt.dump: print "SP_TORP_INFO war=",team_decode(war),"status=",status,"tnum=",tnum
        torp = galaxy.torp(tnum)
        torp.sp_torp_info(war, status)

sp_torp_info = SP_TORP_INFO()

class SP_TORP(SP):
    def __init__(self):
        self.code = 6
        self.format = "!bBhll"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, dir, tnum, x, y) = struct.unpack(self.format, data)
        if opt.dump: print "SP_TORP dir=",dir,"tnum=",tnum,"x=",x,"y=",y
        torp = galaxy.torp(tnum)
        torp.sp_torp(dir, x, y)

sp_torp = SP_TORP()

class SP_PLASMA_INFO(SP):
    def __init__(self):
        self.code = 8
        self.format = "!bbbxhxx"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, war, status, pnum) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PLASMA_INFO war=",team_decode(war),"status=",status,"pnum=",pnum

sp_plasma_info = SP_PLASMA_INFO()

class SP_PLASMA(SP):
    def __init__(self):
        self.code = 9
        self.format = "!bxhll"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, x, y) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PLASMA pnum=",pnum,"x=",x,"y=",y

sp_plasma = SP_PLASMA()

class SP_STATUS(SP):
    def __init__(self):
        self.code = 14
        self.format = "!bbxxIIIIIL"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, tourn, armsbomb, planets, kills, losses, time, timeprod) = struct.unpack(self.format, data)
        if opt.dump: print "SP_STATUS tourn=",tourn,"armsbomb=",armsbomb,"planets=",planets,"kills=",kills,"losses=",losses,"time=",time,"timepro=",timeprod
        # FIXME: display t-mode state

sp_status = SP_STATUS()

class SP_PHASER(SP):
    def __init__(self):
        self.code = 7
        self.format = "!bbbBlll" 
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, status, dir, x, y, target) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PHASER pnum=",pnum,"status=",status,"dir=",dir,"x=",x,"y=",y,"target=",target
        phaser = galaxy.phaser(pnum)
        phaser.sp_phaser(status, dir, x, y, target)

sp_phaser = SP_PHASER()

class SP_PLANET(SP):
    def __init__(self):
        self.code = 15
        self.format = "!bbbbhxxl" 
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, owner, info, flags, armies) = struct.unpack(self.format, data)
        if opt.dump: print "SP_PLANET pnum=",pnum,"owner=",owner,"info=",info,"flags=",flags,"armies=",armies
        planet = galaxy.planet(pnum)
        planet.sp_planet(owner, info, flags, armies)

sp_planet = SP_PLANET()

class SP_MESSAGE(SP):
    def __init__(self):
        self.code = 1
        self.format = "!bBBB80s"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, m_flags, m_recpt, m_from, mesg) = struct.unpack(self.format, data)
        if opt.dump: print "SP_MESSAGE m_flags=",m_flags,"m_recpt=",m_recpt,"m_from=",m_from,"mesg=",strnul(mesg)
        print strnul(mesg)
        # FIXME: display the message

sp_message = SP_MESSAGE()

class SP_STATS(SP):
    def __init__(self):
        self.code = 23
        self.format = "!bbxx13l"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, pnum, tkills, tlosses, kills, losses, tticks, tplanets, tarmies, sbkills, sblosses, armies, planets, maxkills, sbmaxkills) = struct.unpack(self.format, data)
        if opt.dump: print "SP_STATS pnum=",pnum,"tkills=",tkills,"tlosses=",tlosses,"kills=",kills,"losses=",losses,"tticks=",tticks,"tplanets=",tplanets,"tarmies=",tarmies,"sbkills=",sbkills,"sblosses=",sblosses,"armies=",armies,"planets=",planets,"maxkills=",maxkills,"sbmaxkills=",sbmaxkills

sp_stats = SP_STATS()

class SP_WARNING(SP):
    def __init__(self):
        self.code = 10
        self.format = '!bxxx80s'
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, message) = struct.unpack(self.format, data)
        if opt.dump: print "SP_WARNING message=",message
        print strnul(message)
        # FIXME: display the warning

sp_warning = SP_WARNING()

class SP_FEATURE(SP):
    def __init__(self):
        self.code = 60
        self.format = "!bbbbi80s"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, type, arg1, arg2, value, name) = struct.unpack(self.format, data)
        if opt.dump: print "SP_FEATURE type=",type,"arg1=",arg1,"arg2=",arg2,"value=",value,"name=",name
        # FIXME: process the packet

sp_feature = SP_FEATURE()

class SP_BADVERSION(SP):
    def __init__(self):
        self.code = 21
        self.format = "!bbxx"
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, why) = struct.unpack(self.format, data)
        print "SP_BADVERSION why=",why
        # FIXME: process the packet

sp_badversion = SP_BADVERSION()

class SP_PING(SP):
    def __init__(self):
        self.code = 46
        self.format = "!bBHBBBB" 
        self.tabulate(self.code, self.format, self)

    def handler(self, data):
        (ignored, number, lag, tloss_sc, tloss_cs, iloss_sc, iloss_cs) = struct.unpack(self.format, data)

sp_ping = SP_PING()

## end of server packets

## from Xlib.display import Display
## from Xlib import X
## class XlibEventSource:
##     """ incomplete code for obtaining an Xlib event source that can be
##     used to wake the client when keyboard or mouse events occur,
##     usable by select.
##     """
##     def handle_event(event):
##         keycode = event.detail
##         if event.type == X.KeyPress:
##             print event.detail

##     def main():
##         disp = Display()
##         root = disp.screen().root
        
##         root.change_attributes(event_mask = X.KeyPressMask)
##         root.grab_key(49, X.AnyModifier, 1, X.GrabModeAsync, X.GrabModeAsync)
        
##         while 1:
##             event = root.display.next_event()
##             handle_event(event)
##             return

class MetaClient:
    """ Netrek UDP MetaClient
        for connection to metaservers to obtain list of games in play
        References: server/ntserv/solicit.c server/tools/players.c
        metaserver/*.c client/parsemeta.c
    """
    def __init__(self, callback=None):
        self.socket = None
        self.callback = callback
        self.servers = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        metaservers = ("127.0.0.1", "224.0.0.1", "metaserver.netrek.org")
        for x in metaservers:
            try:
                self.socket.sendto('?', (x, 3521))
            except:
                print x, "bad"
                pass
        # FIXME: iterate through the IPs against metaserver.netrek.org
    
    def recv(self):
        while 1:
            is_readable = [self.socket]
            is_writable = []
            is_error = []
            r, w, e = select.select(is_readable, is_writable, is_error, 0.1)
            if not r: return
            try:
                (text, address) = self.socket.recvfrom(2048)
                break
            except:
                return
        if text[0] == 's': self.version_s(text, address)
        elif text[0] == 'r': self.version_r(text)

    def version_s(self, text, address):
        unpack = text.split(',')
        server = {}
        server['name'] = address[0]
        server['type'] = unpack[1]
        server['comment'] = unpack[2]
        server['port'] = int(unpack[4])
        server['players'] = int(unpack[5])
        server['queue'] = int(unpack[6].strip())
        server['status'] = 2
        if server['type'] == 'unknown': server['status'] = 3
        server['age'] = 0
        self.servers[server['name']] = server
        if self.callback: self.callback(server['name'])

    def version_r(self, text):
        lines = text.split('\n')
        (version, n) = lines[0].split(',')
        for x in range(int(n)):
            server = {}
            (server['name'], port, server['status'], age, players, queue, server['type']) = lines[x+1].split(',')
            server['port'] = int(port)
            server['age'] = int(age)
            server['players'] = int(players)
            server['queue'] = int(queue)
            self.servers[server['name']] = server
            if self.callback: self.callback(server['name'])

class Client:
    """ Netrek TCP Client
        for connection to a server to play or observe the game.
    """
    def __init__(self):
        self.socket = None
        self.time = time.time()
        
    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        
    def send(self, data):
        self.socket.send(data)

    def recv(self):
        # FIXME: a network update may cost more local time in
        # processing than the time between updates from the server,
        # which results in a pause to display updates since this
        # function does not return until the network queue is empty
        # ... this could be detected and CP_UPDATES negotiation made
        # to reduce the update rate.
        while 1:
            is_readable = [self.socket]
            is_writable = []
            is_error = []
            r, w, e = select.select(is_readable, is_writable, is_error, 0.04)
            if not r: return
            try:
                byte = self.socket.recv(1)
            except:
                print "recv failure"
                sys.exit()
            if len(byte) == 1:
                self.recv_packet(byte)
            else:
                # FIXME: when server closes connection, offer to reconnect
                # FIXME: ghostbust occurs if player is inactive, must ping
                print "server disconnection"
                sys.exit()

    def recv_packet(self, byte):
        number = struct.unpack('b', byte[0])[0]
        (size, instance) = sp.find(number)
        if size == 1:
            print "\n#### FIXME: UnknownPacketType ", number, "####\n"
            raise "UnknownPacketType, a packet was received from the server that is not known to this program, and since packet lengths are determined by packet types there is no reasonably way to continue operation"
            return
        rest = self.socket.recv(size-1, socket.MSG_WAITALL)
        if len(rest) != (size-1):
            print "### asked for %d and got %d bytes" % ((size-1), len(rest))
        self.time = time.time()
        # handle the prefix byte and the rest of the packet as a whole
        instance.handler(byte + rest)
        # FIXME: packet almalgamation may occur, s.recv second time may
        # return something less than the expected number of bytes, so we
        # have to wait for them.

""" user interface display phases
"""

class Phase:
    def __init__(self):
        self.warning_on = False

    def warning(self, message):
        font = fc.get(None, 36)
        text = font.render(message, 1, (255, 127, 127))
        self.warning_br = text.get_rect(center=(screen.get_width()/2,
                                                screen.get_height()-100))
        self.warning_bg = screen.subsurface(self.warning_br).copy()
        r1 = screen.blit(text, self.warning_br)
        pygame.display.update(r1)
        self.warning_on = True

    def unwarning(self):
        if self.warning_on:
            r1 = screen.blit(self.warning_bg, self.warning_br)
            pygame.display.update(r1)
            self.warning_on = False
        
    def background(self):
        # tile a background image onto the screen
        screen.fill((0,0,0))
        # IMAGERY: stars.png
        background = ic.get("stars.png")
        bh = background.get_height()
        bw = background.get_width()
        for y in range(screen.get_height() / bh + 1):
            for x in range(screen.get_width() / bw + 1):
                screen.blit(background, (x*bw, y*bh))

    def text(self, text, x, y, size=72, colour=(255, 255, 255)):
        font = fc.get(None, size)
        ts = font.render(text, 1, colour)
        tr = ts.get_rect(center=(x, y))
        screen.blit(ts, tr)
        
    def network_sink(self):
        # FIXME: select for *either* pygame events or network events.
        # Currently the code is suboptimal because it waits on network
        # events with a timeout of a twentieth of a second, after which it
        # checks for pygame events.  Therefore pygame events are delayed
        # by up to a twentieth of a second.
        nt.recv()
        
    def display_sink_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.mb(event)
        elif event.type == pygame.KEYDOWN:
            self.kb(event)
        elif event.type == pygame.QUIT:
            nt.send(cp_bye.data())
            sys.exit()
        elif event.type == pygame.MOUSEMOTION:
            self.mm(event)
        
    def display_sink(self):
        for event in pygame.event.get():
            self.display_sink_event(event)

    def display_sink_wait(self):
        event = pygame.event.wait()
        self.display_sink_event(event)

    def mm(self, event):
        # FIXME: watch for MOUSEMOTION and update object information panes
        # for planets or ships (on tactical or galactic)
        pass
    
    def kb(self, event):
        if event.key == pygame.K_q:
            screen.fill((0, 0, 0))
            pygame.display.flip()
            sys.exit()

    def cycle(self):
        while self.run:
            self.network_sink()
            self.display_sink()
    
class PhaseSplash(Phase):
    def __init__(self, screen):
        Phase.__init__(self)
        self.background()
        self.text("netrek", screen.get_width()/2, screen.get_height()/2, 144)
        pygame.display.flip()
        pygame.time.wait(250)
        # FIXME: add neat animation

class PhaseServers(Phase):
    def __init__(self, screen):
        Phase.__init__(self)
        self.background()
        self.text('netrek', 500, 100, 144)
        self.text('server list', 500, 175, 72)
        pygame.display.flip()

        self.fn = fc.get(None, 36)
        self.dy = 40 # vertical spacing
        self.n = 0 # number of servers shown so far
        self.mc = MetaClient(self.add)
        self.run = True
        self.cycle()
        
    def add(self, name):
        """ called by MetaClient for each server listed
        """
        server = self.mc.servers[name]
        y = 300 + self.dy * self.n
        r = []
        # per server icon
        # FIXME: icon per server type?
        # FIXME: icon better than this one
        # IMAGERY: netrek.png
        cs = ic.get("netrek.png")
        cr = cs.get_rect(left=50, centery=y)
        r.append(screen.blit(cs, cr))
        # server name
        ss = self.fn.render(name, 1, (255, 255, 255))
        sr = ss.get_rect(left=100, centery=y)
        r.append(screen.blit(ss, sr))
        # per player icon
        # FIXME: icon better than this one
        # FIXME: icon should not convey team
        for x in range(server['players']):
            # IMAGERY: netrek.png
            ps = ic.get("netrek.png") # per player icon
            pr = ps.get_rect(left=500+(x*36), centery=y)
            r.append(screen.blit(ps, pr))
                     
        self.mc.servers[name]['y'] = y
        self.n = self.n + 1
        pygame.display.update(r)
    
    def network_sink(self):
        self.mc.recv()

    def mb(self, event):
        if event.button != 1: return
        y = event.pos[1]
        distance = screen.get_height()
        chosen = None
        for k, v in self.mc.servers.iteritems():
            dy = abs(v['y'] - y)
            if dy < distance:
                distance = dy
                chosen = v['name']
        self.chosen = chosen
        self.run = False
        
class Field:
    def __init__(self, prompt, value, x, y):
        self.value = value
        self.fn = fn = fc.get(None, 36)
        self.sw = sw = screen.get_width()
        self.sh = sh = screen.get_height()
        # place prompt on screen
        self.ps = ps = fn.render(prompt, 1, (127, 127, 127))
        self.pc = pc = (x, y)
        self.pr = pr = ps.get_rect(topright=pc)
        r1 = screen.blit(ps, pr)
        # highlight entry area
        self.br = pygame.Rect(pr.right, pr.top, sw - pr.right - 300, pr.height)
        self.bg = screen.subsurface(self.br).copy()
        pygame.display.update(r1)
        self.enter()
        
    def highlight(self):
        return screen.fill((0,127,0), self.br)

    def unhighlight(self):
        return screen.blit(self.bg, self.br)

    def draw(self):
        as = self.fn.render(self.value, 1, (255, 255, 255))
        ar = as.get_rect(topleft=self.pc)
        ar.left = self.pr.right
        return screen.blit(as, ar)
        
    def redraw(self):
        r1 = self.highlight()
        r2 = self.draw()
        pygame.display.update([r1, r2])

    def leave(self):
        r1 = self.unhighlight()
        r2 = self.draw()
        pygame.display.update([r1, r2])
        
    def enter(self):
        r1 = self.highlight()
        r2 = self.draw()
        pygame.display.update([r1, r2])
        
    def append(self, char):
        self.value = self.value + char
        r1 = self.draw()
        pygame.display.update(r1)
        
    def backspace(self):
        self.value = self.value[:-1]
        self.redraw()

    def delete(self):
        self.value = ""
        self.redraw()

class PhaseLogin(Phase):
    def __init__(self, screen):
        Phase.__init__(self)
        self.background()
        self.text('netrek', 500, 100, 144)
        self.text(opt.server, 500, 185, 72)
        pygame.display.flip()
        # FIXME: display MOTD below name in smaller text
        self.name = Field("Type a name ? ", "", 500, 750)
        self.focused = self.name
        self.password = None
        self.run = True
        self.warning('connected to server')
        self.cycle()

    def tab(self):
        """ move to next field """
        self.focused.leave()
        if self.focused == self.password:
            self.chuck_cp_login()
        elif self.focused == self.name:
            if self.password == None:
                self.password = Field("Password ? ", "", 500, 800)
                # FIXME: password prompt appears momentarily if guest selected
                # FIXME: force no echo for password
            else:
                self.password.enter()
            self.focused = self.password
            if self.name.value == 'guest' or self.name.value == 'Guest':
                self.password.leave()
                self.password.value = ''
                self.chuck_cp_login()
            else:
                self.chuck_cp_login_attempt()

    def chuck_cp_login_attempt(self):
        self.catch_sp_login_attempt()
        nt.send(cp_login.data(1, str(self.name.value), str(self.password.value), 'pynetrek'))

    def throw_sp_login_attempt(self, accept, flags, keymap):
        if accept == 1:
            self.warning('server has this name listed')
        else:
            self.warning('server ignorant of this name')
        
    def catch_sp_login_attempt(self):
        global sp_login
        sp_login.catch(self.throw_sp_login_attempt)
                
    def chuck_cp_login(self):
        self.catch_sp_login()
        nt.send(cp_updates.data(1000000/opt.updates))
        nt.send(cp_login.data(0, str(self.name.value), str(self.password.value), 'pynetrek'))

    def throw_sp_login(self, accept, flags, keymap):
        if accept == 1:
            self.run = False
        else:
            self.warning('name and password refused by server')
            self.password.value = ''
            self.password.unhighlight()
            self.focused = self.name
            self.focused.enter()
        
    def catch_sp_login(self):
        global sp_login
        sp_login.catch(self.throw_sp_login)
                
    def untab(self):
        if self.focused == self.password:
            self.focused.leave()
            self.focused = self.name
            self.focused.redraw()

    def kb(self, event):
        self.unwarning()
        shift = (event.mod == pygame.KMOD_SHIFT or
                 event.mod == pygame.KMOD_LSHIFT or
                 event.mod == pygame.KMOD_RSHIFT)
        control = (event.mod == pygame.KMOD_CTRL or
                   event.mod == pygame.KMOD_LCTRL or
                   event.mod == pygame.KMOD_RCTRL)
        if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT: pass
        elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL: pass
        elif event.key == pygame.K_d and control:
            nt.send(cp_bye.data())
            sys.exit()
        elif event.key == pygame.K_w and control:
            self.focused.delete()
        elif event.key == pygame.K_TAB and shift:
            self.untab()
        elif event.key == pygame.K_TAB or event.key == pygame.K_RETURN:
            self.tab()
        elif event.key == pygame.K_BACKSPACE:
            self.focused.backspace()
        elif event.key > 31 and event.key < 255 and not control:
            self.focused.append(event.unicode)
        
    def mb(self):
        pass
    
class PhaseOutfit(Phase):
    def __init__(self, screen):
        Phase.__init__(self)
        self.run = True
        self.box = None
        self.last_team = None
        self.last_ship = CRUISER
        
    def do(self):
        self.run = True
        self.background()
        pygame.display.flip()
        self.text('netrek', 500, 100, 144)
        self.text(opt.server, 500, 185, 72)
        self.text('ship and race', 500, 255, 72)
        pygame.display.flip()
        box_l = 212
        box_t = 300
        box_r = 788
        box_b = 875
        r = []
        self.boxes = []
        # FIXME: display number of players on each team
        # FIXME: make these sprites rather than paint on screen
        table = [[FED, -1, +1], [ROM, -1, -1], [KLI, +1, -1], [ORI, +1, +1]]
        for row in table:
            (team, dx, dy) = row
            # box centre
            # FIXME: show SP_MASK by hiding or covering a team axis
            x = (box_r - box_l) / 2 + box_l
            y = (box_b - box_t) / 2 + box_t
            for ship in [CRUISER, ASSAULT, SCOUT, BATTLESHIP, DESTROYER, STARBASE]:
                x = x + dx * 60
                y = y + dy * 60
                # IMAGERY: ???-??.png
                rs = ic.get(teams[team]+'-'+ships[ship]+'.png')
                rr = rs.get_rect(center=(x, y))
                r.append(screen.blit(rs, rr))
                description = teams_long[team] + ' ' + ships_long[ship] + ', ' + ships_use[ship]
                self.boxes.append([x, y, ship, team, description])
        # FIXME: add minature galactic, showing ownership, player
        # positions if any, with ships to choose in each race space or
        # just outside the corner.
        # FIXME: display "in bronco you should remain with your team"
        # FIXME: show logged in players
        # FIXME: show planet status
        # FIXME: show whydead
        self.warning("in netrek all races are equal")
        pygame.display.update(r)
        sp_mask.catch(self.mask)
        self.cycle()
        sp_mask.uncatch()

    def mask(self, mask):
        # FIXME: if mask changes, update available races
        pass

    def team(self, team, ship=CRUISER):
        self.last_team = team;
        self.last_ship = ship;
        sp_pickok.catch(self.sp_pickok)
        nt.send(cp_outfit.data(team, ship))

    def sp_pickok(self, state):
        if state == 1:
            self.run = False
        else:
            self.unwarning()
            self.warning('outfit request refused by server')

    def nearest(self, pos):
        (x, y) = pos
        nearest = None
        minimum = 70**2
        for box in self.boxes:
            (bx, by, ship, team, description) = box
            distance = (bx - x)**2 + (by - y)**2
            if distance < minimum:
                nearest = box
                minimum = distance
        return nearest
    
    def mb(self, event):
        self.unwarning()
        nearest = self.nearest(event.pos)
        if nearest != None:
            (bx, by, ship, team, description) = nearest
            self.team(teams_numeric[team], ship)
        else:
            self.warning('click on a ship, mate')
        # FIXME: click on team icon sends CP_OUTFIT most recent ship
        # FIXME: click on ship icon requests CP_OUTFIT with team and ship
        
    def mm(self, event):
        nearest = self.nearest(event.pos)
        if nearest != self.box:
            self.unwarning()
            if nearest != None:
                (bx, by, ship, team, description) = nearest
                self.warning(description)
            self.box = nearest
        
    def kb(self, event):
        self.unwarning()
        shift = (event.mod == pygame.KMOD_SHIFT or
                 event.mod == pygame.KMOD_LSHIFT or
                 event.mod == pygame.KMOD_RSHIFT)
        control = (event.mod == pygame.KMOD_CTRL or
                   event.mod == pygame.KMOD_LCTRL or
                   event.mod == pygame.KMOD_RCTRL)
        if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT: pass
        elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL: pass
        elif event.key == pygame.K_d and control:
            nt.send(cp_bye.data())
            sys.exit()
        elif event.key == pygame.K_q:
            nt.send(cp_bye.data())
            sys.exit()
        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            if self.last_team != None:
                self.team(self.last_team, self.last_ship)
        elif event.key == pygame.K_f: self.team(0, self.last_ship)
        elif event.key == pygame.K_r: self.team(1, self.last_ship)
        elif event.key == pygame.K_k: self.team(2, self.last_ship)
        elif event.key == pygame.K_o: self.team(3, self.last_ship)
        
class PhaseFlight(Phase):
    def __init__(self):
        Phase.__init__(self)
        self.run = True

    def cycle(self):
        while self.run:
            self.network_sink()
            self.display_sink()
            self.update()
            if me.status == POUTFIT: break

    def mb(self, event):
        """ mouse button down event handler
        position is a list of (x, y) screen coordinates
        button is a mouse button number
        """
        global me
        if event.button == 3 and me != None:
            (x, y) = event.pos
            nt.send(cp_direction.data(xy_to_dir(x, y)))
        elif event.button == 2 and me != None:
            (x, y) = event.pos
            nt.send(cp_phaser.data(xy_to_dir(x, y)))
        elif event.button == 1 and me != None:
            (x, y) = event.pos
            nt.send(cp_torp.data(xy_to_dir(x, y)))
    
    def kb(self, event):
        global me
        shift = (event.mod == pygame.KMOD_SHIFT or
                 event.mod == pygame.KMOD_LSHIFT or
                 event.mod == pygame.KMOD_RSHIFT)
        # FIXME: use a lookup table
        if event.key == pygame.K_LSHIFT: pass
        elif event.key == pygame.K_8 and shift: nt.send(cp_practr.data())
        elif event.key == pygame.K_0: nt.send(cp_speed.data(0))
        elif event.key == pygame.K_1: nt.send(cp_speed.data(1))
        elif event.key == pygame.K_2 and shift: nt.send(cp_speed.data(12))
        elif event.key == pygame.K_2: nt.send(cp_speed.data(2))
        elif event.key == pygame.K_3: nt.send(cp_speed.data(3))
        elif event.key == pygame.K_4: nt.send(cp_speed.data(4))
        elif event.key == pygame.K_5: nt.send(cp_speed.data(5))
        elif event.key == pygame.K_6: nt.send(cp_speed.data(6))
        elif event.key == pygame.K_7: nt.send(cp_speed.data(7))
        elif event.key == pygame.K_8: nt.send(cp_speed.data(8))
        elif event.key == pygame.K_9: nt.send(cp_speed.data(9))
        elif event.key == pygame.K_u or event.key == pygame.K_s:
            if me:
                if me.flags & PFSHIELD:
                    nt.send(cp_shield.data(0))
                else:
                    nt.send(cp_shield.data(1))
        elif event.key == pygame.K_r and shift: nt.send(cp_repair.data(1))
        elif event.key == pygame.K_b: nt.send(cp_bomb.data())
        elif event.key == pygame.K_z: nt.send(cp_beam.data(1))
        elif event.key == pygame.K_x: nt.send(cp_beam.data(2))
        elif event.key == pygame.K_d and shift:
            if me:
                base = me.n * MAXTORP
                for x in range(base, base + MAXTORP):
                    torp = galaxy.torp(x)
                    if torp.status == TMOVE or torp.status == TSTRAIGHT:
                        nt.send(cp_det_mytorp.data(x))
        elif event.key == pygame.K_d: nt.send(cp_det_torps.data())
        elif event.key == pygame.K_c:
            if me:
                if me.flags & PFCLOAK:
                    nt.send(cp_cloak.data(0))
                else:
                    nt.send(cp_cloak.data(1))
        elif event.key == pygame.K_SEMICOLON:
            x, y = pygame.mouse.get_pos()
            nearest = galaxy.nearest_planet(x, y)
            if nearest != None:
                nt.send(cp_planlock.data(nearest.n))
        elif event.key == pygame.K_l:
            x, y = pygame.mouse.get_pos()
            nearest = galaxy.nearest_ship(x, y)
            if nearest != None:
                nt.send(cp_playlock.data(nearest.n))
        elif event.key == pygame.K_t and shift:
            x, y = pygame.mouse.get_pos()
            nearest = galaxy.nearest_ship(x, y)
            if me and nearest != None:
                if me.flags & PFTRACT:
                    nt.send(cp_tractor.data(0, nearest.n))
                else:
                    nt.send(cp_tractor.data(1, nearest.n))
        elif event.key == pygame.K_y:
            x, y = pygame.mouse.get_pos()
            nearest = galaxy.nearest_ship(x, y)
            if me and nearest != None:
                if me.flags & PFPRESS:
                    nt.send(cp_repress.data(0, nearest.n))
                else:
                    nt.send(cp_repress.data(1, nearest.n))
        # FIXME: some of this looks repetitive
        elif event.key == pygame.K_o: nt.send(cp_orbit.data(1))
        else:
            return Phase.kb(self, event)
    
class PhaseFlightGalactic(PhaseFlight):
    def __init__(self):
        PhaseFlight.__init__(self)
        
    def do(self):
        self.run = True
        screen.blit(background, (0, 0))
        pygame.display.flip()
        self.cycle()
        
    def kb(self, event):
        global ph_flight
        if event.key == pygame.K_RETURN:
            ph_flight = ph_tactical
            self.run = False
        else:
            return PhaseFlight.kb(self, event)

    def update(self):
        galactic.clear(screen, background)
        galactic.update()
        pygame.display.update(galactic.draw(screen))


class PhaseFlightTactical(PhaseFlight):
    def __init__(self):
        PhaseFlight.__init__(self)

    def do(self):
        self.run = True
        screen.blit(background, (0, 0))
        pygame.display.flip()
        self.cycle()
        
    def kb(self, event):
        global ph_flight
        if event.key == pygame.K_RETURN:
            ph_flight = ph_galactic
            self.run = False
        else:
            return PhaseFlight.kb(self, event)

    # FIXME: subgalactic in a corner, alpha blended
    # FIXME: console in a corner
    # FIXME: action menu items around edge
    # FIXME: menu item "?" or mouse-over, to do modal information
    # query on a screen object.
        
    def update(self):
        o_phasers = galaxy.phasers_undraw()
        t_weapons.clear(screen, background)
        t_players.clear(screen, background)
        t_planets.clear(screen, background)
        t_planets.update()
        t_players.update()
        t_weapons.update()
        r_planets = t_planets.draw(screen)
        r_players = t_players.draw(screen)
        r_weapons = t_weapons.draw(screen)
        r_phasers = galaxy.phasers_draw()
        pygame.display.update(o_phasers+r_planets+r_players+r_weapons+r_phasers)

""" Main Program
"""

pygame.init()

size = width, height = 1000, 1000
screen = pygame.display.set_mode(size)

t_planets = pygame.sprite.OrderedUpdates(())
t_players = pygame.sprite.OrderedUpdates(())
t_weapons = pygame.sprite.OrderedUpdates(())

galactic = pygame.sprite.OrderedUpdates(())

background = screen.copy()
background.fill((0, 0, 0))
#background.fill((255, 255, 255))
screen.blit(background, (0, 0))
# FIXME: allow user to select graphics theme, default on XO is to be white with oysters, otherwise use stars, planets, and ships.
pygame.display.flip()

pending_outfit = False

ph_splash = PhaseSplash(screen)

print opt
if opt.server == None:
    ph_servers = PhaseServers(screen)
    # FIXME: discover servers from a cache
    opt.server = ph_servers.chosen

# PhaseConnect
# FIXME: do not block and hang during connect, do it asynchronously
# FIXME: handle connection failure gracefully
# FIXME: place connection attempt inside a PhaseConnect
nt = Client()
nt.connect(opt.server, opt.port)
nt.send(cp_socket.data())

# PhaseQueue
# FIXME: if an SP_QUEUE packet is received, present this phase
# FIXME: allow play on another server even while queued? [grin]

if opt.name == '':
    ph_login = PhaseLogin(screen)

ph_outfit = PhaseOutfit(screen)
ph_galactic = PhaseFlightGalactic()
ph_tactical = PhaseFlightTactical()

while 1:
    ph_outfit.do()
    while me.status == POUTFIT: nt.recv()
    ph_flight = ph_tactical
    while 1:
        screen.blit(background, (0, 0))
        pygame.display.flip()
        ph_flight.do()
        if me.status == POUTFIT: break
    # debugging
    if opt.dump:
        for n, ship in galaxy.ships.iteritems():
            if ship == me or ship.sp_flags_cumulative_flags != 0: print "ship %d sp_flags %s sp_you %s" % (ship.n, hex(ship.sp_flags_cumulative_flags), hex(ship.sp_you_cumulative_flags))

# FIXME: very little reason for outfit phase, default to automatically re-enter
# FIXME: planets to be partial alpha in tactical view as ships close in?

# socket http://docs.python.org/lib/socket-objects.html
# struct http://docs.python.org/lib/module-struct.html
# built-ins http://docs.python.org/lib/built-in-funcs.html
