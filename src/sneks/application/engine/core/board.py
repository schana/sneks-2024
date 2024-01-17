"""
This holds the current game state. The board is in a grid shape with 0-based
row and column indices represented by cells:


.. list-table::

    * - (0, 0)
      - (0, 1)
      - (0, 2)
      - ...
      - (0, COLUMNS - 1)
    * - (1, 0)
      - (1, 1)
      - (1, 2)
      - ...
      - (1, COLUMNS - 1)
    * -
      -
      -
      - ...
      -
    * - (ROWS - 1, 0)
      - (ROWS - 1, 1)
      - (ROWS - 2, 2)
      - ...
      - (ROWS - 1, COLUMNS - 1)
"""

from sneks.application.engine.config.config import config

#: Rows in the game board
ROWS = config.game.rows
#: Columns in the game board
COLUMNS = config.game.columns
