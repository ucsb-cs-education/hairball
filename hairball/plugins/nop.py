from . import PluginController, PluginView, PluginWrapper


class NopView(PluginView):
    def view(self, data):
        return ''


class Nop(PluginController):
    """Nothing Plugin

    This plugin does nothing execept allows for the thumbnail to be generated.
    """

    @PluginWrapper(html=NopView)
    def analyze(self, scratch):
        return self.view_data()
