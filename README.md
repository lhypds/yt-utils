
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

Setup
`./setup.sh`  
`./install.sh`  

Uninstall  
`./uninstall.sh`  


Commands
--------

donwload  
Download Youtube video.  
`yt download -u [URL]` - Download a video from Youtube.  

transcript  
Get transcript from a Youtube video. You'll be prompted to pick a language (en, zh, ja).  
`yt transcript -u [URL]` - Get the transcript of a video from Youtube.  
`yt transcript -f [FILE]` - Get the transcript of a video file.  
This will generate a `.srt` subtitle file and a `.txt` transcript file in the video's directory.  

summarize  
Summarize a Youtube video by transcribing it and asking OpenAI for the main points.  
Copy `.env.example` to `.env` and set `OPENAI_API_KEY` first.  
You'll be prompted to pick a language (en, zh, ja) unless the input is an existing `.txt` transcript.  
`yt summarize -u [URL]` - Summarize a video from Youtube.  
`yt summarize -f [FILE]` - Summarize a video file.  
`yt summarize -f [FILE.txt]` - Summarize an existing transcript file.  

update  
For user use GitHub releases to update `yt`, for `git clone` users, use `git pull` instead.  
Update `yt` to the latest release from GitHub (`lhypds/yt`).  
`yt -v` - Show the current version.  
`yt update` - Download and install the latest release if newer.  
`yt update -f` - Force reinstall even when already up to date.  


Shortcuts
---------

Combine the command's first letter with its flag:  
`yt -du [URL]` - Same as `yt download -u [URL]`.  
`yt -su [URL]` - Same as `yt summarize -u [URL]`.  
`yt -sf [FILE]` - Same as `yt summarize -f [FILE]`.  
`yt -tu [URL]` - Same as `yt transcript -u [URL]`.  
`yt -tf [FILE]` - Same as `yt transcript -f [FILE]`.  


Scripts
-------

Clear  
`./clear.sh`  

Release
`./release.sh` - Create a new release on GitHub.
