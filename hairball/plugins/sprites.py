from . import PluginController, PluginView, PluginWrapper


class SpriteCountView(PluginView):
    def view(self, data):
        return '<p>{0}</p>'.format(data['count'])


class SpriteCount(PluginController):
    """The Sprite Count

    Outputs the number of sprites in a scratch file.
    """
    @PluginWrapper(html=SpriteCountView)
    def analyze(self, scratch):
        count = len(scratch.stage.sprites)
        return self.view_data(count=count)


class SpriteImagesView(PluginView):
    def view(self, data):
        images = self.get_image_html(data['_thumbnail'])
        for (name, image_paths) in data['sprites'].items():
            images += '<p>{0}</p> <br />'.format(name)
            for image_path in image_paths:
                images += self.get_image_html(image_path)
        return images


class SpriteImages(PluginController):
    """The Sprite Images

    Shows the first costume of each sprite in a scratch file.
    """
    def get_costumes(self, sprite):
        images = []
        for image in sprite.images:
            images.append(self.save_png(image, image.name, sprite.name))
        return images

    @PluginWrapper(html=SpriteImagesView)
    def analyze(self, scratch):
        images = dict()
        for sprite in scratch.stage.sprites:
            images[sprite.name] = self.get_costumes(sprite)
        images["stage"] = self.get_costumes(scratch.stage)
        return self.view_data(sprites=images)
