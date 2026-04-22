import yt_dlp
import os

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_formats(url):
    ydl_opts = {"quiet": True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        formats = []
        for f in info["formats"]:
            if f.get("height") and f.get("ext") == "mp4":
                formats.append({
                    "id": f["format_id"],
                    "q": f"{f['height']}p"
                })

        return formats[:5]

def download_video(url, format_id):
    ydl_opts = {
        "format": format_id,
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)