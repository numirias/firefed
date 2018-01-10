# Firefed

[![Build Status](https://travis-ci.org/numirias/firefed.svg?branch=master)](https://travis-ci.org/numirias/firefed)
[![codecov](https://codecov.io/gh/numirias/firefed/branch/master/graph/badge.svg)](https://codecov.io/gh/numirias/firefed)
[![PyPI Version](https://img.shields.io/pypi/v/firefed.svg)](https://pypi.python.org/pypi/firefed)
[![Python Versions](https://img.shields.io/pypi/pyversions/firefed.svg)](https://pypi.python.org/pypi/firefed)

Firefed is a command-line tool to inspect Firefox profiles. It can extract saved passwords, examine preferences, addons, history and more. You may use it for forensic analysis, to audit your config for insecure settings or just to quickly extract some data without starting up the browser.

(Note that Firefed is currently under development.)


## Installation

Install the package, preferably via `pip`:

```
pip install firefed --upgrade 
```

## Usage

<!--help-start-->
```
$ firefed -h
usage: firefed [-h] [-p PROFILE] [-v] [-f] FEATURE ...

A tool for Firefox profile analysis, data extraction, forensics and hardening

optional arguments:
  -h, --help            show this help message and exit
  -p PROFILE, --profile PROFILE
                        profile name or directory
  -v, --verbose         verbose output (can be used multiple times)
  -f, --force           force treating target as a profile directory even if
                        it doesn't look like one

features:
  You must choose a feature.

  FEATURE
    addons              Extract installed addons/extensions.
    bookmarks           List bookmarks.
    cookies             Extract cookies.
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
<!--help-end-->
