# Quick Video Text Overlay Tool

Simple and very limited tool to overlay text on top of a video file.  Mostly written by GPT4.

To run the example:

```sh
# to view on screen with ffplay (add `-o output.mp4` to save to a new file instead)
python3 ffmpeg-overlay-text.py -i example/demo.mp4 -c example/commands.txt
```

Refer to [`example/commands.txt`](./example/commands.txt) and it will be clear how to use the tool.