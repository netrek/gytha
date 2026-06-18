"""
Pygame sprite classes for game objects: planets, ships, torps, and plasma.

Module-level state is wired by gytha/__init__.py:

  me         - current player Ship    (set by SP_YOU handler)
  opt        - parsed CLI options     (set at start of main)
  t_planets  - tactical planet group  (set by pg_init)
  t_players  - tactical ship group    (set by pg_init)
  t_torps    - tactical torp group    (set by pg_init)
  t_plasma   - tactical plasma group  (set by pg_init)
  g_planets  - galactic planet group  (set by pg_init)
  g_players  - galactic ship group    (set by pg_init)
"""

import pygame

from .constants import *
from .util import *
from .cache import ic, fc
from .coords import n2gs, n2ts
from .sprites import MultipleImageSprite

# Module-level state — set by __init__.py
me = None
opt = None
t_planets = None
t_players = None
t_torps = None
t_plasma = None
g_planets = None
g_players = None


class PlanetSprite(MultipleImageSprite):
    def __init__(self, planet):
        self.planet = planet
        self.old = None
        self.tag = None
        self.icon = None
        MultipleImageSprite.__init__(self)


class PlanetGalacticSprite(PlanetSprite):
    def __init__(self, planet):
        PlanetSprite.__init__(self, planet)
        self.pick()
        g_planets.add(self)

    def add_armies(self):
        if self.planet.armies == 0:
            return
        tag = pygame.Surface((30, 74), pygame.SRCALPHA, 32)
        message = "%d" % (self.planet.armies)
        colour = (128, 128, 128)
        if self.planet.flags & PLAGRI:
            colour = (255, 255, 255)
        font = fc.get(FONT_SANS, 12)
        text = font.render(message, 1, colour)
        rect = text.get_rect(top=0, centerx=15)
        tag.blit(text, rect)
        self.mi_add_image(tag)

    def add_flags(self):
        if not self.planet.flags & (PLFUEL | PLREPAIR):
            return
        pos = 70
        tag = pygame.Surface((pos, 30), pygame.SRCALPHA, 32)
        colour = team_colour(self.planet.owner)
        if self.planet.flags & PLFUEL:
            font = fc.get(FONT_SANS, 12)
            text = font.render('F', 1, colour)
            rect = text.get_rect(left=0, centery=15)
            tag.blit(text, rect)
        if self.planet.flags & PLREPAIR:
            font = fc.get(FONT_SANS, 12)
            text = font.render('R', 1, colour)
            rect = text.get_rect(right=pos, centery=15)
            tag.blit(text, rect)
        self.mi_add_image(tag)

    def add_icon(self):
        # IMAGERY: planet-???-30x30.png
        # TODO: add agri planet 30x30 png files
        self.icon = ic.get("planet-" + teams[self.planet.owner] + "-30x30.png")
        self.mi_add_image(self.icon)

    def add_name(self):
        if self.planet.name == '':
            return
        tag = pygame.Surface((92, 74), pygame.SRCALPHA, 32)
        font = fc.get(FONT_SANS, 12)
        message = "%s" % (self.planet.name)
        colour = team_colour(self.planet.owner)
        if self.planet.armies > 4:
            colour = brighten(colour)
        text = font.render(message, 1, colour)
        rect = text.get_rect(centerx=46, bottom=74)
        tag.blit(text, rect)
        self.mi_add_image(tag)

    def pick(self):
        self.mi_begin()
        self.add_icon()
        if self.planet.info & me.team:
            self.add_armies()
            self.add_flags()
        self.add_name()
        self.mi_commit()

    def update(self):
        new = self.planet.owner, self.planet.info, self.planet.name, self.planet.flags, self.planet.armies, self.planet.x, self.planet.y
        if new != self.old:
            self.old = new
            self.pick()
            self.rect.center = n2gs(self.planet.x, self.planet.y)


class PlanetTacticalSprite(PlanetSprite):
    def __init__(self, planet):
        PlanetSprite.__init__(self, planet)
        self.pick()
        self.pos = 0, 0

    def show(self):
        t_planets.add(self)

    def hide(self):
        t_planets.remove(self)

    def pick(self):
        self.mi_begin()

        # IMAGERY: planet-???.png
        if self.planet.flags & PLAGRI:
            image = ic.get("planet-" + teams[self.planet.owner] + "-agri.png")
        else:
            image = ic.get("planet-" + teams[self.planet.owner] + ".png")
        self.mi_add_image(image)

        # IMAGERY: planet-overlay-*.png
        if me.planet == self.planet and me.flags & PFPLLOCK:
            self.mi_add_image(ic.get('planet-overlay-lock.png'))
        if self.planet.armies > 4 and self.planet.owner != me.team:
            self.mi_add_image(ic.get('planet-overlay-attack.png'))
            # FIXME: show attack ring for unscanned planets as well?
        if self.planet.armies > 4:
            self.mi_add_image(ic.get('planet-overlay-army.png'))
        if self.planet.flags & PLREPAIR:
            self.mi_add_image(ic.get('planet-overlay-repair.png'))
        if self.planet.flags & PLFUEL:
            self.mi_add_image(ic.get('planet-overlay-fuel.png'))

        # planet name
        image = pygame.Surface((120, 120), pygame.SRCALPHA, 32)
        font = fc.get(FONT_SANS, 17)
        message = "%s" % (self.planet.name)
        text = font.render(message, 1, team_colour(self.planet.owner))
        rect = text.get_rect(centerx=60, bottom=120)
        # FIXME: name may not fit within surface
        image.blit(text, rect)
        self.mi_add_image(image)

        self.mi_commit()

    def update(self):
        reposition = False
        new = self.planet.owner, self.planet.info, self.planet.name, self.planet.flags, self.planet.armies, (self.planet == me.planet and me.flags & PFPLLOCK)
        if new != self.old:
            self.old = new
            self.pick()
            reposition = True
        new = me.x, me.y, self.planet.x, self.planet.y
        if new != self.pos:
            self.pos = new
            reposition = True
        if reposition:
            self.rect.center = n2ts(me, self.planet.x, self.planet.y)


class ShipSprite(MultipleImageSprite):
    def __init__(self, ship):
        self.ship = ship
        self.old = None
        MultipleImageSprite.__init__(self)


class ShipGalacticSprite(ShipSprite):
    # FIXME: a non-moving ship does not appear
    def __init__(self, ship):
        ShipSprite.__init__(self, ship)
        self.pick()

    def update(self):
        new = self.ship.dir, self.ship.team, self.ship.shiptype, self.ship.status, self.ship.flags
        if new != self.old:
            self.old = new
            self.pick()
        self.rect.center = n2gs(self.ship.x, self.ship.y)

    def pick(self):
        self.mi_begin()
        size = 22
        message = slot_decode(self.ship.n)
        colour = team_colour(self.ship.team)
        if self.ship.flags & (PFPRACTR | PFROBOT | PFBPROBOT):
            size = 16
        if self.ship.flags & (PFCLOAK):
            message = '?'
        if self.ship.status == PEXPLODE:
            message = '*'
        if self.ship.kills > 199:
            colour = brighten(colour)
        pos = 36
        ring = pygame.Surface((pos, pos), pygame.SRCALPHA, 32)
        rgba = list(colour)
        rgba.append(128)
        pygame.draw.ellipse(ring, rgba, pygame.Rect((0, 6), (pos, 24)), 2)
        pygame.draw.ellipse(ring, rgba, pygame.Rect((6, 0), (24, pos)), 2)
        self.mi_add_image(ring)
        font = fc.get(FONT_SANS, size)
        self.image = font.render(message, 1, colour)
        self.rect = self.image.get_rect()
        self.mi_add_image(self.image)
        self.mi_commit()

    def show(self):
        g_players.add(self)

    def hide(self):
        g_players.remove(self)


class ShipTacticalSprite(ShipSprite):
    def __init__(self, ship):
        ShipSprite.__init__(self, ship)
        self.tag = self.old_tag = None
        self.name = self.old_name = None
        self.pick()
        self.explosions = ['exp-10.png', 'exp-09.png', 'exp-08.png',
                           'exp-07.png', 'exp-06.png', 'exp-05.png', 'exp-04.png',
                           'exp-03.png', 'exp-02.png', 'exp-01.png', 'exp-00.png']

    def update(self):
        new = self.ship.dir, self.ship.team, self.ship.shiptype, self.ship.status, self.ship.flags, self.ship.fuse
        if new != self.old:
            self.old = new
            self.pick()
        self.rect.center = n2ts(me, self.ship.x, self.ship.y)

    def add_explosion(self):
        # IMAGERY: exp-??.png
        # FIXME: works fine at 10ups, looks wrong at 25ups.
        x = max(self.ship.fuse, 0)
        try:
            self.mi_add_image(ic.get(self.explosions[x]))
        except:
            self.mi_add_image(ic.get('explosion.png'))

    def add_ship(self):
        # IMAGERY: ???-??-40x40.png
        if self.ship.shiptype != STARBASE:
            rotation = self.ship.dir
        else:
            rotation = 0
        try:
            self.mi_add_image(ic.get_rotated(teams[self.ship.team] + '-' + ships[self.ship.shiptype] + "-40x40.png", rotation / 10 * 10))
        except:
            self.mi_add_image(ic.get_rotated('netrek.png', rotation / 16 * 16))

    def add_tag(self):
        new = self.ship.team, self.ship.flags & (PFPRACTR | PFROBOT | PFBPROBOT)
        if new != self.old_tag:
            self.old_tag = new
            pos = 76
            self.tag = pygame.Surface((pos, pos), pygame.SRCALPHA, 32)
            font = fc.get(FONT_SANS, 20)
            message = slot_decode(self.ship.n)
            colour = team_colour(self.ship.team)
            if self.ship.flags & (PFPRACTR | PFROBOT | PFBPROBOT):
                colour = (255, 0, 255)
            text = font.render(message, 1, colour)
            rect = text.get_rect(top=0, right=pos)
            self.tag.blit(text, rect)
        self.mi_add_image(self.tag)

    def add_name(self):
        new = self.ship.team, self.ship.flags & (PFPRACTR | PFROBOT | PFBPROBOT)
        if new != self.old_name:
            self.old_old_name = new
            pos = 80
            self.name = pygame.Surface((pos, pos), pygame.SRCALPHA, 32)
            font = fc.get(FONT_SANS, 16)
            message = self.ship.name.lower()
            colour = team_colour(self.ship.team)
            if self.ship.flags & (PFPRACTR | PFROBOT | PFBPROBOT):
                colour = (255, 0, 255)
            text = font.render(message, 1, colour)
            rect = text.get_rect(bottom=pos, centerx=pos/2)
            self.name.blit(text, rect)
        self.mi_add_image(self.name)

    def pick(self):
        self.mi_begin()
        status = self.ship.status
        flags = self.ship.flags
        if status == PEXPLODE:
            self.add_explosion()
        else:
            self.add_ship()
            if not flags & PFCLOAK:
                self.add_tag()
                if opt.ubertweak:
                    self.add_name()
        if status == PALIVE:
            if flags & PFCLOAK:
                # IMAGERY: ship-cloak.png
                self.mi_add_image(ic.get('ship-cloak.png'))
            if flags & PFSHIELD and (self.ship == me or not flags & PFCLOAK):
                # IMAGERY: shield-80x80.png
                self.mi_add_image(ic.get('shield-80x80.png'))
        self.mi_commit()

    def show(self):
        if not self.ship.flags & PFOBSERV:
            t_players.add(self)

    def hide(self):
        if not self.ship.flags & PFOBSERV:
            t_players.remove(self)


class TorpSprite(pygame.sprite.Sprite):
    def __init__(self, torp):
        self.torp = torp
        self.old_status = torp.status
        pygame.sprite.Sprite.__init__(self)


class TorpTacticalSprite(TorpSprite):
    def __init__(self, torp):
        TorpSprite.__init__(self, torp)
        self.teams = {IND: 'torp-ind.png', FED: 'torp-fed.png', ROM: 'torp-rom.png', KLI: 'torp-kli.png', ORI: 'torp-ori.png'}
        self.types = {TFREE: 'netrek.png',
                      TEXPLODE: 'torp-explode-200.png',
                      TDET: 'torp-det.png',
                      TOFF: 'torp-off.png',
                      TSTRAIGHT: 'torp-straight.png'}
        self.pick()

    def update(self):
        if self.torp.status == TEXPLODE:
            self.old_status = self.torp.status
            self.pick()
        else:
            if self.torp.status != self.old_status:
                self.old_status = self.torp.status
                self.pick()
        self.rect.center = n2ts(me, self.torp.x, self.torp.y)

    def pick(self):
        if self.torp.status == TMOVE:
            if self.torp.ship == me:
                # IMAGERY: torp-me.png
                self.image = ic.get('torp-me.png')
            else:
                # IMAGERY: torp-???.png
                self.image = ic.get(self.teams[self.torp.ship.team])
        elif self.torp.status == TEXPLODE:
            # IMAGERY: torp-explode.png
            # IMAGERY: torp-explode-*.png
            exp = ['torp-explode-20.png', 'torp-explode-40.png', 'torp-explode-60.png',
                   'torp-explode-80.png', 'torp-explode-100.png', 'torp-explode-120.png',
                   'torp-explode-140.png', 'torp-explode-160.png', 'torp-explode-180.png',
                   'torp-explode-200.png']
            try:
                self.image = ic.get(exp[self.torp.fuse])
            except:
                self.image = ic.get('torp-explode.png')
        else:
            self.image = ic.get('netrek.png')
        self.rect = self.image.get_rect()

    def show(self):
        t_torps.add(self)

    def hide(self):
        t_torps.remove(self)


class PlasmaSprite(pygame.sprite.Sprite):
    def __init__(self, plasma):
        self.plasma = plasma
        self.old_status = plasma.status
        pygame.sprite.Sprite.__init__(self)


class PlasmaTacticalSprite(PlasmaSprite):
    def __init__(self, plasma):
        PlasmaSprite.__init__(self, plasma)
        self.pick()

    def update(self):
        if self.plasma.status != self.old_status:
            self.old_status = self.plasma.status
            self.pick()
        self.rect.center = n2ts(me, self.plasma.x, self.plasma.y)

    def pick(self):
        if self.plasma.status == PTMOVE:
            self.image = ic.get('plasma-move.png')
            self.rect = self.image.get_rect()
        elif self.plasma.status == TEXPLODE:
            self.image = ic.get('plasma-explode.png')
            self.rect = self.image.get_rect()
        else:
            self.image = None
            self.rect = None

    def show(self):
        t_plasma.add(self)

    def hide(self):
        t_plasma.remove(self)
