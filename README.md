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

The Convert tab calculates the entered RUB amount when Enter is pressed. The History tab can export saved rate records to an XLSX workbook.

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
