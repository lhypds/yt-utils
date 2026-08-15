
yt
==


Tools for transcribing and summarizing videos.  
Initially designed for Youtube videos, but should work with any video file.  


Video Sources Supported
-----------------------

Verified sources:  

| Source            | Example                                                              | Notes                                                                          |
| ----------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| YouTube           | `yt summarize -u https://www.youtube.com/watch?v=xxxxxxxx`           |                                                                                |
| bilibili          | `yt summarize -u https://www.bilibili.com/video/xxxxxxxx/`           | Anonymous access caps at 480P; use `--cookies-from-browser` for higher quality |
| x.com (Twitter)   | `yt summarize -u https://x.com/xxxxxxxx/status/xxxxxxxxxxxxxxx`      |                                                                                |
| TikTok            | `yt summarize -u https://www.tiktok.com/@xxxxxxxx/video/xxxxxxxxxxx` |                                                                                |
| Instagram         | `yt summarize -u https://www.instagram.com/reel/xxxxxxxx/`           | May require `--cookies-from-browser` for login-gated posts                     |
| Threads           | `yt summarize -u https://www.threads.com/@xxxxxxxx/post/xxxxxxxx`    | `threads.net` URLs also work                                                   |

And all other sources supported in [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).  


Install
-------

Linux and macOS, one command — downloads the latest release and installs `yt`
into `~/.local/bin`:  

```bash
curl -fsSL https://raw.githubusercontent.com/lhypds/yt/master/get.sh | bash
```

Options: `--version 0.0.11` to pin a release, `--dir PATH` to unpack somewhere
other than `~/.local/share/yt` (`bash -s -- --version 0.0.11` when piping).
Re-run it to upgrade — or just use `yt update`; settings and the virtualenv are
kept either way, the one exception being the move described just below.  

Where things go, following the XDG base directory spec:  

| Path | Holds |
| ---- | ----- |
| `~/.local/bin/yt` | the command — the only part that needs to be on `PATH` |
| `~/.local/share/yt/` | the program and its virtualenv (`$XDG_DATA_HOME`) |
| `~/.config/yt/.env` | the API key (`$XDG_CONFIG_HOME`) |

An install from an earlier release sits in `~/.yt`. The installer moves it the
next time it runs — `yt update` included — and rebuilds the virtualenv at the new
path, because a virtualenv records its own location and stops working when moved.
Nothing else changes: the settings file is untouched, and the Whisper models
faster-whisper downloads are cached outside the install either way.  

From a checkout instead:  

`./setup.sh`  
`./install.sh`  

Uninstall  
`./uninstall.sh`  


Settings
--------

`OPENAI_API_KEY` is required (for `summarize`) and lives in `~/.config/yt/.env`
(`$XDG_CONFIG_HOME/yt/.env` if set).  

`yt` asks for it the first time it needs it and saves the answer there. A key
exported in your shell always wins, and a `.env` next to the install or
checkout takes precedence over `~/.config`.  

`yt config` opens that file in `$EDITOR`; `yt config --show` lists which keys
are set without printing their values.  


Commands
--------

`yt download -u [URL]` - Download a video.  
`yt transcript -u [URL]` or `-f [FILE]` - Transcribe a video; writes `.srt` and `.txt` files next to it.  
`yt summarize -u [URL]` or `-f [FILE]` - Transcribe and summarize with OpenAI (a `.txt` transcript also works as input).  
`yt config` - Edit the settings file holding your API key (`--path` to print its location, `--show` to list which keys are set).  
`yt update` - Update to the latest GitHub release (`-f` to force; `git clone` users should `git pull` instead).  

Transcribing prompts for a language (en, zh, ja).  
Summarizing requires `OPENAI_API_KEY` — see Settings above.  

Shortcuts: combine the command's first letter with its flag, e.g.  
`yt -du [URL]` == `yt download -u [URL]` (also `-su`, `-sf`, `-tu`, `-tf`).  
`config` takes no flag, so its shortcut is just the letter: `yt -c` == `yt config`.  
Run `yt -h` or `yt <command> -h` for full options.  


Scripts
-------

Clear  
`./clear.sh`  
Release  
`./release.sh` - Create a new release on GitHub.  
