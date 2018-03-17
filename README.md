# Firefed

[![Build Status](https://travis-ci.org/numirias/firefed.svg?branch=master)](https://travis-ci.org/numirias/firefed)
[![codecov](https://codecov.io/gh/numirias/firefed/branch/master/graph/badge.svg)](https://codecov.io/gh/numirias/firefed)
[![PyPI Version](https://img.shields.io/pypi/v/firefed.svg)](https://pypi.python.org/pypi/firefed)
[![Python Versions](https://img.shields.io/pypi/pyversions/firefed.svg)](https://pypi.python.org/pypi/firefed)

Firefed is a command-line tool to inspect Firefox profiles. It can extract saved passwords, preferences, addons, history and more. You may use it for forensic analysis, to audit your config for insecure settings or just to quickly extract some data without starting up the browser.

Note that Firefed is a work in progress and not all features work seamlessly yet -- but you're more than welcome to contribute, e.g. with bug reports and usage feedback.


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
                        profile name or directory to be used when running a
                        feature
  -v, --verbose         verbose output (can be used multiple times)
  -f, --force           treat target as a profile directory even if it doesn't
                        look like one

features:
  Set the feature you want to run as positional argument. Each feature has
  its own sub arguments which can be listed with `firefed <feature> -h`.

  FEATURE
    addons              List installed addons/extensions.
    bookmarks           List bookmarks.
    cookies             List cookies.
    downloads           List downloaded files.
    forms               List form input history (search terms, address fields,
                        etc.).
    history             List history.
    hosts               List known hosts.
    infect              Install a PoC reverse shell via a hidden extension.
    inputhistory        List history of urlbar inputs (typed URLs).
    logins              List saved logins.
    permissions         List host permissions (e.g. location sharing).
    preferences         List user preferences.
    summary             Summarize results of all (summarizable) features.
    visits              List history of visited URLs.
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

Don't find a cookie you have definitely set? Not all cookies are
immediately written to the cookie store. You possibly need to close the
browser first to force all cookies being written to disk.


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

Searches in the browser's searchbar have the key "searchar-history".


```
usage: firefed forms [-h] [-s]

optional arguments:
  -h, --help     show this help message and exit
  -s, --summary  summarize results
```

### History

List history.


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

This is highly experimental and only a proof of concept. Also note the
extension currently isn't actually hidden and disappears with the next
browser restart.

The reverse shell will attempt to connect to `localhost:8123` and provides
a JS REPL with system principal privileges.


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

List saved logins.

You can provide a valid master password, but firefed doesn't (yet) support
cracking an unkown password.


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

List host permissions (e.g. location sharing).

This feature extracts the stored permissions which the user has granted to
particular hosts (e.g. popups, location sharing, desktop notifications).


```
usage: firefed permissions [-h] [-f {table,csv}] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -f {table,csv}, --format {table,csv}
                        output format
  -s, --summary         summarize results
```

### Preferences

List user preferences.

This feature reads the preferences from `prefs.js` and `user.js`.
Unfortunately, we can't extract any default values since these aren't
stored in the profile.


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

Summarize results of all (summarizable) features.


```
usage: firefed summary [-h]

optional arguments:
  -h, --help  show this help message and exit
```

### Visits

List history of visited URLs.

This is different from the `history` feature because it lists a single
entry with a timestamp for each individual visit, even if the URL is the
same.


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
