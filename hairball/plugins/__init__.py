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

    BLOCKMAPPING = {"position": set([("move %n steps", "relative"),
                                     ("go to x:%n y:%n", "absolute"),
                                     ("go to %m", "relative"),
                                     ("glide %n secs to x:%n y:%n",
                                      "relative"),
                                     ("change x by %n", "relative"),
                                     ("x position", "absolute"),
                                     ("change y by %n", "relative"),
                                     ("y position", "absolute")]),
                    "orientation": set([("turn cw %n degrees", "relative"),
                                        ("turn ccw %n degrees", "relative"),
                                        ("point in direction %d", "absolute"),
                                        ("point towards %m", "relative")]),
                    "costume": set([("switch to background %l", "absolute"),
                                    ("next background", "relative"),
                                    ("switch to costume %l", "absolute"),
                                    ("next costume", "relative")]),
                    "size": set([("change size by %n", "relative"),
                                 ("set size to %n%", "absolute")])}

    @staticmethod
    def iter_blocks(block_list):
        """A generator for blocks contained in a block list.

        Yields tuples containing the block name, the "depth" that the block was
        found at, and finally a handle to the block itself.

        """
        # queue the block and the depth of the block
        queue = [(block, 0) for block in block_list
                 if isinstance(block, kurt.scripts.Block)]
        while queue:
            block, depth = queue.pop(0)
            if block.command == 'EventHatMorph':
                assert depth == 0
                if block.args[0] == 'Scratch-StartClicked':
                    yield 'when green flag clicked', depth, block
                else:
                    yield 'when I receive %e', depth, block
            elif block.command == 'changeVariable':
                if 'setVar' in str(block.args[1]):
                    yield 'set %v by %n', depth, block
                else:
                    yield block.type.text, depth, block
            elif block.command == '':
                # Not sure if this ever actually happens
                print('WARN: Empty command')
                continue
            else:
                if block.command == 'doIfElse':
                    yield 'if %b else', depth, block
                else:
                    yield block.type.text, depth, block
                for arg in block.args:
                    if hasattr(arg, '__iter__'):
                        queue[0:0] = [(x, depth + 1) for x in arg
                                      if isinstance(x, kurt.scripts.Block)]
                    elif isinstance(arg, kurt.scripts.Block):
                        queue.append((arg, depth))

    @classmethod
    def get_broadcast_events(cls, script):
        """Return a Counter of event-names that were broadcast.

        The Count will contain the key `True` if any of the broadcast blocks
        contain a  parameter that is a variable.

        """
        events = Counter()
        for name, _, block in cls.iter_blocks(script.blocks):
            if 'broadcast %e' in name:
                if isinstance(block.args[0], kurt.scripts.Block):
                    events[True] += 1
                else:
                    events[block.args[0].lower()] += 1
        return events

    @staticmethod
    def check_empty(word):
        """Return True if there is at least one character and no spaces.

        TODO: Check for the purpose. This can probably be replaced by `isalnum`
            or at the very least simplified and moved into a helper class.

        """
        if len(word) == 0:
            return True
        else:
            for letter in word:
                if letter != " ":
                    return False
        return True

    @classmethod
    def mark_scripts(cls, scratch):
        """Tag each script with attribute reachable.

        The reachable attribute will be set false, for any script that does not
        begin with a hat block. Additionally, any script that begins with a
        "when I receive" block whose event-name doesn't appear in a
        corresponding broadcast block is marked as unreachable.

        TODO: Rename for clarity.

        """
        processing = set()
        pending = {}
        scratch.static = True
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        # Find scripts without hat blocks
        for script in scripts:
            if cls.hat_type(script) == "No Hat":
                script.reachable = False
            elif cls.hat_type(script) == "when I receive %e":
                message = script.blocks[0].args[0].lower()
                script.reachable = True
                if message in pending.keys():
                    pending[message].add(script)
                else:
                    pending[message] = {script}
            else:
                script.reachable = True
                processing.add(script)
        while len(processing) != 0:
            script = processing.pop()
            for event in cls.get_broadcast_events(script):
                if event in pending.keys():
                    for s in pending[event]:
                        processing.add(s)
                    del pending[event]
        while len(pending) != 0:
            (message, scripts) = pending.popitem()
            for script in scripts:
                script.reachable = False
        scratch.plugin_prepared = True

    @staticmethod
    def hat_type(script):
        """Helper that returns the hat type of the block.

        TODO: Refactor or remove.

        """
        if script.blocks[0].command == 'EventHatMorph':
            if script.blocks[0].args[0] == 'Scratch-StartClicked':
                return "when green flag clicked"
            else:
                return "when I receive %e"
        elif 'EventHatMorph' in script.blocks[0].command:
            return script.blocks[0].command
        else:
            return "No Hat"

    @classmethod
    def pull_hat(cls, hat_name, all_scripts):
        """Return a tuple of lists separating reachable scripts.

        The first list in the tuple are scripts that are reachable due to the
        fact that they begin with a hat block (note: some of these may not
        actually be reachable due to the lack of a corresponding broadcast
        event). The second list in the tuple contains all other scripts, i.e.,
        those that do not begin with hat blocks.

        TODO: rename or remove

        """
        hat_scripts = []
        other = []
        scripts = all_scripts[:]
        for script in scripts:
            if cls.hat_type(script) == hat_name:
                hat_scripts.append(script)
            else:
                other.append(script)
        return hat_scripts, other

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

    def finalize(self):
        """Overwrite this function to be notified when analysis is complete.

        This is useful for saving/outputing aggregate results or performing any
        necessary cleanup.

        """
        pass

    def _process(self, scratch, **kwargs):
        if not hasattr(scratch, 'plugin_prepared'):
            self.mark_scripts(scratch)
        return self.analyze(scratch, **kwargs)
