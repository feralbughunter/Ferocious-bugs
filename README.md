# Ferocious-bugs
Repository of bug reports for Ferocious.  
https://store.steampowered.com/app/1645630/FEROCIOUS/  
<img src="dino.jpg" alt="Cute Daemonosaurus" width="500">

## Usage
To regenerate the website use the `./generate_bug_report.py` script.  

## Website
https://feralbughunter.github.io/Ferocious-bugs/ 

## Bug reports
TXT and yaml format available.

### Adding a bug
Copy one existing bug and change values in the `bug_info.txt` and `bug_info.yaml` file, add screenshots.
Make sure you are using a new number.  
Add the new bug to the appropriate folder.  

### Bug Types
* Item placement - Item incorrectly placed in the world.
* Collision missing - Incorrect collision between an object an the player.
* Level escape - A way to escape behind the playable map.
* Broken model - World object with broken physics, joints, sound...
* Interaction issue - A problem with using an object.
* Player confusion - A problem that mystifies the player.
* Invisible wall - An invisible wall blocking the player.
* Game breaking - Major issue leading making it impossible to continue the game or accessing an important objective.
* Broken logic - Events happening out of order or not at all.

### Severity
Summarizes how much the bug breaks the game, breaks immersion or how visible it is.  

Options:  
* High
* Medium
* Low

### Bug Status
* fixed - Bug has been fixed in a newer version
* unfixed - Bug has not been resolved yet
* notabug - Reported issue is not considered a bug

 
