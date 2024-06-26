# mac_displays
Python script to use Displayplacer &amp; Wallpaper apps to organise Mac monitors 

Displayplacer:  https://github.com/jakehilborn/displayplacer

Wallpaper:      https://github.com/sindresorhus/macos-wallpaper

mac_displays.py is a Python script to automate "normalisation" of my Mac monitors.  I have 2 external monitors attached to an M1 Macbook via a StarTech dock. 
My Mac are constantly getting confused about position and wallpaper settings, whenever I restart, disconnect or even sleep the Mac.

Displayplacer(DP) is an excellent CLI that resolves this.  Wallpaper does the same thing for desktop wallpapers, although it uses contextual IDs (that is, ID like 0,1,2 which are assigned in the order that the Maxc detects the displays).

The problem with DP is that my Mac (and many others) swaps contextual IDs all the time, and constantly generates new "persistent" IDs as well.  This script uses the serial # to identify the monitors ... so far this does seem to be persistent.  The other alternative would be to use the resolution or description - or a hashed combo of these (which the script could do prertty easily).  That would, however, still be an issue with identical monitors.

So the script checks the "displayplacer list" output and loads the results into a list of dictionaries.  While it does this it also checks the contextual ID (i.e. the list index) of each monitor so that I can bind the wallpaper to the correct one.

The script puts monitors in this config:

<img width="383" alt="image" src="https://github.com/quirkiest/mac_displays/assets/37827013/ca98c5a4-2e1c-4c1f-af2e-bee7bd0c175b">

But you can change to whatever you like.

Script will default to looking for a file called "mac_displays_params.json" if no filepath is provided as an argument.

## mac_displays_params.json: ##
```json
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
        "Description" : "LG UltraFine",
        "Serial screen id" : "xxx321",
        "Wallpaper" : "/Users/username/Pictures/Dynamic Wallpapers/Fuji.heic"
    },
    "philips":{
        "id":2,
        "Description" : "Philips 328B",
        "Serial screen id" : "xxx456",
        "Wallpaper" : "/Users/username/Pictures/Dynamic Wallpapers/Trek.heic"
    }
    }
```

| parameter  | meaning | mandatory? |
| ------------- | ------------- | :-------------: |
| name | friendly name for the screen object.  Note that "apple" is mandatory | ✅ |
| id  | this is default contextual id, replaced by the script.  | |
| Description | Description of the monitor.  Not mandatory. | |
| Serial screen id  | Serial number of the display (from Displayplacer output)  | ✅ |
| Wallpaper | Path to wallpaper file | |
| Width | Only for default display, replaced by the script | |
