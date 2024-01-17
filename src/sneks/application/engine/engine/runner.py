from typing import List, Optional

from sneks.application.engine.config.config import config
from sneks.application.engine.engine.mover import NormalizedScore
from sneks.application.engine.engine.state import State


def main() -> Optional[List[NormalizedScore]]:
    runs = 0
    state = State()
    state.reset()
    if config.graphics.display:
        from sneks.gui.graphics import Painter
        from sneks.gui.recorder import Recorder

        recorder = Recorder() if config.graphics.record else None
        painter = Painter(recorder=recorder)
        painter.initialize()
        while runs < config.runs:
            painter.clear()
            painter.draw_boarders()
            for snake in state.active_snakes:
                painter.draw_snake(snake.cells, True, snake.color)
            for snake in state.ended_snakes:
                painter.draw_snake(snake.cells, False, snake.color)
            for food in state.food:
                painter.draw_food(food)
            painter.draw()
            if state.should_continue(config.turn_limit):
                state.step()
            else:
                print(f"Run complete: {runs}")
                if config.graphics.record:
                    recorder.animate_game()
                    recorder.reset()
                normalized = state.report()
                for s in normalized:
                    print(f"{s.total():.4f} {s}")
                painter.end_delay()
                runs += 1
                state.reset()
    else:
        scores = []
        while runs < config.runs:
            if state.should_continue(config.turn_limit):
                state.step()
            else:
                scores += state.report()
                state.reset()
                runs += 1
                if runs % (config.runs / 20) == 0:
                    print("{}% complete".format(100 * runs / config.runs))
        return scores


if __name__ == "__main__":
    main()
