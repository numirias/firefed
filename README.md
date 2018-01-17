# Firefed

[![Build Status](https://travis-ci.org/numirias/firefed.svg?branch=master)](https://travis-ci.org/numirias/firefed)
[![codecov](https://codecov.io/gh/numirias/firefed/branch/master/graph/badge.svg)](https://codecov.io/gh/numirias/firefed)
[![PyPI Version](https://img.shields.io/pypi/v/firefed.svg)](https://pypi.python.org/pypi/firefed)
[![Python Versions](https://img.shields.io/pypi/pyversions/firefed.svg)](https://pypi.python.org/pypi/firefed)

Firefed is a command-line tool to inspect Firefox profiles. It can extract saved passwords, preferences, addons, history and more. You may use it for forensic analysis, to audit your config for insecure settings or just to quickly extract some data without starting up the browser.

(Note that Firefed is currently under development and not all features work seamlessly yet.)


## Installation

Install the package, preferably via `pip`:

```
pip install firefed --upgrade 
```

## Usage

<!--usage-start-->
```
$ firefed -h
usage: firefed [-h] [-P] [-p PROFILE] [-v] [-f] FEATURE ...

A tool for Firefox profile analysis, data extraction, forensics and hardening

optional arguments:
  -h, --help            show this help message and exit
  -P, --profiles        show all local profiles
  -p PROFILE, --profile PROFILE
                        profile name or directory
  -v, --verbose         verbose output (can be used multiple times)
  -f, --force           force treating target as a profile directory even if
                        it doesn't look like one

features:
  Set the feature you want to run as positional argument. Each feature has
  its own sub arguments.

  FEATURE
    addons              List installed addons/extensions.
    bookmarks           List bookmarks.
    cookies             List cookies.
    downloads           List downloaded files.
    forms               List form input history (search terms, address fields,
                        etc.).
    history             Extract history.
    hosts               List known hosts.
    infect              Install a PoC reverse shell via a hidden extension.
    inputhistory        List history of urlbar inputs (typed URLs).
    logins              Extract saved logins.
    permissions         Extract permissions granted to particular hosts (e.g.
                        location sharing).
    preferences         Extract user preferences. (This doesn't include
                        defaults.)
    summary             Summarize results of all features (that can be
                        summarized).
    visits              Extract history of visited URLs.
```
<!--usage-end-->

## Features

<!--features-start-->
### Addons

List installed addons/extensions.

```
usage: firefed addons [-h] [-a] [-A] [-S] [-f {list,short,csv}] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -a, --all             show all extensions (including system extensions)
  -A, --show-addons-json
                        show entries from "addons.json"
  -S, --show-startup-json
                        show addon startup entries (from
                        "addonStartup.json.lz4")
  -f {list,short,csv}, --format {list,short,csv}
                        output format
  -s, --summary         summarize results
```

### Bookmarks

List bookmarks.

```
usage: firefed bookmarks [-h] [-f {tree,list,csv}] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -f {tree,list,csv}, --format {tree,list,csv}
                        output format
  -s, --summary         summarize results
```

### Cookies

List cookies.

```
usage: firefed cookies [-h] [-H HOST] [-a] [-S SESSION_FILE]
                       [-f {setcookie,list,csv}] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  filter by hostname (glob)
  -a, --all             show cookies from all sources, including all available
                        session files
  -S SESSION_FILE, --session-file SESSION_FILE
                        extract cookies from session file (you can use
                        "recovery", "previous", "sessionstore" as shortcuts
                        for default file locations)
  -f {setcookie,list,csv}, --format {setcookie,list,csv}
                        output format
  -s, --summary         summarize results
```

### Downloads

List downloaded files.

```
usage: firefed downloads [-h] [-s]

optional arguments:
  -h, --help     show this help message and exit
  -s, --summary  summarize results
```

### Forms

List form input history (search terms, address fields, etc.).

```
usage: firefed forms [-h] [-s]

optional arguments:
  -h, --help     show this help message and exit
  -s, --summary  summarize results
```

### History

Extract history.

```
usage: firefed history [-h] [-f {list,short,csv}] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -f {list,short,csv}, --format {list,short,csv}
                        output format
  -s, --summary         summarize results
```

### Hosts

List known hosts.

```
usage: firefed hosts [-h] [-s]

optional arguments:
  -h, --help     show this help message and exit
  -s, --summary  summarize results
```

### Infect

Install a PoC reverse shell via a hidden extension.

```
usage: firefed infect [-h] [-u] [-c] [-y]

optional arguments:
  -h, --help       show this help message and exit
  -u, --uninstall  uninstall malicious addon
  -c, --check      check if profile appears infected
  -y, --yes        don't prompt for confirmation
```

### InputHistory

List history of urlbar inputs (typed URLs).

```
usage: firefed inputhistory [-h] [-s]

optional arguments:
  -h, --help     show this help message and exit
  -s, --summary  summarize results
```

### Logins

Extract saved logins.

```
usage: firefed logins [-h] [-l LIBNSS] [-p PASSWORD] [-f {table,list,csv}]
                      [-s]

optional arguments:
  -h, --help            show this help message and exit
  -l LIBNSS, --libnss LIBNSS
                        path to libnss3
  -p PASSWORD, --master-password PASSWORD
                        profile's master password (If not set, an empty
                        password is tried. If that fails, you're prompted.)
  -f {table,list,csv}, --format {table,list,csv}
                        output format
  -s, --summary         summarize results
```

### Permissions

Extract permissions granted to particular hosts (e.g. location sharing).

```
usage: firefed permissions [-h] [-f {table,csv}] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -f {table,csv}, --format {table,csv}
                        output format
  -s, --summary         summarize results
```

### Preferences

Extract user preferences. (This doesn't include defaults.)

```
usage: firefed preferences [-h] [-d] [-c] [-S PATH] [-b] [-i] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -d, --duplicates      show all preferences, even if the key appears multiple
                        times (otherwise, only the last occurence is shown
                        because it overrides all previous occurences)
  -c, --check           compare preferences with recommended settings
  -S PATH, --source PATH
                        path to file with recommended settings (use "userjs-
                        master" or "userjs-relaxed" to load userjs config from
                        Github)
  -b, --bad-only        when comparing with recommendations, show only bad
                        values
  -i, --include-undefined
                        when comparing with recommendations, treat undefined
                        preferences as bad values
  -s, --summary         summarize results
```

### Summary

Summarize results of all features (that can be summarized).

```
usage: firefed summary [-h]

optional arguments:
  -h, --help  show this help message and exit
```

### Visits

Extract history of visited URLs.

```
usage: firefed visits [-h] [-f {list,csv}] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -f {list,csv}, --format {list,csv}
                        output format
  -s, --summary         summarize results
```

<!--features-end-->

## Related tools

- [dumpzilla](https://github.com/Busindre/dumpzilla) (Extracts various information in a single step)

- [firefox_decrypt](https://github.com/unode/firefox_decrypt) (Extracts passwords)
