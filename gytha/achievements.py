"""
Player achievement tracking — persistent per-session learning milestones.

Module-level state — set by gytha/__init__.py:

  opt    - parsed CLI options  (set at start of main; opt.ubertweak controls display)
  me     - current player Ship (set by SP_YOU hook via _sync_me)
  b_info - info overlay group  (set by pg_init; used to gate delivery)
  sound  - sound module        (set at module load)
"""
import json
import os
import time

from .constants import PFGREEN
from .overlays import InfoSprite

# Module-level state — set by __init__.py
opt = None
me = None
b_info = None
sound = None

home = os.getenv('HOME')
if not home:
    home = ''
AC_FILE = os.path.join(home, '.gytha.achievements')

guidance = {}
guidance['Using Help'] = ['You can come back to read the help later.']
guidance['Using Keyboard Help'] = \
    ['- gives you an idea what else you can do.',
     '- use it as a checklist.']
guidance['Using Information'] = \
    ['- shows you how many armies are on a planet.',
     '- shows you what services a planet provides.',
     '- shows you if an enemy has kills.']
guidance['Using the Galactic Map'] = \
    ['- shows you the whole playing area.',
     '- you can do most of your green alert flying there.']
guidance['Moving'] = \
    ['- you are a sitting duck unless you move.',
     '- on the tactical, that is still you in the middle.']
guidance['Turning'] = \
    ['- use a turn to dodge enemy fire.',
     '- you will turn slower when you are moving faster.']
guidance['Planet Lock'] = \
    ['- you have locked onto a planet.',
     '- your ship will steer to the planet, unless you turn.',
     '- watch for other ships making a direct line to the planet.']
guidance['Orbit'] = \
    ['- you are in orbit around a planet.',
     '- if it is an enemy planet, you should bomb, press b once.',
     '- if it is a friendly planet, it will repair or refuel your ship.']
guidance['Bombing'] = \
    ['- you bombed armies from a planet, or killed armies in an enemy ship.']
guidance['Shields Lowered'] = \
    ['- lower your shields to conserve fuel.',
     '- raise your shields to preserve yourself.',
     '',
     '- flash your shields to draw attention.',
     '- lower your shields at the right moment to trigger a chain explosion.']
guidance['Phaser Hit'] = \
    ['- you hit an enemy with your phaser.',
     '- do it just enough to cripple them so they cannot move.',
     '- finish them off if they are carrying armies.',
     '- if they die, they get a fresh new ship.']
guidance['Detonate'] = \
    ['- you detonated all the enemy torpedos nearby ... if any.',
     '- the explosions hurt you, and the enemy ... but not your friends!']
guidance['Cloaked Flight'] = \
    ['- you are hard to see when cloaked.',
     '- watch your fuel, it will go quickly.']
guidance['Pick'] = \
    ['- you picked up armies.',
     '- take them to an enemy planet and beam them down!',
     '- put the mouse on that planet and press control/t to tell your team.',
     '- keep yourself safe, the armies are lost if you die.']
guidance['Drop'] = \
    ['- you have beamed down armies!']
guidance['Calling a Take'] = \
    ['- your team has been told you plan to take a planet.',
     '- hopefully they will use control/e to say they will escort.']
guidance['Calling Escort'] = \
    ['- your taker has been told you plan to help them.',
     '- now you should keep yourself between your taker and the enemy.']
guidance['A conquer parade!'] = \
    ['- this is where the game has been won.',
     '- wait for it to finish.']
guidance['Phaser Hit a Cloaked Enemy'] = \
    ['- you hit an cloaked enemy with your phaser.',
     '- the phaser tracks their true position.']
guidance['Phaser Hit a Plasma'] = \
    ['- you have hit an enemy plasma torpedo with your phaser!',
     '- it explodes violently, damaging everybody nearby.']
guidance['Drop on Agricultural'] = \
    ['- you have dropped armies on an agricultural planet,',
     '- this can be difficult because it may breed, or pop, at the same time.']
guidance['Drop on Enemy Homeworld'] = \
    ['- you have dropped armies on the enemy homeworld, quite audacious,',
     '- because an enemy may respawn right next to you.']
guidance['Ten Kills'] = \
    ['- accumulating kills is considered inefficient,',
     '- try to cripple the enemy rather than kill them,',
     '- you are not using your death explosion much,',
     '- try to die in the right place!']
guidance['Planet Hook'] = \
    ['- you manually made orbit while cloaked with enemies nearby']

sequence = [
    'Started',
    'Using Help',
    'Using Keyboard Help',
    'Using Information',
    'Using the Galactic Map',
    'Moving',
    'Turning',
    'Planet Lock',
    'Orbit',
    'Bombing',
    'Shields Lowered',
    'Phaser Hit',
    'Detonate',
    'Cloaked Flight',
    'Pick',
    'Drop',
    'Calling a Take',
    'Calling Escort',
    'A conquer parade!',
    'Phaser Hit a Cloaked Enemy',
    'Phaser Hit a Plasma',
    'Drop on Agricultural',
    'Drop on Enemy Homeworld',
    'Ten Kills',
    'Planet Hook',
]

promises = []
achievements = {}


def ac_load():
    global achievements
    try:
        text = open(AC_FILE, 'r').read()
        achievements = json.loads(text)
    except:
        achievements = {'Started': time.time()}

def ac_save():
    for key in promises:
        achievements[key] = time.time()
    text = json.dumps(achievements, sort_keys=True, ensure_ascii=False,
                      indent=0)
    open(AC_FILE, 'w').write(text)

def ac_done_now(key):
    global achievements
    if key in achievements:
        return
    achievements[key] = time.time()

    if not opt.ubertweak:
        return

    sound.achievement()
    tips = ["Achievement Unlocked: %s" % key]
    if key in guidance:
        tips.append('')
        for line in guidance[key]:
            tips.append('    ' + line)
    tips.append('')
    if len(achievements) > 2:
        tips.append('You have unlocked %d achievements out of %d!' % (len(achievements), len(sequence)))
        tips.append('')
    if len(achievements) > 6:
        for key in sequence:
            if key not in achievements:
                tips.append('Next: %s' % key)
                tips.append('')
                break
    tips.append('Press ESC to clear this message.')
    InfoSprite(tips, expires=10+len(tips)*2, fillcolour=(24, 48, 24, 64), bordercolour=(128, 255, 128))

def ac_done(key):
    global achievements, promises

    if key in achievements:
        return

    if not opt.ubertweak:
        achievements[key] = time.time()
        return

    if (me.flags & PFGREEN) and not b_info:
        ac_done_now(key)
        return

    if key not in promises:
        promises.append(key)

def ac_done_later(key):
    global achievements, promises

    if key in achievements:
        return

    if not opt.ubertweak:
        achievements[key] = time.time()
        return

    if key not in promises:
        promises.append(key)

def ac_deliver():
    global promises

    if len(promises) == 0:
        return

    if b_info:
        return

    if me.flags & PFGREEN:
        key = promises[0]
        ac_done_now(key)
        promises.remove(key)

def ac_progress():
    global achievements

    b_info.empty()

    tips = ["Achievements"]
    tips.append('')
    if len(achievements) > 2:
        tips.append('You have unlocked %d achievements out of %d!' %
                    (len(achievements), len(sequence)))
        tips.append('')

    tips.append('You have unlocked:')
    for key in achievements:
        tips.append('    ' + key)
    tips.append('')

    tips.append('You have not yet unlocked:')
    for key in sequence:
        if key not in achievements:
            tips.append('    ' + key)
    tips.append('')

    tips.append('Press ESC to clear this message.')
    InfoSprite(tips, expires=10+len(tips)*2, fillcolour=(24, 48, 24, 192), bordercolour=(128, 255, 128))
