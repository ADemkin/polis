### Polis

Парсер выписок из росреестра.


# Known bugs:
1. .xlsx files should be named in ascii only (english symbols)

# Installation:
1. clone this repo
2. create .env file near run.py with folowing contents:
```
STATIC_DIR='/var/tmp/polis/static/'
SETTINGS_DIR='/var/tmp/polis/'
DEBUG_MODE=True
PORT=9999
```
Done!

