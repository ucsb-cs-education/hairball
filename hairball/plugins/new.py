from . import PluginController, PluginView


# NOTE: The views must be defined before the controllers


class SpriteImagesView(PluginView):
    def view(self, data):
        for name, image_path in data['sprites']:
            thumbnail = self.get_image_html(image_path)
        return '<div>{0} {1}</div>'.format(name, thumbnail)


class SpriteImages(PluginController):
    """The Sprite Images

    Shows the first costume of each sprite in a scratch file.
    """
    @SpriteImagesView
    def analyze(self, scratch):
        sprites = [('Stage', self.save_png(scratch.stage.images[0], 'stage'))]
        for sprite in scratch.stage.sprites:
            image_path = self.save_png(sprite.images[0], sprite.name)
            sprites.append((sprite.name, image_path))
        return self.view_data(sprites=sprites)
