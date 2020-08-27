import youtube_dl

ydl_opts = {
    'format': 'bestvideo/best',
}
with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://www.youtube.com/watch?v=wlLHZruDCAA'])
