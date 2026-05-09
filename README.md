# YenShift

YenShift is a fixed-size Windows desktop app for estimating the current-day cash conversion path:

```text
RUB -> USD -> JPY
```

It fetches current cash exchange rates from:

- `banki.ru` for the RUB -> USD sell rate
- `tokyo-card.co.jp` for the USD -> JPY buy rate

If an update fails, the app falls back to the latest saved SQLite record when one exists.

## Run

```powershell
pip install -r requirements.txt
python main.py
```

Run these commands from the `currency_app` directory.

## Build

```powershell
pyinstaller --onefile --windowed --name YenShift --icon assets\icons\yenshift_petal.ico main.py
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
