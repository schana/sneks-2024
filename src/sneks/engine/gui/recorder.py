import os
import pathlib
import uuid

try:
    import pygame.image
    from pygame import Surface
except ModuleNotFoundError:
    pygame = object()  # type: ignore

from sneks.engine.config.instantiation import config


class Recorder:
    def __init__(self):
        self.identifier = uuid.uuid4()
        self.i = 0
        self.prefix = pathlib.Path(config.graphics.record_prefix)
        self.prefix.mkdir(exist_ok=True)
        (self.prefix / "pics").mkdir(exist_ok=True)
        (self.prefix / "movies").mkdir(exist_ok=True)

    def reset(self):
        self.identifier = uuid.uuid4()
        self.i = 0

    def record_frame(self, screen: Surface):
        pygame.image.save(
            screen,
            str(self.prefix / "pics" / f"pic_{self.identifier}_{self.i:04d}.png"),
        )
        self.i += 1

    def animate_game(self):
        import moviepy.video.io.ImageSequenceClip  # type: ignore

        images = sorted(
            [str(i) for i in self.prefix.glob(f"pics/pic_{self.identifier}_*.png")]
        )

        clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(images, fps=24)
        clip.write_videofile(
            str(self.prefix / "movies" / f"game_{self.identifier}.mp4")
        )

        for image in images:
            os.remove(image)
