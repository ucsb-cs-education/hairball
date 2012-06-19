from . import PluginBase


class Blocks(PluginBase):
    """Produces an aggregate count of blocks contained in a scratch file."""

    def __init__(self, batch):
        super(Blocks, self).__init__(name='Basic Blocks', batch=batch)

    def process(self, scratch_file):
        pass


class History(PluginBase):
    """Produces a display for the history contained in a scratch file."""

    def __init__(self, batch):
        super(Blocks, self).__init__(name='Basic History', batch=batch)

    def process(self, scratch_file):
        pass


class Sprites(Blocks):
    """Produces a visual of all sprites contained in a scratch file."""

    def __init__(self, batch):
        super(Blocks, self).__init__('Basic Sprites', batch)

    def process(self, scratch_file):
        pass
