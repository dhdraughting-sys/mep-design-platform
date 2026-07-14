# MEP Design Platform \u2014 Streamlit version

A simpler, single-process replacement for the earlier FastAPI+htmx
prototype. Same idea (one live-editable Room Schedule instead of
re-selecting rooms across Excel tabs) with none of the CDN-dependency
problems that version ran into.

## Running it (Windows) \u2014 the easy way

**Double-click `run.bat`.**

The first time, it will take a minute or two (it sets up a private Python
environment and installs the packages this app needs). Every time after
that, it starts in a few seconds. Your browser opens automatically.

**For a proper desktop icon** (not just a plain shortcut): run
`create_shortcut.ps1` once \u2014 right-click it \u2192 "Run with PowerShell".
This creates a "MEP Design Platform" icon on your Desktop with a custom
navy/ice-blue snowflake icon (`mep_icon.ico`), pointing at `run.bat`. From
then on, just double-click that desktop icon \u2014 no terminal, no typing.

If right-click \u2192 Run with PowerShell doesn't work, open a terminal in
this folder instead and run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\create_shortcut.ps1
```

Keep the black window that pops up open while you're using the app \u2014
that's the app actually running. Closing that window stops the app.

## Running it manually (if `run.bat` doesn't work, or on Mac/Linux)

```bash
python -m venv venv
venv\Scripts\activate          # Windows; use "source venv/bin/activate" on Mac/Linux
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## What this does

- One editable table: click any cell to edit it, add rooms with the `+`
  at the bottom-left of the table, delete a row by selecting it and
  pressing Delete.
- Heat gains (sensible/latent/total) and FCU auto-selection recalculate
  immediately on every edit \u2014 no separate tab, no manual lookup.
- **Export to Excel** button generates a Room Schedule + HVAC Summary
  workbook from whatever is currently in the table.

## Important limitation: this does NOT persist between runs

Unlike a real database-backed app, this Streamlit version keeps data only
in memory for the current running session. **Closing the black `run.bat`
window (or pressing Ctrl+C in it) loses any changes** that haven't been
exported. Refreshing the browser tab does NOT lose data \u2014 only actually
stopping the app does.

If this becomes something you rely on regularly, the next step would be
adding a small persistence layer (e.g. saving to a local JSON or SQLite
file automatically after every edit) \u2014 flagged here rather than silently
built in, since it changes how the app behaves and is worth deciding on
deliberately rather than by default.

## What's deliberately simplified (same honesty as the last version)

- Only 3 example cities, 5 glazing types, and the Daikin Ducted FCU range
  are included in `reference_data.py` \u2014 expand these lists from
  `generate_mep_workbook.py`'s Reference Data tab as needed.
- `psychrolib` isn't used \u2014 the moisture content default is a hardcoded
  approximation (see the comment in `reference_data.py`).
- Ventilation, Air Terminals, and the full Reference Data tab from the
  Excel workbook aren't ported yet \u2014 only the HVAC/Room Schedule link.

## Verification

Every number this app produces was cross-checked against the actual Excel
workbook (recalculated in LibreOffice) before being handed over:
Reception (RG-01) with default inputs gives exactly 1.554 kW sensible /
0.304 kW latent / 1.859 kW total in both. I could not, however, run
Streamlit itself in the sandbox this was built in (no internet access to
install it) \u2014 so the calculation logic is verified, but I have not
personally clicked through the running app, and I have not been able to
test `run.bat` on an actual Windows machine either. If something in the
UI or the launcher doesn't behave as described, tell me the exact error
and I'll fix it.

## Turning this into something that "works anywhere"

There are two genuinely different meanings of "anywhere," and they lead
to different work:

### 1. Runs on any Windows PC, no Python installed there at all

Possible with a tool like **PyInstaller**, which bundles Python + this
app + all its packages into one folder (or one `.exe`) that runs
standalone. The honest tradeoffs:
- The output is large (typically 200\u2013400 MB for a Streamlit app,
  since it bundles a full Python runtime)
- Streamlit specifically is known to be fiddly to package this way \u2014
  it needs a small wrapper script and some extra PyInstaller config to
  find its own static files at runtime
- I can't build or test this myself in the sandbox I'm working in (no
  internet access to install PyInstaller, no Windows machine to verify
  the output actually runs) \u2014 so this genuinely needs to be built and
  iterated on a real Windows machine, which is exactly what **Claude
  Code** is for: it can run PyInstaller directly on your machine, see the
  actual errors, and fix them in place, rather than us doing this same
  screenshot-and-guess cycle we've already been through twice.

### 2. Opens from any device via a web link

This is actually the easier win, and doesn't need PyInstaller at all.
**Streamlit Community Cloud** (free) hosts a Streamlit app straight from
a GitHub repo:
1. Create a free GitHub account if you don't have one, and push this
   folder to a new repository
2. Go to share.streamlit.io, sign in, point it at your repo and
   `streamlit_app.py`
3. It gives you a URL (like `yourapp.streamlit.app`) that works from any
   phone, laptop, anywhere

**Important tradeoffs to know before doing this:**
- It would be **publicly accessible** to anyone with the link unless you
  add password protection (Streamlit supports this, but it's an extra
  step, not default)
- Data still doesn't persist between sessions the way this app is built
  right now (see the limitation below) \u2014 that matters more once
  multiple people might use it
- Free tier apps "sleep" after inactivity and take a few seconds to wake
  up on the next visit

**My honest recommendation:** if you want this usable beyond just your
own machine, cloud hosting (option 2) is the higher-value, lower-effort
step to take first. The standalone `.exe` mainly matters if you need it
to work completely offline on other machines with zero setup \u2014 worth
doing, but a bigger, separate piece of work best tackled in Claude Code
where it can actually be tested.
