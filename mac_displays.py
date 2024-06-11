#!/usr/bin/env python

# Displayplacer
# https://github.com/jakehilborn/displayplacer

# macos-wallpaper
# https://github.com/sindresorhus/macos-wallpaper

# Note: both installed via HomeBbrew

import json
import sys
import os

# Determine the path to the script to construct the default params file path
script_dir = os.path.dirname(os.path.abspath(__file__))
default_params_path = os.path.join(script_dir, "mac_displays_params.json")

# Use the first command line argument as the params file path if provided, else use the default
params_file_path = sys.argv[1] if len(sys.argv) > 1 else default_params_path

# Load params from the specified JSON file
with open(params_file_path, 'r') as file:
    params = json.load(file)
    

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

for screen in screen_info:
    screen["Width"], screen["Height"] = getres(screen["Resolution"])
    if screen["Serial screen id"] == params["apple"]["Serial screen id"]:
        params['apple']['Width'] = screen["Width"]

apple_wallpaper_id = 0
LG_monitor_id = 1
philips_monitor_id = 2

displayplacer_command = "displayplacer "

for i,val in enumerate(screen_info):
    id = val["Serial screen id"]
    if id == params['apple']['Serial screen id']: 
        params['apple']['id'] = i
        origin = f"origin:(0,0)"
    elif id == params["lg"]["Serial screen id"]:
        params['lg']['id'] = i
        origin = f"origin:({int(params['apple']['Width']/2)},-{val['Height']})"
    elif id == params['philips']['Serial screen id']:
        params['philips']['id'] = i
        origin = f"origin:(-{int(val['Width']-int(params['apple']['Width'])/2)},-{val['Height']})"
    displayplacer_command += f' \"id:{val.get("Persistent screen id")} res:{val.get("Resolution")} hz:{val.get("Hertz","8")} color_depth:{val.get("Color Depth")} enabled:true scaling:{val.get("Scaling","off")} {origin} degree:0\"'

"""
displayplacer 
"id:37D8832A-2D66-02CA-B9F7-8F30A301B230 res:1728x1117 hz:120 color_depth:8 enabled:true scaling:on origin:(0,0) degree:0" "id:768F61BA-BCF8-41EC-B2BC-3F20ED8D936E res:3440x1440 hz:60 color_depth:8 enabled:true scaling:off origin:(864,-1440) degree:0" "id:ACCC194E-6907-46F1-B364-B27BF313D122 res:3008x1692 hz:60 color_depth:8 enabled:true scaling:off origin:(-2144,-1692) degree:0"
"""

# print(displayplacer_command)

stream = os.popen(displayplacer_command)

# Store wallpaper commands in a list
wallpaper_commands = [
    f'wallpaper set "{params["apple"]["Wallpaper"]}" --screen {params["apple"]["id"]}',
    f'wallpaper set "{params["philips"]["Wallpaper"]}" --screen {params["philips"]["id"]}',
    f'wallpaper set "{params["lg"]["Wallpaper"]}" --screen {params["lg"]["id"]}'
]
# Execute each wallpaper command
for cmd in wallpaper_commands:
    os.system(cmd)
# Apple_wallpaper = os.popen(f'wallpaper set "/Users/wazza/Pictures/Dynamic Wallpapers/earth.heic" --screen {apple_wallpaper_id}')
# Philips_wallpaper = os.popen(f'wallpaper set "/Users/wazza/Pictures/Dynamic Wallpapers/Star Trek Strange New Worlds V4.heic" --screen {philips_monitor_id}')
# LG_wallpaper = os.popen(f'wallpaper set "/Users/wazza/Pictures/Dynamic Wallpapers/Fuji.heic" --screen {LG_monitor_id}')


