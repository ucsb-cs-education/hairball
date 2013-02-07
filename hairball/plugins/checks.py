import copy
from collections import Counter
from . import HairballPlugin


class Animation(HairballPlugin):
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
            file.write('{0} {1} {2} {3}'
                       .format(results[3], results[2],
                               results[1], results[0]))

    def check_results(self, a):
        if a['t'] > 0:
            if a['l'] > 0:
                if a['rr'] > 0 or a['ra'] > 1:
                    print 1, 3, a
                    return 3
                elif a['cr'] > 0 or a['ca'] > 1:
                    print 2, 3, a
                    return 3
                elif a['mr'] > 0 or a['ma'] > 1:
                    print 3, 2, a
                    return 2
            if a['cr'] > 1 or a['ca'] > 2:
                print 4, 2, a
                return 2
            if a['mr'] > 0 or a['ma'] > 1:
                if a['cr'] > 0 or a['ca'] > 1:
                    print 6, 0, a
                    return 0
            if a['rr'] > 1 or a['ra'] > 2:
                print 7, 0, a
                return 0
            if a['sr'] > 1 or a['sa'] > 2:
                print 8, 0, a
                return 0
        if a['l'] > 0:
            if a['rr'] > 0 or a['ra'] > 1:
                print 9, 2, a
                return 2
            if a['cr'] > 0 or a['ca'] > 1:
                print 10, 0, a
                return 0
        return -1

    def check_animation(self, last, last_level, gen):
        loop = set(["repeat %n", "repeat until %b",
                    "forever", "forever if %b"])
        costume = set(["switch to costume %l", "next costume"])
        rotate = set(["turn cw %n degrees", "turn ccw %n degrees",
                      "point in direction %d"])
        motion = set(["change y by %n", "change x by %n",
                      "glide %n secs to x:%n y:%n",
                      "move %n steps", "go to x:%n y:%n"])
        timing = set(["wait %n secs", "glide %n secs to x:%n y:%n"])
        size = set(["change size by %n", "set size to %n%"])
        animation = costume | rotate | motion | timing | loop | size
        a = Counter()
        results = Counter()
        (name, level, block) = (last, last_level, last)
        others = False
        last_level = last_level
        while name in animation and level >= last_level:
            if name in loop:
                if block != last:
                    count = self.check_results(a)
                    if count > -1:
                        results.update({count: 1})
                    a.clear()
                a.update({'l': 1})
            if (name, "relative") in self.BLOCKMAPPING["costume"]:
                a.update({'cr': 1})
            elif (name, "absolute") in self.BLOCKMAPPING["costume"]:
                a.update({'ca': 1})
            if (name, "relative") in self.BLOCKMAPPING["orientation"]:
                a.update({'rr': 1})
            elif (name, "absolute") in self.BLOCKMAPPING["orientation"]:
                a.update({'ra': 1})
            if (name, "relative") in self.BLOCKMAPPING["position"]:
                a.update({'mr': 1})
            elif (name, "absolute") in self.BLOCKMAPPING["position"]:
                a.update({'ma': 1})
            if (name, "relative") in self.BLOCKMAPPING["size"]:
                a.update({'sr': 1})
            elif (name, "absolute") in self.BLOCKMAPPING["size"]:
                a.update({'sa': 1})
            if name in timing:
                a.update({'t': 1})
            last_level = level
            (name, level, block) = next(gen, ("", 0, ""))
            # allow some exceptions
            if name not in animation and name != "":
                if not others:
                    if block.type.flag != 't':
                        last_level = level
                        (name, level, block) = next(gen, ("", 0, ""))
                        others = True
        count = self.check_results(a)
        if count > -1:
            results.update({count: 1})
        return gen, results

    def analyze(self, scratch):
        print scratch.group
        scripts = []
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        loop = set(["repeat %n", "repeat until %b",
                    "forever", "forever if %b"])
        costume = set(["switch to costume %l", "next costume"])
        rotate = set(["turn cw %n degrees", "turn ccw %n degrees",
                      "point in direction %d"])
        motion = set(["change y by %n", "change x by %n",
                      "glide %n secs to x:%n y:%n",
                      "move %n steps", "go to x:%n y:%n"])
        timing = set(["wait %n secs", "glide %n secs to x:%n y:%n"])
        size = set(["change size by %n", "set size to %n%"])
        animation = costume | rotate | motion | timing | loop | size
        a = Counter()
        for script in scripts:
            gen = self.iter_blocks(script.blocks)
            name = "start"
            level = None
            while name != "":
                if name in animation:
                    (gen, count) = self.check_animation(name, level, gen)
                    a.update(count)
                (name, level, block) = next(gen, ("", 0, ""))
        if hasattr(scratch, 'group') and hasattr(scratch, 'project'):
            self.animation[(scratch.group,
                            scratch.project)] = copy.deepcopy(a)
        return {'animation': a}


class BroadcastReceive(HairballPlugin):
    """Broadcast Receive

    Shows possible errors relating to broadcast and receive blocks
    """
    def __init__(self):
        super(BroadcastReceive, self).__init__()
        self.broadcast = {}

    def finalize(self):
        file = open('broadcastreceive.txt', 'w')
        file.write("activity, pair: 3 1 0")
        for ((group, project), mistakes) in self.broadcast.items():
            file.write('\n{0}, {1}: '.format(project, group))
            if len(mistakes) != 0:
                if project == "06_MayanConversation":
                    self.mayan(mistakes)
                zero = len(mistakes[2]) + len(mistakes[3]) + len(mistakes[1])
                one = len(mistakes[4] | mistakes[5])
                three = len(mistakes[6])
                file.write("{0} {1} {2}".format(three, one, zero))

    def mayan(self, mistakes):
        for x in range(7):
            if "final scene" in mistakes[x]:
                mistakes[x].remove("final scene")
        return mistakes

    def get_receive(self, script_list):
        messages = {}
        scripts = script_list[:]
        for script in scripts:
            if self.script_start_type(script) == self.HAT_WHEN_I_RECEIVE:
                message = script.blocks[0].args[0].lower()
                if message not in messages.keys():
                    messages[message] = set()
                messages[message].add(script)
        return messages

    def broadcast_scripts(self, script_list):
        scripts = script_list[:]
        events = {}
        for script in scripts:
            events[script] = self.get_broadcast_events(script)
        return events

    def analyze(self, scratch):
        all_scripts = scratch.stage.scripts[:]
        [all_scripts.extend(x.scripts) for x in scratch.stage.sprites]
        errors = {}
        errors[0] = set()  # sprites who broadcast variable-events
        errors[1] = set()  # message is broadcasted in dead code
        errors[2] = set()  # message is never broadcast
        errors[3] = set()  # message is never received
        errors[4] = set()  # message has parallel scripts with timing
        # below: maybe check all scripts with the same hat block
        errors[5] = set()  # messages are broadcast in scripts that contain
                           # other broadcasts
        errors[6] = set()  # working
        errors[7] = set()  # TO DO
        broadcast = self.broadcast_scripts(all_scripts)
        receive = self.get_receive(all_scripts)
        received_messages = set()
        for message in receive.keys():
            received_messages.add(message)
            errors[3].add(message)
        # first remove all variable-event broadcast scripts
        for script, messages in broadcast.items():
            for message in messages:
                if message is True:
                    errors[0].add(script.morph.name)
                    #del message  # TODO: what was this meant to do?
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
                    for name, level, block in self.iter_blocks(script.blocks):
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
        return {'broadcast': errors}


class SaySoundSync(HairballPlugin):
    """Say and sound synchronization

    Checks for errors when dealing with sound/say bubble synchronization
    The order should be:
    Say "___",
    Play sound "___" until done,
    Say ""
    """

    CORRECT = -1
    ERROR = 0
    INCORRECT = 1
    HACKISH = 2

    SAY_THINK = ('say %s', 'think %s')
    SAY_THINK_DURATION = ('say %s for %n secs', 'think %s for %n secs')
    ALL_SAY_THINK = SAY_THINK + SAY_THINK_DURATION

    @staticmethod
    def is_blank(word):
        """Return True if the string is empty, or only whitespace."""
        return not word or word.isspace()

    def analyze(self, scratch):
        """Categorize instances of attempted say and sound synchronization."""
        errors = Counter()
        for script in self.iter_scripts(scratch):
            prev_name, prev_depth, prev_block = '', 0, script.blocks[0]
            gen = self.iter_blocks(script.blocks)
            for name, depth, block in gen:
                if prev_depth == depth:
                    if prev_name in self.SAY_THINK:
                        if name == 'play sound %S until done':
                            if not self.is_blank(prev_block.args[0]):
                                errors += self.check(gen)
                        # TODO: What about play sound?
                    elif prev_name in self.SAY_THINK_DURATION and \
                            'play sound %S' in name:
                        errors['1'] += 1
                    elif prev_name == 'play sound %S':
                        if name in self.SAY_THINK:
                            errors[self.INCORRECT] += 1
                        elif name in self.SAY_THINK_DURATION:
                            if self.is_blank(block.args[0]):
                                errors[self.ERROR] += 1
                            else:
                                errors[self.HACKISH] += 1
                    elif prev_name == 'play sound %S until done' and \
                            name in self.ALL_SAY_THINK:
                        if not self.is_blank(block.args[0]):
                            errors[self.INCORRECT] += 1
                        # TODO: Should there be an else clause here?
                prev_name, prev_depth, prev_block = name, depth, block
        return {'sound': errors}

    def check(self, gen):
        """Check that the last part of the chain matches.

        TODO: Fix to handle the following situation that appears to not work

        say 'message 1'
        play sound until done
        say 'message 2'
        say 'message 3'
        play sound until done
        say ''

        """
        retval = Counter()
        name, _, block = next(gen, ('', 0, ''))
        if name in self.SAY_THINK:
            if self.is_blank(block.args[0]):
                retval[self.CORRECT] += 1
            else:
                name, _, block = next(gen, ('', 0, ''))
                if name == 'play sound %S until done':
                    # Increment the correct count because we have at least
                    # one successful instance
                    retval[self.CORRECT] += 1
                    # This block represents the beginning of a second
                    retval += self.check(gen)
                else:
                    retval[self.INCORRECT] += 1
        else:
            retval[self.INCORRECT] += 1
        return retval
