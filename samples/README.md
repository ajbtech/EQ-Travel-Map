# Sample log

`sample_eqlog_Gorrek_P1999Green.txt` is real Project 1999 gameplay from the
maintainer's character "Gorrek", included with permission. The log was trimmed
from a much larger archive to keep the repo small: only the lines the parser
actually consumes (zones, kills, deaths, levels, logins, looted/merchant cash)
were retained. Combat damage, chat, and other log noise were stripped.

The file ships with the app so first-time users — and CI — can generate a map
without needing their own EverQuest log files.

To try it from the desktop app, point the log folder at `samples/` and use
character name `Gorrek`. From the command line:

```powershell
python src\eq_parser.py Gorrek --log-folder samples
```
