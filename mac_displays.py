#!/usr/bin/env python

# Displayplacer
# https://github.com/jakehilborn/displayplacer

# macos-wallpaper
# https://github.com/sindresorhus/macos-wallpaper

# Note: both installed via HomeBbrew

import json
import sys
import os
import pprint # only used for debugging

# Determine the path to the script to construct the default params file path
script_dir = os.path.dirname(os.path.abspath(__file__))
default_params_path = os.path.join(script_dir, "mac_displays_params.json")

# Use the first command line argument as the params file path if provided, else use the default
params_file_path = sys.argv[1] if len(sys.argv) > 1 else default_params_path

# Load params from the specified JSON file
with open(params_file_path, 'r') as file:
    json_params = json.load(file)

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


def do_origin(param, width, height):
    pos = param.get("position","home").lower()
    if pos == "home":
        return "(0,0)"
    elif pos == "topright":
        return f"({int(json_params['apple']['Width']/2)},-{height})"
    elif pos == "topleft":
        return f"(-{int(width-int(json_params['apple']['Width'])/2)},-{height})"
    elif pos == "midleft":
        return f"(-{int(width)},-{int(height/2)})"
    elif pos == "topmid":
        print(f"{int((width-json_params['apple']['Width'])/2)*-1},-{height}")
        return f"({int((width-json_params['apple']['Width'])/2)*-1},-{height})"
    else:
        return "(0,0)"
    
# Open the displayplacer list command and read the output
output = os.popen('displayplacer list').read()
displayplacer_screen_info = load_screen_info(output)
# pprint.pprint(screen_info)

# def get_unique_id(screen):
#     serial_id = screen.get("Serial screen id", "")
#     persistent_id = screen.get("Persistent screen id", "")
#     return f"{serial_id}_{persistent_id}"

# Get Width & Height from displayplacer_screen_info string
# for screen in displayplacer_screen_info:
#     screen["Width"], screen["Height"] = getres(screen["Resolution"])
    # special case for the apple screen (because we know what its resolution is)
    # inserts detected width into the apple screen params
    # if screen.get("Type") == "MacBook built in screen":
    #     pprint.pprint(screen)
    #     json_params['apple']['Width'] = int(screen.get("Width", 1728))

displayplacer_command = "displayplacer "
wallpapers = []

def count_matching_values(dict1, dict2):
    """Count the number of matching values between two dictionaries and return the count and matching keys."""
    matched_keys = [key for key in dict1 if key in dict2 and dict1[key] == dict2[key]]
    return len(matched_keys), matched_keys

for i, dp_val in enumerate(displayplacer_screen_info):
    # screen_unique_id = get_unique_id(val)
    params_dict = {key: value for key, value in json_params.items()}
    
    # Find the best match
    best_match = None
    matchlist = None
    max_matches = -1
    for screen_id, screen_params in params_dict.items():
        matches, matched_keys = count_matching_values(dp_val, screen_params)
        if matches > max_matches:
            max_matches = matches
            best_match = screen_params
            matchlist = matched_keys
    
    if best_match:
        # print(f"{val['Type']} => {best_match['Description']} : {matchlist}")
        dp_val["Width"], dp_val["Height"] = getres(dp_val["Resolution"])
        if best_match.get("Resolution"):
            best_match["Width"], best_match["Height"] = getres(best_match["Resolution"])
        else:
            best_match["Width"] = dp_val["Width"]
            best_match["Height"] = dp_val["Height"]
        best_match["id"] = i
        best_match["origin"] = do_origin(best_match, best_match["Width"], best_match["Height"])
        displayplacer_command += f' \"id:{best_match["Serial screen id"]} res:{best_match.get("Resolution") or dp_val.get("Resolution") or ""} enabled:true scaling:{best_match.get("Scaling") or dp_val.get("Scaling", "off") or ""} origin:{best_match["origin"]} degree:0\"'
        wallpapers.append(f'wallpaper set "{best_match["Wallpaper"]}" --screen {i}')
# print (displayplacer_command)
#displayplacer_command = 'displayplacer "id:s4251086178 res:1728x1117 enabled:true scaling:on origin:(0,0) degree:0" "id:s5929 res:3008x1692 enabled:true scaling:on origin:(-2144,-1692) degree:0" "id:s16843009 res:3440x1440 enabled:true scaling:off origin:(864,-1440) degree:0"'

#displayplacer "id:37D8832A-2D66-02CA-B9F7-8F30A301B230 res:1728x1117 hz:120 color_depth:8 enabled:true scaling:on origin:(0,0) degree:0" "id:E075EA1B-045E-4B2E-94A5-53E3EEF9B75D res:1920x1080 hz:60 color_depth:8 enabled:true scaling:off origin:(-1920,-540) degree:0"

stream = os.popen(displayplacer_command)

for wallpaper in wallpapers:
    #print(wallpaper)
    os.popen(wallpaper)

