#!env python3

# ffmpeg -y -i test.mp4 \  # -y = overwrite output
# -vf "drawtext=\          # 1st drawtext cmd
# fontfile=/System/Library/Fonts/Supplemental/Verdana.ttf:\
# text='Hello, world!':\   # the text
# fontcolor=red:\          # color
# fontsize=48:\            # size
# box=1:boxcolor=black@0.5:boxborderw=5:\   # bounding box, 50% alpha
# x=(w-text_w)/2:y=h-th-40:\                # bottom center
# enable='between(t,5,10)',\                # from 5-10sec
# drawtext=\                                # 2nd drawtext command
# fontfile=/System/Library/Fonts/Supplemental/Verdana.ttf:\
# text='Hello again!':\
# fontcolor=green:\
# fontsize=48:\
# boxcolor=black@0.5:boxborderw=5:\
# x=(w-text_w)/2:y=40:\                     # top center
# enable='between(t,0,5)'" \                # from 0-5 sec
# -codec:a copy x.mp4                       # otherwise just copy the video straight through, no changes

# Same but with `ffplay ...` just shows preview

import argparse
import sys

BOTTOM_CENTER = 1
TOP_CENTER    = 2

def make_drawtext_string(msg,color,size,position,start_sec,end_sec):
  fontfile = 'fontfile=/System/Library/Fonts/Supplemental/Verdana.ttf'
  bottom_center = 'x=(w-text_w)/2:y=h-th-40'
  top_center = 'x=(w-text_w)/2:y=40'
  box = 'box=1:boxcolor=black@0.5:boxborderw=5'

    enable_period = None
  else
    enable_period = 'enable=\'between(t,%d,%d)\''%(start_sec,end_sec)

  if position == BOTTOM_CENTER:
    pos_string = bottom_center
  elif position == TOP_CENTER:
    pos_string = top_center
  else:
    raise(Exception("Unknown position '%d'"%position)

  drawtext = 'drawtext=fontfile=%s:text=\'%s\':fontcolor=%s:fontsize=%d:%s:%s'%(fontfile,msg,color,size,box,pos_str)
  if not start_sec is None and not end_sec is None:
    enable_period = 'enable=\'between(t,%d,%d)\''%(start_sec,end_sec)
    drawtext += ':%s'%enable_period
  return drawtext

def make_drawtext_array_string(drawtext_args):
  if len(drawtext_args)==0:
    raise(Exception("No arguments passed"))
  drawtext = ''
  for (el in drawtext_args):
    drawtext += make_drawtext_string(el.msg, el.color, el.size, el.position, el.start_sec, el.end_sec) + ','
  drawtext = drawtext[0,len(drawtext)-1]  # strip extra comma at end
  return drawtext

# Returns an array of command followed by args, e.g., ['ls', '-l', '-a', '/path/to/dir']
def make_full_cmd_arr(input_filename, output_filename, drawtext_args, overwrite_outputfile=False):
  cmd = []
  
  if overwrite_outputfile:
    overwrite_str = '-y '
  else:
    overwrite_str = ''

  # If output_filename is None, we do an `ffplay` instead of conversion
  if output_filename is None:
    cmd.push('ffplay')
  else:
    cmd.push('ffmpeg')
    if overwrite_outputfile:
      cmd.push('-y')

  cmd.push('-i')
  cmd.push(input_filename)
  cmd.push('-vf')
  cmd.push('"%s"')%make_drawtext_array_string(drawtext_args)

  if not output_filename is None:
    cmd.push('-codec:a')
    cmd.push('copy')
    cmd.push(output_filename)
  return cmd

def make_arg_parser():
  parser = argparse.ArgumentParser(
    description = 'Adds captions to a movie file',
    epilog = None)
  parser.add_argument('-v', '--verbose', action='store_true', required=False, help='Verbose output on stderr')
  parser.add_argument('-y', '--overwrite-output-file', action='store_true', required=False, help='Overwrite output file without prompting if it exists')
  parser.add_argument('-i', '--input-file', action='store', required=True, help='Input movie file', dest='input_filename')
  parser.add_argument('-o', '--output-file', action='store', required=False, help='Output movie file (omit for live preview)', dest='output_filename')
  parser.add_argument('command-file', metavar='COMMAND_FILE', help='File containing sequence of caption commands\nline format: \'msg\':color:size:[TOP|BOTTOM]:from-to\nOnly \'msg\' is required and it must be single-quoted with backslash escapes for internal apostrophes', dest='command_file')
  return parser

def main():
  try:
    global g_verbose
    args = make_arg_parser().parse_args()
    g_verbose = args.verbose

    input_commands_arr = parse_cmd_file(args.command_file)
    cmd_arr = make_full_cmd_arr(input_commands_arr)

    # run cmd_arr
    # TODO...
    
  except KeyboardInterrupt:
    return 1
  except Exception(e):
    print('error: %s'%e)
    raise(e)
  return 0

if __name__ == "__main__":
  sys.exit(main())
