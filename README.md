# YenShift

YenShift is a fixed-size Windows desktop app for estimating the current-day cash conversion path:

```text
RUB -> USD -> JPY
```

It fetches current cash exchange rates from:

- `banki.ru` for the RUB -> USD sell rate
- `tokyo-card.co.jp` for the USD -> JPY buy rate

If an update fails, the app falls back to the latest saved SQLite record when one exists.

Automatic rate updates on startup can be enabled in the Settings tab. This option is disabled by default.

Scheduled automatic updates can also be enabled in Settings. When enabled, YenShift checks the local computer time while the app is running and refreshes rates at up to four selected daily times.

YenShift can keep running in the Windows notification area after the main window is closed. On close, choose whether to exit completely or continue in the background. Left-click the tray icon to reopen the app, or right-click it to update rates, open the app, or close YenShift. Scheduled updates continue in the background without playing the update sound.

If YenShift is already running and the shortcut is opened again, the existing app shows a notification instead of starting a second copy.

The Convert tab calculates the entered RUB amount when Enter is pressed. The History tab can export saved rate records to an XLSX workbook.

The Convert tab also shows color indicators next to each rate by comparing it with the latest saved record before the current day: light blue means better, red means worse, white means unchanged, and black means there is no earlier record to compare.

YenShift plays a notification sound after a successful rate update. The sound can be disabled in the Settings tab and is enabled by default.

## Run

```powershell
pip install -r requirements.txt
python main.py
```

Run these commands from the `YenShift` directory.

## Build

```powershell
pyinstaller --noconfirm YenShift.spec
```

The SQLite cache is stored in:

```text
%APPDATA%\YenShift\yenshift.sqlite
```

## Project Layout

```text
main.py
app.py
assets/
ui/
services/
storage/
models/
```

Parser and source logic live outside the UI under `services/`.
