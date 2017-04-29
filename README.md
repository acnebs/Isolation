# Isolation

## Info

This program is a Python/wxPython implementation of the 1970s game *Isolation*, originally designed by Bernd Kienitz. [See it on BGG here.](https://boardgamegeek.com/boardgame/1875/isolation)
It was created as a way to learn basic board game building using Python/wxPython. *Isolation* was chosen for its simple rules and my enjoyment of it as a young boy.

This program was entirely written and tested entirely on macOS systems, from OS X 10.6 upward. However, as both Python and wxPython are fairly platform agnostic, and this code does not contain any platform-specific code (to my recollection), it should run fairly well on Windows/other systems. Until April 2017, this program had not been touched since April 2012, five years prior, so it is quite likely that there are some bugs that have cropped up over time, though I have tried my best to eliminate any obvious issues. 

As this software is published under the MIT license, please feel free to modify it/use any code as you see fit.


## Usage

0. Install dependencies:
  * wxPython, last tested using wxPython 3.0.2.0 (classic), available on Homebrew
1. Download all files into same directory (for now, the main isolation.py file and two image assets)
2. `cd` into the directory containing the three files
3. Run `python isolation.py`. Please note that this program is limited to Python2, as wxPython does not yet support Python3.
4. You should be ready to rumble and play a round or two of Isolation