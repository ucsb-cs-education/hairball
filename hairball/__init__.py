"""A plugin-able framework for the static analysis of Scratch projects."""

import appdirs
import cPickle
import importlib
import kurt
import os
import sys
from functools import wraps
from hashlib import sha1
from imp import load_source
from optparse import OptionParser
from .plugins import HairballPlugin


__version__ = '0.1rc3'


class Hairball(object):

    """The Hairball exeuction class.

    This class is responsible for parsing command line arguments, loading the
    plugins, and running the plugins on the specified scratch files.

    """

    DEFAULT_CACHE_PATH = os.path.join(
        appdirs.user_cache_dir(appname='Hairball', appauthor='bboe'),
        'parsed.pkl')

    @staticmethod
    def save_cache(function):
        """Write out the Hairball instance's cache at function exit."""
        @wraps(function)
        def function_wrapper(instance):
            try:
                return function(instance)
            finally:
                if instance._cache is not None and \
                        len(instance._cache) != instance._initial_cache_size:
                    print('Saving {} items to cache'
                          .format(len(instance._cache)))
                    with open(Hairball.DEFAULT_CACHE_PATH, 'wb') as fp:
                        cPickle.dump(instance._cache, fp,
                                     cPickle.HIGHEST_PROTOCOL)
        return function_wrapper

    def __init__(self, argv):
        """Initialize a Hairball instance by processing arguments."""
        description = ('PATH can be either the path to a scratch file, or a '
                       'directory containing scratch files. Multiple PATH '
                       'arguments can be provided.')
        parser = OptionParser(usage='%prog -p PLUGIN_NAME [options] PATH...',
                              description=description,
                              version='%prog {}'.format(__version__))
        parser.add_option('-d', '--plugin-dir', metavar='DIR',
                          help=('Specify the path to a directory containing '
                                'plugins. Plugins in this directory take '
                                'precedence over similarly named plugins '
                                'included with Hairball.'))
        parser.add_option('-p', '--plugin', action='append',
                          help=('Use the named plugin to perform analysis. '
                                'This option can be provided multiple times.'))
        parser.add_option('-k', '--kurt-plugin', action='append',
                          help=('Provide either a python import path (e.g, '
                                'kelp.octopi) to a package/module, or the path'
                                ' to a python file, which will be loaded as a '
                                'Kurt plugin. This option can be provided '
                                'multiple times.'))
        self.options, self.args = parser.parse_args(argv)

        if not self.options.plugin:
            parser.error('At least one plugin must be specified via -p.')
        if not self.args:
            parser.error('At least one PATH must be provided.')

        if self.options.plugin_dir:
            if os.path.isdir(self.options.plugin_dir):
                sys.path.append(self.options.plugin_dir)
            else:
                parser.error('{} is not a directory'
                             .format(self.options.plugin_dir))

        if self.options.kurt_plugin:
            for kurt_plugin in self.options.kurt_plugin:
                failure = False
                if kurt_plugin.endswith('.py') and os.path.isfile(kurt_plugin):
                    module = os.path.splitext(os.path.basename(kurt_plugin))[0]
                    try:
                        load_source(module, kurt_plugin)
                    except Exception:
                        failure = True
                else:
                    try:
                        importlib.import_module(kurt_plugin)
                    except ImportError:
                        failure = True
                if failure:
                    print('Could not load Kurt plugin: {}'.format(kurt_plugin))

        # Initialization Data
        self._cache = None
        self.plugins = []
        self.extensions = [x.extension for x in
                           kurt.plugin.Kurt.plugins.values()]

    def initialize_cache(self, filename=DEFAULT_CACHE_PATH):
        """Initialize and load the cache of parsed Hairball files.

        Attempts to create the cache directory if it does not exist.

        """
        cache_dir = os.path.dirname(filename)
        if not os.path.isdir(cache_dir):
            try:
                os.makedirs(cache_dir)
            except:
                return  # No cache support
        if os.path.isfile(filename):
            with open(filename) as fp:
                try:
                    self._cache = cPickle.load(fp)
                except Exception:
                    self._cache = {}
        else:
            self._cache = {}
        self._initial_cache_size = len(self._cache)

    def finalize(self):
        """Indicate that analysis is complete.

        Calling finalize  will call the finalize method of all plugins thus
        allowing them to output any aggregate results or perform any clean-up.

        """
        for plugin in self.plugins:
            plugin.finalize()

    def initialize_plugins(self):
        """Attempt to Load and initialize all the plugins.

        Any issues loading plugins will be output to stderr.

        """
        for plugin_name in self.options.plugin:
            parts = plugin_name.split('.')
            if len(parts) > 1:
                module_name = '.'.join(parts[:-1])
                class_name = parts[-1]
            else:
                # Use the titlecase format of the module name as the class name
                module_name = parts[0]
                class_name = parts[0].title()

            # First try to load plugins from the passed in plugins_dir and then
            # from the hairball.plugins package.
            plugin = None
            for package in (None, 'hairball.plugins'):
                if package:
                    module_name = '{}.{}'.format(package, module_name)
                try:
                    module = __import__(module_name, fromlist=[class_name])
                    # Initializes the plugin by calling its constructor
                    plugin = getattr(module, class_name)()

                    # Verify plugin is of the correct class
                    if not isinstance(plugin, HairballPlugin):
                        sys.stderr.write('Invalid type for plugin {}: {}\n'
                                         .format(plugin_name, type(plugin)))
                        plugin = None
                    else:
                        break
                except (ImportError, AttributeError):
                    pass
            if plugin:
                self.plugins.append(plugin)
            else:
                sys.stderr.write('Cannot find plugin {}\n'.format(plugin_name))
        if not self.plugins:
            sys.stderr.write('No plugins loaded. Goodbye!\n')
            sys.exit(1)

    def process(self):
        """Start the analysis."""
        def add_file(filename):
            return os.path.splitext(filename)[1] in self.extensions

        hairball_files = []
        while self.args:
            arg_path = self.args.pop()
            if os.path.isdir(arg_path):
                tmp_files = []
                for path, _, files in os.walk(arg_path):
                    for filename in files:
                        if add_file(filename):
                            tmp_files.append(os.path.join(path, filename))
                if not tmp_files:
                    print('No files found in {}'.format(arg_path))
                hairball_files.extend(tmp_files)
            elif add_file(arg_path):
                hairball_files.append(arg_path)
            else:
                print('Invalid file {}'.format(arg_path))
                print('Did you forget to load a Kurt plugin (-k)?')

        # Run all the plugins on a single file at a time so we only have to
        # open the file once.
        for filename in sorted(hairball_files):
            print(filename)
            hash = None
            if self._cache is not None:
                with open(filename) as fp:
                    hash = sha1(fp.read()).hexdigest()
            if hash in self._cache:
                scratch = self._cache[hash]
            else:
                scratch = kurt.Project.load(filename)
                if hash:
                    self._cache[hash] = scratch
            for plugin in self.plugins:
                plugin._process(scratch)  # pylint: disable-msg=W0212
# @Hairball.save_cache doesn't work within the class, so decorate now.
Hairball.process = Hairball.save_cache(Hairball.process)


def main():
    """The entrypoint for the hairball command installed via setup.py."""
    hairball = Hairball(sys.argv[1:])
    hairball.initialize_cache()
    hairball.initialize_plugins()
    hairball.process()
    hairball.finalize()
