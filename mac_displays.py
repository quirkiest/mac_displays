#!/usr/bin/env python
from __future__ import print_function
import os
import pprint

# Hoping these are persistent!
APPLE_SERIAL_ID = "s4251086178"
LG_SERIAL_ID = "s16843009"
PHILIPS_SERIAL_ID = "s5929"
APPLE_WIDTH = "1728"
# Define wallpaper paths

wallpapers = {
    "apple": "/Users/wazza/Pictures/Dynamic Wallpapers/earth.heic",
    "philips": "/Users/wazza/Pictures/Dynamic Wallpapers/Star Trek Strange New Worlds V4.heic",
    "lg": "/Users/wazza/Pictures/Dynamic Wallpapers/Fuji.heic"
}

def getres(res):
    return tuple(map(int, res.split('x')))

# def load_screen_info(stream):

#     #sections = stream.split("Persistent screen id: ")[1:]  # Skip the first split before the first id
#     sections = ["Persistent screen id: " + section for section in stream.split("Persistent screen id: ")[1:]]
#     screen_info_list = []
    
#     for section in sections:
#         # Check if "Resolutions for rotation 0:" is in the section and split it off
#         if "Resolutions for rotation 0:" in section:
#             section = section.split("Resolutions for rotation 0:")[0]
        
#         lines = section.strip().split("\n")
#         screen_dict = {}
#         for line in lines:
#             if ": " in line:  # Ensure there's a key-value pair to split
#                 key, value = line.split(": ", 1)  # Split on the first occurrence of ": "
#                 screen_dict[key.strip()] = value.strip()
#                 if key.strip() == "Enabled" and value.strip() == "true":
#                     break  # Stop adding more key-value pairs once "Enabled: true" is encountered
        
#         screen_info_list.append(screen_dict)
    
#     return screen_info_list
def load_screen_info(stream):
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
    if screen["Serial screen id"] == APPLE_SERIAL_ID:
        APPLE_WIDTH = screen["Width"]

apple_wallpaper_id = 0
LG_monitor_id = 1
philips_monitor_id = 2

displayplacer_command = "displayplacer "

for i,val in enumerate(screen_info):
    id = val["Serial screen id"]
    if id == APPLE_SERIAL_ID: 
        apple_wallpaper_id = i
        origin = f"origin:(0,0)"
    elif id == LG_SERIAL_ID:
        LG_monitor_id = i
        origin = f"origin:({int(APPLE_WIDTH/2)},-{val['Height']})"
    elif id == PHILIPS_SERIAL_ID:
        philips_monitor_id = i
        origin = f"origin:(-{int(val['Width']-APPLE_WIDTH/2)},-{val['Height']})"
    displayplacer_command += f' \"id:{val.get("Persistent screen id")} res:{val.get("Resolution")} hz:{val.get("Hertz","8")} color_depth:{val.get("Color Depth")} enabled:true scaling:{val.get("Scaling","off")} {origin} degree:0\"'

"""
displayplacer 
"id:37D8832A-2D66-02CA-B9F7-8F30A301B230 res:1728x1117 hz:120 color_depth:8 enabled:true scaling:on origin:(0,0) degree:0" "id:768F61BA-BCF8-41EC-B2BC-3F20ED8D936E res:3440x1440 hz:60 color_depth:8 enabled:true scaling:off origin:(864,-1440) degree:0" "id:ACCC194E-6907-46F1-B364-B27BF313D122 res:3008x1692 hz:60 color_depth:8 enabled:true scaling:off origin:(-2144,-1692) degree:0"
"""

# print(displayplacer_command)

stream = os.popen(displayplacer_command)



# Store wallpaper commands in a list
wallpaper_commands = [
    f'wallpaper set "{wallpapers["apple"]}" --screen {apple_wallpaper_id}',
    f'wallpaper set "{wallpapers["philips"]}" --screen {philips_monitor_id}',
    f'wallpaper set "{wallpapers["lg"]}" --screen {LG_monitor_id}'
]
# Execute each wallpaper command
for cmd in wallpaper_commands:
    os.system(cmd)
# Apple_wallpaper = os.popen(f'wallpaper set "/Users/wazza/Pictures/Dynamic Wallpapers/earth.heic" --screen {apple_wallpaper_id}')
# Philips_wallpaper = os.popen(f'wallpaper set "/Users/wazza/Pictures/Dynamic Wallpapers/Star Trek Strange New Worlds V4.heic" --screen {philips_monitor_id}')
# LG_wallpaper = os.popen(f'wallpaper set "/Users/wazza/Pictures/Dynamic Wallpapers/Fuji.heic" --screen {LG_monitor_id}')


