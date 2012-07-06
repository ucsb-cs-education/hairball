from . import PluginController, PluginView


class FileHistoryView(PluginView):
    def view(self, data):
        return '<pre>{0}</pre'.format(data['history'])


class FileHistory(PluginController):
    """The File History

    Shows the history of the Scratch file.
    """
    @PluginWrapper(html=FileHistoryView)
    def analyze(self, scratch):
        return self.view_data(history=scratch.info['history'])
