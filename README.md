# SexyThyme - Time trial timing software with OnTheDay.net integration

# Version History
1.0.2
- Add cheat sheet (help window showing keyboard shortcuts).
- Reduce NTP clock check noisiness false positives.
- Add multi-client support.
        
1.0.1
- Bug fixes, ontheday.net remote robustness fixes.
- Used for Race to the Observatory 2019.

1.0.0
- Initial release, used for SBHC 2019.

# Prerequisites

## For Running
keyring
ntplib
PyQt5
requests

## For Linting
pyenchant
pylint

## For regenerating requirements.txt
pipreqs

## TODO
- Implement 12-hour time.

## Known Bugs
- Clear button on result_input doesn't always erase text. (OS X)
- Get "Empty filename passed to function" when select "Computer" in file
  selector. (OS X)
- Native anyfile file selector does not allow new file. (OS X)
- File selector not keyboard-navigatable. (OS X)
- You can violate SQL table field uniqueness by editing the table view directly.
  Doing so puts the table view in this weird state where you can't edit anything
  else, until you go back to that cell and fix it. Obviously, the uniqueness
  violation doesn't get written to the database. The main issue is that there
  is no visual indication of anything going wrong other than the fact that
  the table becomes uneditable (until you edit the offending cell).
- Pressing "Today" on the clock tab of the race builder does not update the
  edit box, although the calendar popup is updated.
