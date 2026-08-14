
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

And all other sources supported in `yt-dlp`.  


Install
-------

Linux and macOS, one command — downloads the latest release and installs `yt`
into `~/.local/bin`:  

```bash
curl -fsSL https://raw.githubusercontent.com/lhypds/yt/master/get.sh | bash
```

Options: `--version 0.0.11` to pin a release, `--dir PATH` to unpack somewhere
other than `~/.yt` (`bash -s -- --version 0.0.11` when piping). Re-run it to
upgrade — or just use `yt update`; settings and the virtualenv are kept either
way.  

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


Commands
--------

`yt download -u [URL]` - Download a video.  
`yt transcript -u [URL]` or `-f [FILE]` - Transcribe a video; writes `.srt` and `.txt` files next to it.  
`yt summarize -u [URL]` or `-f [FILE]` - Transcribe and summarize with OpenAI (a `.txt` transcript also works as input).  
`yt update` - Update to the latest GitHub release (`-f` to force; `git clone` users should `git pull` instead).  

Transcribing prompts for a language (en, zh, ja).  
Summarizing requires `OPENAI_API_KEY` — see Settings above.  

Shortcuts: combine the command's first letter with its flag, e.g.  
`yt -du [URL]` == `yt download -u [URL]` (also `-su`, `-sf`, `-tu`, `-tf`).  
Run `yt -h` or `yt <command> -h` for full options.  


Scripts
-------

Clear  
`./clear.sh`  
Release  
`./release.sh` - Create a new release on GitHub.  
