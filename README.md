
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


Setup
-----

`./setup.sh`  
`./install.sh`  

Uninstall  
`./uninstall.sh`  


Commands
--------

`yt download -u [URL]` - Download a video.  
`yt transcript -u [URL]` or `-f [FILE]` - Transcribe a video; writes `.srt` and `.txt` files next to it.  
`yt summarize -u [URL]` or `-f [FILE]` - Transcribe and summarize with OpenAI (a `.txt` transcript also works as input).  
`yt update` - Update to the latest GitHub release (`-f` to force; `git clone` users should `git pull` instead).  

Transcribing prompts for a language (en, zh, ja).  
Summarizing requires `OPENAI_API_KEY` — copy `.env.example` to `.env` and set it.  

Shortcuts: combine the command's first letter with its flag, e.g.  
`yt -du [URL]` == `yt download -u [URL]` (also `-su`, `-sf`, `-tu`, `-tf`).  
Run `yt -h` or `yt <command> -h` for full options.  


Scripts
-------

Clear  
`./clear.sh`  

Release
`./release.sh` - Create a new release on GitHub.
