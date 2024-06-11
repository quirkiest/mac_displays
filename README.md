# mac_displays
Python script to use Displayplacer &amp; Wallpaper apps to organise Mac monitors 

Displayplacer:  https://github.com/jakehilborn/displayplacer
Wallpaper:      https://github.com/sindresorhus/macos-wallpaper

This is a Pythin script to automate "normalisation" of my Mac monitors.  I have 2 external monitors attached to an M1 Macbook via a StarTech dock. 
My Mac are constantly getting confused about position and wallpaper settings, whenever I restart, disconnect or even sleep the Mac.

Displayplacer(DP) is an excellent CLI that resolves this.  Wallpaper does the same thing for desktop wallpapers, although it uses contextual IDs (that is, ID like 0,1,2 which are assigned in the ortdee that the Maxc detects the displays).

The problem with DP is that my Mac (and many others) swaps contextual IDs all the time, and constantly generates new "persistent" IDs as well.  This script uses the serial # to identify the monitors ... so far this does seem to be persistent.  The other alternative would be to use the resolution or description - or a hashed combo of these (which the script could do prertty easily).  That would, however, still be an issue with identical monitors.

So the script checks the "displayplacer list" output and loads the results into a list of dictionaries.  While it does this it also checks the contextual ID (i.e. the list index) of each monitor so that I can bind the wallpaper to the correct one.
