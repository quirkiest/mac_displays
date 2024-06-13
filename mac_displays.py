#!/usr/bin/env python
###########################
#        CREDITS          #
###########################

__author__      = "Warwick Matthews"
__copyright__   = "Copyright 2024, Warwick Matthews"
__credits__     = ["Warwick Matthews"]
__license__     = "MIT"
__version__     = "0.9"
__updatedate__  = "2024-06-13"
__maintainer__  = "Warwick Matthews"
__email__       = "python@quirkiest.com"
__status__      = "active development"

# MIT License

# Copyright (c) 2024 Warwick Matthews

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

###########################
#       REFERENCES        #
###########################
# Displayplacer
# https://github.com/jakehilborn/displayplacer

# macos-wallpaper
# https://github.com/sindresorhus/macos-wallpaper

# Note: both installed via HomeBbrew

###########################
#         IMPORTS         #
###########################
import json
import sys
import os
import pprint # only used for debugging

###########################
#        FUNCTIONS        #
###########################
def getres(res):
    """
    Converts a resolution string in the format 'widthxheight' into a tuple of integers (width, height).

    Parameters:
    - res (str): A string representing the resolution, formatted as 'widthxheight'.

    Returns:
    - tuple: A tuple of two integers, representing the width and height of the resolution.
    """
    return tuple(map(int, res.split('x')))
    
def load_screen_info(stream):

    """
    Parses the output from `displayplacer list` command to extract screen information.

    The function splits the input stream by "Persistent screen id: " to identify each screen section,
    then further processes each section to extract key-value pairs of screen attributes.
    It ignores lines without a colon separator to filter out irrelevant information.
    The result is a list of dictionaries, each representing a screen's attributes.

    Parameters:
    - stream (str): The output string from `displayplacer list` command.

    Returns:
    - list: A list of dictionaries, where each dictionary contains the attributes of a screen.
    """
    
    sections = ["Persistent screen id: " + section for section in stream.split("Persistent screen id: ")[1:]]
    return [
        {key.strip(): value.strip() for key, value in 
         (line.split(": ", 1) for line in section.split("Resolutions for rotation 0:")[0].strip().split("\n") if ": " in line)}
        for section in sections
    ]

def do_origin(screen_param, width, height):
    width = int(width)
    height = int(height)
    applewidth = int(params['apple']['Width']) # note this is from global params
    pos = screen_param.get("position", "home").lower()
    positions = {
        "home": "(0,0)",
        "topright": f"({int(applewidth/2)},-{height})",
        "topleft": f"(-{int(width-applewidth/2)},-{height})",
        "midleft": f"(-{width},-{int(height/2)})",
        "midright": f"({applewidth},-{int(height/2)})",
        "left": f"(-{width},0)",
        "right": f"({applewidth},0)",
        "above": f"(0,-{height})",
        "below": f"(0,{height})",
    }
    return positions.get(pos, "(0,0)")

# Determine the path to the script to construct the default params file path
script_dir = os.path.dirname(os.path.abspath(__file__))
default_params_path = os.path.join(script_dir, "mac_displays_params.json")

# Use the first command line argument as the params file path if provided, else use the default
params_file_path = sys.argv[1] if len(sys.argv) > 1 else default_params_path

# Load params from the specified JSON file
with open(params_file_path, 'r') as file:
    params = json.load(file)

output = os.popen('displayplacer list').read()
screen_info = load_screen_info(output)
#pprint.pprint(screen_info)

for screen in screen_info:
    screen["Width"], screen["Height"] = getres(screen["Resolution"])
    # if screen["Serial screen id"] == params.get("apple",{}).get("Serial screen id"):
    #     params['apple']['Width'] = int(screen.get("Width",1728))

# this gets the width of the first screen in the list (which is always apple mactop built-in monitor).
# This is needed for relative positioning of the other screens.
# We set it as "apple" width, which will usually exist in params, or get created if not.
params['apple']['Width'] = screen_info[0].get("Width",1728)

displayplacer_command = "displayplacer "
wallpapers = []
for i,val in enumerate(screen_info):
    screen_serial_id = val.get("Serial screen id")
    params_dict = {screen["Serial screen id"]: screen for screen in params.values()}
    params_serial_id = params_dict.get(screen_serial_id)
    
    params_serial_id["Width"], params_serial_id["Height"] = getres(params_serial_id["Resolution"]) if params_serial_id.get("Resolution") else (val["Width"], val["Height"])
    if params_serial_id:
        #params_serial_id["id"] = i
        params_serial_id["origin"] = do_origin(params_serial_id, params_serial_id["Width"], params_serial_id["Height"])
        displayplacer_command += f' \"id:{params_serial_id["Serial screen id"]} res:{params_serial_id.get("Resolution") or val.get("Resolution") or ""} enabled:true scaling:{params_serial_id.get("Scaling") or val.get("Scaling","off") or ""} origin:{params_serial_id["origin"]} degree:0\"'
        wallpaper_path = params_serial_id.get("Wallpaper", {})
        if wallpaper_path:
            wallpapers.append(f'wallpaper set "{wallpaper_path}" --screen {i}')

# print (displayplacer_command)
#displayplacer_command = 'displayplacer "id:s4251086178 res:1728x1117 enabled:true scaling:on origin:(0,0) degree:0" "id:s5929 res:3008x1692 enabled:true scaling:on origin:(-2144,-1692) degree:0" "id:s16843009 res:3440x1440 enabled:true scaling:off origin:(864,-1440) degree:0"'

stream = os.popen(displayplacer_command)

for wallpaper in wallpapers:
    os.popen(wallpaper)

