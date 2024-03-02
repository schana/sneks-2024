from sneks.engine.gui import graphics, recorder


def main():
    """
    Draws the game board with nothing on it and saves the image

    :return:
    """
    painter = graphics.Painter(recorder.Recorder())
    painter.initialize()
    painter.clear()
    painter.draw_boarders()
    painter.draw()
