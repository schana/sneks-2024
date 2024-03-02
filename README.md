# Sneks on a Toroidal Plane

Build the behavior for your Snek and upload it at [sneks.dev/submit](https://www.sneks.dev/submit) to see how
it does against other submitters. See the website for [live results](https://www.sneks.dev) and details regarding
scoring and submission help.

## Getting started

### Prerequisites

1. Install Python >=3.12 from [python.org/downloads](https://www.python.org/downloads/)
   1. Add Python to your Path to make things easier
2. _(Optional)_ Install an IDE to work in
   1. [PyCharm Community Edition](https://www.jetbrains.com/pycharm/download)
   2. [Visual Studio Code](https://code.visualstudio.com/)
3. Download `template.zip` to your local machine
   from [sneks.dev/template/template.zip](https://www.sneks.dev/template/template.zip) and extract its contents.

### Set up development environment

1. Open a terminal or command prompt
2. Change to the directory where the template is located. After unzipping, it should be the directory called
   `toroidal-sneks-submission-main`.
   1. You should be located in the same directory as `pyproject.toml`
3. _(Optional, but recommended)_ Set up a virtual environment
   1. Create virtual environment
      ```
      python -m venv venv
      ```
   2. Activate the environment
      1. macOS / Linux
         ```
         source venv/bin/activate
         ```
      2. Windows
         ```
         venv\Scripts\activate
         ```
         1. If you get an error saying your execution policy prevents the running of the activate script,
            you can disable that policy temporarily with `Set-ExecutionPolicy Unrestricted -Scope Process`.
4. Install this package to enable testing locally
   ```
   pip install --editable .
   ```
5. Ensure everything works by trying out the helper scripts
   1. Test that the current snake passes validation
      ```
      validate
      ```
   2. Run the current snake by itself
      ```
      run
      ```

### Develop your Snek

In `src/submission/snek/submission.py`, modify the logic of `get_next_direction()`
to control your Snek's behavior. See [sneks.dev/docs](https://www.sneks.dev/docs/index.html) for documentation of
the classes and helper functions available to help refine your Snek. There are also a couple example Sneks
in `src/examples` that can be used as starting points.

#### Configuration

In `src/scripts/config.py`, there are some values that can be changed to tune how the game performs locally. Each step
in the game has a delay afterwards, defaulting to 40ms. Likewise, after the end of a run, the game pauses for a default
of one second. These can be changed to your liking, with the added option of requiring a keypress to advance the snake.
With either `WAIT_FOR_KEYPRESS` option set to `True`, the snake will not move unless a key is pressed. Holding down a
key will continuously advance the snake.

### Updating the submission template dependencies

If directed by your contest coordinator, you can use the following command to update the submission template
dependencies to the latest version:

```
pip install --upgrade --upgrade-strategy eager --editable .
```