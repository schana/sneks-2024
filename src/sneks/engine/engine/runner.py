from typing import List, Optional

from sneks.engine.config.instantiation import config
from sneks.engine.engine.mover import NormalizedScore
from sneks.engine.engine.state import State


def demo() -> None:
    config.graphics.display = True
    # config.game.rows = 360
    # config.game.columns = 540
    # config.graphics.cell_size = 2
    config.graphics.step_delay = 0
    config.runs = 100
    config.turn_limit = 10000
    config.registrar_submission_sneks = 100

    main()


def main() -> Optional[List[NormalizedScore]]:
    # import cProfile
    # import pstats
    #
    # pr = cProfile.Profile()
    # pr.enable()

    return main2()

    # pr.disable()
    # stats = pstats.Stats(pr)
    # stats.sort_stats("tottime").print_stats(20)


def main2() -> Optional[List[NormalizedScore]]:
    runs = 0
    state = State()
    state.reset()
    if config.graphics.display:
        from sneks.engine.gui.graphics import Painter
        from sneks.engine.gui.recorder import Recorder

        recorder = None
        if config.graphics.record:
            recorder = Recorder()
        painter = Painter(recorder=recorder)
        painter.initialize()
        while runs < config.runs:
            painter.clear()
            painter.draw_boarders()
            for snake in state.active_snakes:
                painter.draw_snake(snake.head, snake.body, True, snake.color)
            for snake in state.ended_snakes:
                painter.draw_snake(snake.head, snake.body, False, snake.color)
            for snake in state.ended_snakes:
                painter.draw_ended_head(snake.head)
            painter.draw()
            if state.should_continue(config.turn_limit):
                state.step()
            else:
                print(f"Run complete: {runs}")
                if recorder is not None:
                    recorder.animate_game()
                    recorder.reset()
                normalized = state.report()
                for s in normalized:
                    print(f"{s.total():.4f} {s}")
                painter.end_delay()
                runs += 1
                state.reset()
        return None
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
