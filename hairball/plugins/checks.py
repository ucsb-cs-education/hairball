import copy
from collections import Counter
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
        file.write("activity, pair: 3 2 1 0")
        for ((group, project), results) in self.animation.items():
            file.write('\n{0}, {1}: '.format(project, group))
            file.write('{0} {1} {2} {3}'.format(
                    results['3'], results['2'],
                    results['1'], results['0']))

    def check_block(self, name, block):
        movement = False
        rotation = False
        costume = False
        timing = False
        switch = False
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
            switch = True
        return (movement, rotation, costume, timing, switch)

    def check_loop(self, level, gen):
        movement = False
        rotation = False
        costume = False
        timing = False
        switch = False
        (name, l, block) = next(gen, ("wtf", -1, ""))
        while l == level:
            (m, r, c, t, s) = self.check_block(name, block)
            if m and not movement:
                movement = True
            if r and not rotation:
                rotation = True
            if c and not costume:
                costume = True
            if t and not timing:
                timing = True
            if s:
                if switch:
                    costume = True
                    switch = False
                else:
                    switch = True
            (name, l, block) = next(gen, ("", -1, ""))
        if timing and (costume or rotation):
            return '3'
        elif rotation or (timing and movement):
            return '2'

    @PluginWrapper(html=AnimationView)
    def analyze(self, scratch):
        stop_check = set(["broadcast %e and wait", 'forever if %b',
                          'if %b', 'if %b else', 'wait until %b',
                          'repeat until %b', 'forever',
                          'repeat %n', 'broadcast %e'])
        animation = Counter()
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            timing = False
            costume1 = False
            costume = False
            gen = self.block_iter(script.blocks)
            for name, level, block in gen:
                if name in stop_check:
                    timing = False
                    costume1 = False
                    costume = False
                if "forever" in name or "repeat" in name:
                    animation.update({
                            self.check_loop(level + 1, gen): 1})
                else:
                    (m, r, c, t, s) = self.check_block(name, block)
                    if t and not timing:
                        timing = True
                    if c or s:
                        if not costume1:
                            costume1 = True
                        else:
                           costume1 = False
                           costume = True
                    if costume and timing:
                        animation.update({'0': 1})
                        costume = False
                        costume1 = False
                        timing = False
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
        file.write("activity, pair: 3 2 1.5 1 0")
        for ((group, project), mistakes) in self.broadcast.items():
            file.write('\n{0}, {1}: '.format(project, group))
            if len(mistakes) != 0:
                if project == "06_MayanConversation":
                    self.mayan(mistakes)
                zero = len(mistakes[2]) + len(mistakes[3]) + len(mistakes[1])
                one_and_two = len(mistakes[4] & mistakes[5])
                one = len(mistakes[4]) - one_and_two
                two = len(mistakes[5]) - one_and_two
                three = len(mistakes[6])
                file.write("{0} {1} {2} {3} {4}".format(
                        three, two, one_and_two, one, zero))

    def mayan(self, mistakes):
        for x in range(7):
            if "final scene" in mistakes[x]:
                mistakes[x].remove("final scene")
        return mistakes

    def get_receive(self, script_list):
        messages = {}
        scripts = script_list[:]
        for script in scripts:
            if PluginController.hat_type(script) == "when I receive %e":
                message = script.blocks[0].args[0].lower()
                if message not in messages.keys():
                    messages[message] = set()
                messages[message].add(script)
        return messages

    def broadcast_scripts(self, script_list):
        scripts = script_list[:]
        messages = {}
        for script in scripts:
            messages[script] = self.get_broadcast(script)
        return messages

    def analyze(self, scratch):
        all_scripts = scratch.stage.scripts[:]
        [all_scripts.extend(x.scripts) for x in scratch.stage.sprites]
        errors = {}
        errors[0] = set()  # sprites who broadcast dynamic messages
        errors[1] = set()  # message is broadcasted in dead code
        errors[2] = set()  # message is never broadcast
        errors[3] = set()  # message is never received
        errors[4] = set()  # message has parallel scripts with timing
        errors[5] = set()  # messages are broadcast in scripts w/other broadcasts
        errors[6] = set()  # working
        errors[7] = set()  # TO DO
        broadcast = self.broadcast_scripts(all_scripts)
        receive = self.get_receive(all_scripts)
        received_messages = set()
        for message in receive.keys():
            received_messages.add(message)
            errors[3].add(message)
        # first remove all dynamic broadcast messages
        for script, messages in broadcast.items():
            for message in messages:
                if message == "dynamic":
                    errors[0].add(script.morph.name)
                    del message
        # then remove messages that aren't received or broadcast
                elif message in received_messages:
                    if message in errors[3]:
                        errors[3].remove(message)
                else:
                    errors[2].add(message)
        for message in receive.keys():
            if message not in received_messages:
                del receive[message]
            if message in errors[3]:
                del receive[message]
        # now find error 4
        for message, scripts in receive.items():
            if len(scripts) > 1:
                for script in scripts:
                    for name, level, block in self.block_iter(script.blocks):
                        if block.type.flag == 't':
                            errors[4].add(message)
        # now find error 5
        for script, messages in broadcast.items():
            if len(messages) > 1:
                for message in messages:
                    if message in receive.keys():
                        errors[5].add(message)
        # finally, get the working messages
        for message in receive.keys():
            if message not in errors[4] and message not in errors[5]:
                errors[6].add(message)
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
                    elif last_name == "think %s":
                        if not self.check_empty(last_block.args[0]):
                            if name == "play sound %S until done":
                                errors.extend(self.check(gen))
                    elif last_name == "play sound %S":
                        if name == "say %s for %n secs":
                            if not self.check_empty(block.args[0]):
                                errors.append('2')
                            else:
                                errors.append('1')
                        elif name == "think %s for %n secs":
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
                    elif "play sound %S" in last_name and "think %s" in name:
                        if not self.check_empty(block.args[0]):
                            errors.append('1')
                    elif "play sound %S" in name and "think %s" in last_name:
                        errors.append('1')
                (last_name, last_level, last_block) = (name, level, block)
        if hasattr(scratch, 'group') and hasattr(scratch, 'project'):
            self.sound[(scratch.group,
                        scratch.project)] = errors
        return self.view_data(sound=errors)
