"""This module provides the code necessary to write a Hairball plugin."""

import kurt
from collections import Counter


class HairballPlugin(object):

    """The simple plugin name should go on the first comment line.

    The plugin description should start on the third line and can span as many
    lines as needed, though all newlines will be treated as a single space.

    If you are seeing this message it means you need to define a docstring for
    your plugin.

    """

    HAT_GREEN_FLAG = 0
    HAT_WHEN_I_RECEIVE = 1
    HAT_MOUSE = 2
    HAT_KEY = 3
    NO_HAT = 4

    BLOCKMAPPING = {
        'costume': frozenset([('switch to background %l', 'absolute'),
                              ('next background', 'relative'),
                              ('switch to costume %l', 'absolute'),
                              ('next costume', 'relative')]),
        'orientation': frozenset([('turn cw %n degrees', 'relative'),
                                  ('turn ccw %n degrees', 'relative'),
                                  ('point in direction %d', 'absolute'),
                                  ('point towards %m', 'relative')]),
        'position': frozenset([('move %n steps', 'relative'),
                               ('go to x:%n y:%n', 'absolute'),
                               ('go to %m', 'relative'),
                               ('glide %n secs to x:%n y:%n', 'relative'),
                               ('change x by %n', 'relative'),
                               ('x position', 'absolute'),
                               ('change y by %n', 'relative'),
                               ('y position', 'absolute')]),
        'size': frozenset([('change size by %n', 'relative'),
                           ('set size to %n%', 'absolute')]),
        'visibility': frozenset([('hide', 'absolute'),
                                 ('show', 'absolute')])}

    @staticmethod
    def iter_blocks(block_list):
        """A generator for blocks contained in a block list.

        Yields tuples containing the block name, the depth that the block was
        found at, and finally a handle to the block itself.

        """
        # queue the block and the depth of the block
        queue = [(block, 0) for block in block_list
                 if isinstance(block, kurt.Block)]
        while queue:
            block, depth = queue.pop(0)
            assert block.type.text
            yield block.type.text, depth, block
            for arg in block.args:
                if hasattr(arg, '__iter__'):
                    queue[0:0] = [(x, depth + 1) for x in arg
                                  if isinstance(x, kurt.Block)]
                elif isinstance(arg, kurt.Block):
                    queue.append((arg, depth))

    @staticmethod
    def iter_scripts(scratch):
        """A generator for all scripts contained in a scratch file.

        yields stage scripts first, then scripts for each sprite

        """
        for script in scratch.stage.scripts:
            yield script
        for sprite in scratch.sprites:
            for script in sprite.scripts:
                yield script

    @staticmethod
    def iter_sprite_scripts(scratch):
        """A generator for all scripts contained in a scratch file.

        yields stage scripts first, then scripts for each sprite

        """

        for script in scratch.stage.scripts:
            yield ('Stage', script)
        for sprite in scratch.sprites:
            for script in sprite.scripts:
                yield (sprite.name, script)

    @staticmethod
    def script_start_type(script):
        """Return the type of block the script begins with."""
        if script[0].type.text == 'when @greenFlag clicked':
            return HairballPlugin.HAT_GREEN_FLAG
        elif script[0].type.text == 'when I receive %s':
            return HairballPlugin.HAT_WHEN_I_RECEIVE
        elif script[0].type.text == 'when this sprite clicked':
            return HairballPlugin.HAT_MOUSE
        elif script[0].type.text == 'when %s key pressed':
            return HairballPlugin.HAT_KEY
        else:
            return HairballPlugin.NO_HAT


    @classmethod
    def get_broadcast_events(cls, script):
        """Return a Counter of event-names that were broadcast.

        The Count will contain the key `True` if any of the broadcast blocks
        contain a  parameter that is a variable.

        """
        events = Counter()
        for name, _, block in cls.iter_blocks(script.blocks):
            if 'broadcast %e' in name:
                if isinstance(block.args[0], kurt.Block):
                    events[True] += 1
                else:
                    events[block.args[0].lower()] += 1
        return events

    @classmethod
    def tag_reachable_scripts(cls, scratch):
        """Tag each script with attribute reachable.

        The reachable attribute will be set false for any script that does not
        begin with a hat block. Additionally, any script that begins with a
        `when I receive` block whose event-name doesn't appear in a
        corresponding broadcast block is marked as unreachable.

        """
        reachable = set()
        untriggered_events = {}
        # Initial pass to find reachable and potentially reachable scripts
        for script in cls.iter_scripts(scratch):
            starting_type = cls.script_start_type(script)
            if starting_type == cls.NO_HAT:
                script.reachable = False
            elif starting_type == cls.HAT_WHEN_I_RECEIVE:
                script.reachable = False  # Value will be updated if reachable
                message = script.blocks[0].args[0].lower()
                untriggered_events.setdefault(message, set()).add(script)
            else:
                script.reachable = True
                reachable.add(script)
        # Expand reachable states based on broadcast events
        while reachable:
            for event in cls.get_broadcast_events(reachable.pop()):
                if event in untriggered_events:
                    for script in untriggered_events.pop(event):
                        script.reachable = True
                        reachable.add(script)
        scratch.hairball_prepared = True

    @property
    def description(self):
        """Attribute that returns the plugin description from its docstring."""
        lines = []
        for line in self.__doc__.split('\n')[2:]:
            line = line.strip()
            if line:
                lines.append(line)
        return ' '.join(lines)

    @property
    def name(self):
        """Attribute that returns the plugin name from its docstring."""
        return self.__doc__.split('\n')[0]

    def _process(self, scratch, **kwargs):
        """Internal hook that marks reachable scripts before calling analyze.

        Returns data exactly as returned by the analyze method.

        """
        if not getattr(scratch, 'hairball_prepared', False):
            self.tag_reachable_scripts(scratch)
        return self.analyze(scratch, **kwargs)

    def analyze(self, scratch, **kwargs):
        """Perform the analysis and return the results.

        This function must be overridden by a subclass.

        """
        raise NotImplementedError('Subclass must implement this method')

    def finalize(self):
        """Overwrite this function to be notified when analysis is complete.

        This is useful for saving/outputing aggregate results or performing any
        necessary cleanup.

        """
        pass
