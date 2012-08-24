import copy
from . import PluginController, PluginView, PluginWrapper


class AnimationView(PluginView):
    def view(self, data):
        images = ""
        sprite_str = ""
        for (sprite, results) in data["animation"].items():
            for (change, timing) in results:
                sprite_str += "Change: {0}, Timing: {1}; ".format(
                    change, timing)
            images += "Sprite {0}: {1}".format(sprite, sprite_str) + '<br />'
        return '<p>{0}</p>'.format(images)


class Animation(PluginController):
    """Animation

    Checks for possible errors relating to animation.
    Animation should include loops, motion, timing, and costume changes.
    """
    def __init__(self):
        super(Animation, self).__init__()
        self.animation = {}

    def finalize(self):
        file = open('animation.txt', 'w')
        file.write("activity, pair: rotation animation")
        for ((group, project), sprites) in self.animation.items():
            file.write('\n{0}, {1}: '.format(project, group))
            attributes = self.format_all(sprites)
            for attr in attributes:
                file.write(",".join(attr))
                file.write(" ")

    def format_all(self, sprites):
        rotation = []
        animation = []
        if len(sprites) == 0:
            return rotation, animation
        for (sprite, checks) in sprites.items():
            for (r, a) in checks:
                rotation.append(str(int(r)))
                animation.append(str(int(a)))
        return rotation, animation

    def check_loop(self, level, gen):
        movement = False
        rotation = False
        costume = False
        timing = False
        switch_to = False
        (name, l, block) = next(gen, ("wtf", -1, ""))
        while l == level:
            if block.type.flag == 't':
                timing = True
            if "turn" in name:
                rotation = True
            elif block.type.category == "motion":
                if "change" in name or "go to" in name:
                    movement = True
                elif "move" in name or "set" in name:
                    movement = True
            if name == "next costume":
                costume = True
            if name == "switch to costume %l":
                if switch_to:
                    costume = True
                else:
                    switch_to = True
            (name, l, block) = next(gen, ("", -1, ""))
        animation = timing and costume and movement
        return (rotation, animation)

    @PluginWrapper(html=AnimationView)
    def analyze(self, scratch):
        animation = {}
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            gen = self.block_iter(script.blocks)
            for name, level, block in gen:
                if "forever" in name or "repeat" in name:
                    (r, a) = self.check_loop(level + 1, gen)
                    if (r, a) != (False, False):
                        if script.morph.name not in animation.keys():
                            animation[script.morph.name] = [(r, a)]
                        else:
                            animation[script.morph.name].append((r, a))
        if hasattr(scratch, 'group') and hasattr(scratch, 'project'):
            self.animation[(scratch.group,
                            scratch.project)] = copy.deepcopy(animation)
        return self.view_data(animation=animation)


class BroadcastReceiveView(PluginView):
    def view(self, data):
        images = ""
        message_str = ""
        for (error, messages) in data["broadcast"].items():
            if len(messages) != 0:
                message_str = ', '.join(messages)
                images += "error {0}: {1}".format(
                    error, message_str) + '<br />'
        return '<p>{0}</p>'.format(images)


class BroadcastReceive(PluginController):
    """Broadcast Receive

    Shows possible errors relating to broadcast and receive blocks
    """
    def __init__(self):
        super(BroadcastReceive, self).__init__()
        self.broadcast = {}

    def finalize(self):
        file = open('broadcastreceive.txt', 'w')
        file.write("activity, pair:  error 0; error 1; error 2; error 3")
        for ((group, project), mistakes) in self.broadcast.items():
            file.write('\n{0}, {1}: '.format(project, group))
            if len(mistakes) != 0:
                for (error, messages) in mistakes.items():
                    if len(messages) != 0:
                        for x in range(len(messages)):
                            file.write("{0},".format(error))

    @PluginWrapper(html=BroadcastReceiveView)
    def analyze(self, scratch):
        all_scripts = scratch.stage.scripts[:]
        [all_scripts.extend(x.scripts) for x in scratch.stage.sprites]
        errors = {}
        errors[0] = set()  # sprites who broadcast dynamic messages
        errors[1] = set()  # message is broadcasted in dead code
        errors[2] = set()  # meessage is never broadcasted
        errors[3] = set()  # message is never received
        errors[4] = set()  # message is circularly broadcast; TO DO
        (errors[3], errors[2]) = self.broadcastreceive(all_scripts)
        for (message, scripts) in self.get_broadcast(all_scripts).items():
            for script in scripts:
                if not script.reachable:  # broadcast in dead code
                    errors[1].add(message)
            if message == "dynamic":  # dynamic broadcast
                errors[0].add(script.morph.name)
        if hasattr(scratch, 'group') and hasattr(scratch, 'project'):
            self.broadcast[(scratch.group,
                            scratch.project)] = errors
        return self.view_data(broadcast=errors)


class SoundSynchView(PluginView):
    def view(self, data):
        results = ""
        if len(data['sound']) == 0:
            results = "No sound"
        else:
            results = "errors: {0}".format(", ".join(data['sound']))
        return '<p>{0}</p>'.format(results)


class SoundSynch(PluginController):
    """Sound Synch

    Checks for errors when dealing with sound/say bubble synchronization
    The order should be:
    Say "___",
    Play sound "___" until done,
    Say ""
    """
    def __init__(self):
        super(SoundSynch, self).__init__()
        self.sound = {}

    def finalize(self):
        file = open('soundsynch.txt', 'w')
        file.write("activity, pair: sound synchronization")
        for ((group, project), results) in self.sound.items():
            file.write('\n{0}, {1}: '.format(project, group))
            if len(results) != 0:
                file.write(",".join(results))

    def check(self, gen):
        errors = []
        (name, level, block) = next(gen, ("", 0, ""))
        if name == "say %s" or name == "think %s":
            # counts as blank if it's a string made up of spaces
            if self.check_empty(block.args[0]):
                return '3'
            else:
                (name, level, block) = next(gen, ("", 0, ""))
                if name == "play sound %S until done":
                    errors.append('3')
                    errors.extend(self.check(gen))
                    return errors
                else:
                    return '1'
        else:
            return '1'

    @PluginWrapper(html=SoundSynchView)
    def analyze(self, scratch):
        errors = []
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            (last_name, last_level, last_block) = ("", 0, script.blocks[0])
            gen = self.block_iter(script.blocks)
            for name, level, block in gen:
                if last_level == level:
                    if last_name == "say %s":
                        if not self.check_empty(last_block.args[0]):
                            if name == "play sound %S until done":
                                errors.extend(self.check(gen))
                    elif last_name == "play sound %S":
                        if name == "say %s for %n secs":
                            if not self.check_empty(block.args[0]):
                                errors.append('2')
                            else:
                                errors.append('1')
                        elif name == "say %s":
                            errors.append('1')
                    elif "play sound %S" in last_name and "say %s" in name:
                        if not self.check_empty(block.args[0]):
                            errors.append('1')
                    elif "play sound %S" in name and "say %s" in last_name:
                        errors.append('1')
                (last_name, last_level, last_block) = (name, level, block)
        if hasattr(scratch, 'group') and hasattr(scratch, 'project'):
            self.sound[(scratch.group,
                        scratch.project)] = errors
        return self.view_data(sound=errors)
