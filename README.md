
yt
==


Tools for transcribing and summarizing videos.  
Initially designed for Youtube videos, but should work with any video file. 


Video Sources Supported
-----------------------

Verified sources:

| Source            | Example                                                              | Notes                                                             |
| ----------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------- |
| YouTube           | `yt summarize -u https://www.youtube.com/watch?v=xxxxxxxx`        |                                                                   |
| bilibili          | `yt summarize -u https://www.bilibili.com/video/xxxxxxxx/`       | Anonymous access caps at 480P; use `--cookies-from-browser` for higher quality |
| x.com (Twitter)   | `yt summarize -u https://x.com/xxxxxxxx/status/xxxxxxxxxxxxxxx` |                                                                 |


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
Update `yt` to the latest release from GitHub (`lhypds/yt`).  
`yt -v` - Show the current version.  
`yt update` - Download and install the latest release if newer.  
`yt update -f` - Force reinstall even when already up to date.  


Scripts
-------

Clear  
`./clear.sh`  

Release
`./release.sh` - Create a new release on GitHub.
