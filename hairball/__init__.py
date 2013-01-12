import kurt
import os
import sys
from optparse import OptionParser


__version__ = '0.1a'


class ScratchAnalysis(object):
    def __init__(self, argv):
        self.plugins = []
        description = ('PATH can be either the path to a scratch file, or a '
                       'directory containing scratch files. Multiple PATH '
                       'arguments can be provided.')
        parser = OptionParser(usage='%prog -p PLUGIN_NAME [options] PATH...',
                              description=description)
        parser.add_option('-p', '--plugin', action='append')
        self.options, self.args = parser.parse_args(argv)

        if not self.options.plugin:
            parser.error('At least one plugin must be specified via -p.')
        if not self.args:
            parser.error('At least one PATH must be provided.')

    def finalize(self):
        for plugin in self.plugins:
            plugin.finalize()

    def initialize_plugins(self):
        for plugin_name in self.options.plugin:
            parts = plugin_name.split('.')
            if len(parts) > 1:
                module_name = '.'.join(parts[:-1])
                class_name = parts[-1]
            else:
                # Use the titlecase format of the module name as the class name
                module_name = parts[0]
                class_name = parts[0].title()

            try:
                module = __import__('hairball.plugins.{0}'.format(module_name),
                                    fromlist=[class_name])
                self.plugins.append(getattr(module, class_name)())
            except (AttributeError, ImportError):
                print 'Not a plugin: {!r}'.format(plugin_name)
                continue

        if not self.plugins:
            print 'No plugins loaded. Goodbye!'
            sys.exit(1)

    def process(self):
        sbfiles = []
        while self.args:
            filename = self.args.pop()
            if os.path.isdir(filename):
                for temp in os.listdir(filename):
                    if temp not in ('.', '..'):
                        self.args.append(os.path.join(filename, temp))
            elif os.path.isfile(filename) and filename.endswith('.sb'):
                sbfiles.append(filename)
        for file in sbfiles:
            scratch = kurt.ScratchProjectFile(file)
            scratch.thumbnail_saved = True
            (pathname, file) = os.path.split(file)
            scratch.group = file[0:2]
            (path, dir) = os.path.split(pathname)
            scratch.project = dir
            for plugin in self.plugins:
                plugin._process(scratch)


def main():
    sa = ScratchAnalysis(sys.argv[1:])
    sa.initialize_plugins()
    sa.process()
    sa.finalize()
