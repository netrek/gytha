""" cache of pygame objects, to avoid repeated file I/O to images that
are used frequently in different ways, as an "strace -e open" shows
that a second pygame.image.load for the same file causes the file to
be opened again. """
import pygame

class IC:
    """ an image cache """
    def __init__(self):
        self.cache = {}
        self.cache_rotated = {}
        self.cache_scale2xed = {}
        self.hits = self.miss = 0
        self.hits_rotated = self.miss_rotated = 0
        self.paths = ['/usr/share/netrek-client-pygame/images/', 'images/']

    def read(self, name):
        """ try package location, otherwise try local directory """
        image = None
        for path in self.paths:
            try:
                image = pygame.image.load(path + name)
            except pygame.error:
                pass
        if not image:
            raise pygame.error
        return pygame.Surface.convert_alpha(image)

    def get(self, name):
        """ get an image from cache, normal """
        if name not in self.cache:
            self.cache[name] = self.read(name)
            self.miss += 1
        else:
            self.hits += 1
        return self.cache[name]

    def get_rotated(self, name, angle):
        """ get an image from cache, rotated """
        if (name, angle) not in self.cache_rotated:
            unrotated = self.get(name)
            self.miss_rotated += 1
            rotated = pygame.transform.rotate(unrotated, -angle)
            self.cache_rotated[(name, angle)] = rotated
        else:
            self.hits_rotated += 1
        return self.cache_rotated[(name, angle)]

    def get_scale2xed(self, name):
        """ get an image from cache, scaled up """
        if (name) not in self.cache_scale2xed:
            unscaled = self.get(name)
            try:
                scaled = pygame.transform.smoothscale(unscaled, (2000, 2000))
            except:
                scaled = pygame.transform.scale2x(unscaled)
            self.cache_scale2xed[(name)] = scaled
        return self.cache_scale2xed[(name)]

    def statistics(self):
        """ calculate and print cache statistics """
        if self.miss > 0:
            rate = self.hits * 100 / (self.hits + self.miss)
        else:
            rate = 0
        if self.miss_rotated > 0:
            rate_rotated = self.hits_rotated * 100 / \
                (self.hits_rotated + self.miss_rotated)
        else:
            rate_rotated = 0
        print "IC: normal hits=%d miss=%d rate=%d%% n=%d" % \
              (self.hits, self.miss, rate, len(self.cache))
        print "IC: rotate hits=%d miss=%d rate=%d%% n=%d" % \
              (self.hits_rotated, self.miss_rotated, rate_rotated, \
               len(self.cache_rotated))

class FC:
    """ a font cache """
    def __init__(self):
        self.cache = {}

    def read(self, name, size):
        """ try system font location, otherwise use default font """
        if name == None:
            return pygame.font.Font(None, size)
        path = '/usr/share/fonts/truetype/ttf-dejavu/'
        try:
            return pygame.font.Font(path + name, size)
        except IOError:
            return pygame.font.Font(None, size)

    def get(self, name, size):
        """ get a font from cache """
        key = (name, size)
        if key not in self.cache:
            self.cache[key] = self.read(name, size)
        return self.cache[key]
