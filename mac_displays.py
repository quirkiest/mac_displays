#!/usr/bin/env python

# Displayplacer
# https://github.com/jakehilborn/displayplacer

# macos-wallpaper
# https://github.com/sindresorhus/macos-wallpaper

# Note: both installed via HomeBbrew

import json
import sys
import os
#import pprint # only used for debugging

# Determine the path to the script to construct the default params file path
script_dir = os.path.dirname(os.path.abspath(__file__))
default_params_path = os.path.join(script_dir, "mac_displays_params.json")

# Use the first command line argument as the params file path if provided, else use the default
params_file_path = sys.argv[1] if len(sys.argv) > 1 else default_params_path

# Load params from the specified JSON file
with open(params_file_path, 'r') as file:
    params = json.load(file)

# ================== mac_displays_params.json ==================
""" 
{
    "apple":{
        "id":0,
        "Description" : "MacBook built in screen",
        "Serial screen id" : "xxx123",
        "Wallpaper" : "/Users/username/Pictures/Dynamic Wallpapers/earth.heic",
        "Width": 1728
    },
    "lg":{
        "id":1,
        "Description" : "LG UltraWide",
        "Serial screen id" : "xxx321",
        "Wallpaper" : "/Users/username/Pictures/Dynamic Wallpapers/Fuji.heic"
    },
    "philips":{
        "id":2,
        "Description" : "Philips 123",
        "Serial screen id" : "xxx456",
        "Wallpaper" : "/Users/username/Pictures/Dynamic Wallpapers/Trek.heic"
    }
    }
"""
def getres(res):
    """
    Converts a resolution string in the format 'widthxheight' into a tuple of integers (width, height).

    Parameters:
    - res (str): A string representing the resolution, formatted as 'widthxheight'.

    Returns:
    - tuple: A tuple of two integers, representing the width and height of the resolution.
    """
    return tuple(map(int, res.split('x')))
    
# return screen_info_list
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
output = os.popen('displayplacer list').read()
screen_info = load_screen_info(output)
#pprint.pprint(screen_info)

# this gets the width of the Macbook built-in screen
# which is needed for relative positioning of the other screens

for screen in screen_info:
    screen["Width"], screen["Height"] = getres(screen["Resolution"])
    if screen["Serial screen id"] == params.get("apple",{}).get("Serial screen id"):
        params['apple']['Width'] = int(screen.get("Width",1728))


displayplacer_command = "displayplacer "
def do_origin(param, width, height):
    pos = param.get("position","home").lower()
    if pos == "home":
        return "origin:(0,0)"
    elif pos == "topright":
        return f"origin:({int(params['apple']['Width']/2)},-{height})"
    elif pos == "topleft":
        return f"origin:(-{int(width-int(params['apple']['Width'])/2)},-{height})"
    else:
        return "origin:(0,0)"
    
for i,val in enumerate(screen_info):
    screen_serial_id = val["Serial screen id"]
    params_dict = {screen["Serial screen id"]: screen for screen in params.values()}
    params_serial_id = params_dict.get(screen_serial_id)
    if params_serial_id:
        params_serial_id["id"] = i
        params_serial_id["origin"] = do_origin(params_serial_id, val["Width"], val["Height"])
        displayplacer_command += f' \"id:{val.get("Persistent screen id")} res:{val.get("Resolution")} hz:{val.get("Hertz","8")} color_depth:{val.get("Color Depth")} enabled:true scaling:{val.get("Scaling","off")} {params_serial_id["origin"]} degree:0\"'

"""
displayplacer 
"id:37D8832A-2D66-02CA-B9F7-8F30A301B230 res:1728x1117 hz:120 color_depth:8 enabled:true scaling:on origin:(0,0) degree:0" "id:768F61BA-BCF8-41EC-B2BC-3F20ED8D936E res:3440x1440 hz:60 color_depth:8 enabled:true scaling:off origin:(864,-1440) degree:0" "id:ACCC194E-6907-46F1-B364-B27BF313D122 res:3008x1692 hz:60 color_depth:8 enabled:true scaling:off origin:(-2144,-1692) degree:0"
"""

stream = os.popen(displayplacer_command)

for screen in params.values():
    os.popen(f'wallpaper set "{screen["Wallpaper"]}" --screen {screen["id"]}')

