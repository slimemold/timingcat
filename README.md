# SexyThyme - Time trial frontend for ontheday.net

## Prerequisites
python3
peewee - ORM
sqlite - database backend

## TODO
- Implement bikereg import in GUI.
- Finish field table proxy model to show finishers and total.
- Fix field-specific racer tables to actually filter by field.
- Add "commit" and "delete" buttons to result table.
- Hook up "commit selected" button.
- Add "delete" buttons to racer table.
- Add "new racer" button to racer table.
- Add "racers" and "delete" buttons to field table.
- Add "new field" button to field table.
- Add reports pdf generation.
- Add result commit hook.
- Implement OnTheDay.net result commit hook.

## Known Bugs
- Clear button on result_input doesn't always erase text. (OS X)
- Get "Empty filename passed to function" when select "Computer" in file
  selector. (OS X)
- Native anyfile file selector does not allow new file. (OS X)
- File selector not keyboard-navigatable. (OS X)
