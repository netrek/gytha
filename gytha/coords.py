"""
Coordinate conversion functions for gytha.

Module-level state (r_us, r_sg, galactic_factor, subgalactic_factor,
is_galactic) is set once by pg_init() and updated at each galactic/tactical
view switch.  All functions read those names from this module's namespace, so
assignments via `coords.r_us = …` take effect immediately.
"""

import math
import pygame

from .constants import GWIDTH

# Set by pg_init() after the display surface is created.
r_us = None
r_sg = None
galactic_factor = None
subgalactic_factor = None

# Set True when PhaseFlightGalactic is active, False for PhaseFlightTactical.
is_galactic = False


def n2ss(x, y):
    """Netrek to subgalactic screen coordinate conversion."""
    return (x / subgalactic_factor + r_sg.left,
            y / subgalactic_factor + r_sg.top)


def n2gs(x, y):
    """Netrek to galactic screen coordinate conversion."""
    return (x / galactic_factor + r_us.left,
            y / galactic_factor + r_us.top)


def n2ts(me, x, y):
    """Netrek to tactical screen coordinate conversion."""
    return ((x - me.x) // 20 + r_us.centerx,
            (y - me.y) // 20 + r_us.centery)


def gs2n(x, y):
    """Galactic screen to netrek coordinate conversion."""
    return ((x - r_us.left) * galactic_factor,
            (y - r_us.top) * galactic_factor)


def ts2n(me, x, y):
    """Tactical screen to netrek coordinate conversion."""
    return ((x - r_us.centerx) * 20 + me.x,
            (y - r_us.centery) * 20 + me.y)


def s2g(me, x, y):
    """Screen to netrek coordinate conversion (dispatches by view mode)."""
    if is_galactic:
        return gs2n(x, y)
    else:
        return ts2n(me, x, y)


def cursor(me):
    """Return the netrek coordinates of the mouse cursor."""
    x, y = pygame.mouse.get_pos()
    return s2g(me, x, y)


def intragalactic(xy):
    """Return True if netrek coordinates xy lie within the galaxy."""
    x, y = xy
    return (0 < x < GWIDTH) and (0 < y < GWIDTH)


def d2a(dir):
    """Convert netrek direction (0-255) to angle in degrees (0-359)."""
    return dir * 360 / 256


def s2d(me, x, y):
    """Screen coordinate to netrek direction (0-255) conversion."""
    if is_galactic:
        (mx, my) = n2gs(me.x, me.y)
    else:
        (mx, my) = n2ts(me, me.x, me.y)
    return int((math.atan2(x - mx, my - y) / math.pi * 128.0 + 0.5))


def n_o(p1, p2):
    """Netrek coordinates to offset."""
    (x1, y1) = p1
    (x2, y2) = p2
    return (abs(x1 - x2), abs(y1 - y2))


def o_d(offset_x, offset_y):
    """Offset to distance."""
    return int((offset_x ** 2 + offset_y ** 2) ** 0.5)


def n_d(p1, p2):
    """Netrek coordinates to distance."""
    (offset_x, offset_y) = n_o(p1, p2)
    return o_d(offset_x, offset_y)
