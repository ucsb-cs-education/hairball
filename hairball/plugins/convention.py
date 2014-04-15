"""This module provides plugins for basic programming convention checks."""

from __future__ import print_function
from hairball.plugins import HairballPlugin


class SpriteNaming(HairballPlugin):

    """Plugin that keeps track of how often sprites' default names are used.

    E.g., Sprite1, Sprite2, ...

    """

    def __init__(self):
        """Initialize an instance of the SpriteNaming plugin."""
        super(SpriteNaming, self).__init__()
        self.total_default = 0
        self.list_default = []
        self.default_names = ['Sprite', 'Objeto']

    def finalize(self):
        """Output the default sprite names found in the project."""
        print("%d default sprite names found:" % self.total_default)
        for name in self.list_default:
            print(name)

    def analyze(self, scratch):
        """Run and return the results from the SpriteNaming plugin."""
        for sprite in self.iter_sprites(scratch):
            for default in self.default_names:
                if default in sprite.name:
                    self.total_default += 1
                    self.list_default.append(sprite.name)
