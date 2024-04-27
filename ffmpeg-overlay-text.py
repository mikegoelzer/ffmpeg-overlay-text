#!env python3

#
# Example of how we shell out to add text overlays:
#
#   ffmpeg -y -i test.mp4 \  # -y = overwrite output
#   -vf "drawtext=\          # 1st drawtext cmd
#   fontfile=/System/Library/Fonts/Supplemental/Verdana.ttf:\
#   text='Hello, world!':\   # the text
#   fontcolor=red:\          # color
#   fontsize=48:\            # size
#   box=1:boxcolor=black@0.5:boxborderw=5:\   # bounding box, 50% alpha
#   x=(w-text_w)/2:y=h-th-40:\                # bottom center
#   enable='between(t,5,10)',\                # from 5-10sec
#   drawtext=\                                # 2nd drawtext command
#   fontfile=/System/Library/Fonts/Supplemental/Verdana.ttf:\
#   text='Hello again!':\
#   fontcolor=green:\
#   fontsize=48:\
#   boxcolor=black@0.5:boxborderw=5:\
#   x=(w-text_w)/2:y=40:\                     # top center
#   enable='between(t,0,5)'" \                # from 0-5 sec
#   -codec:a copy x.mp4                       # otherwise just copy the video straight through, no changes
# 
# (Same syntax for `ffplay ...` to just show preview)
# 

import argparse
import subprocess
import sys

BOTTOM_CENTER = 1
TOP_CENTER    = 2

def make_drawtext_string(msg,color,size,position,start_sec,end_sec):
    """
    Returns a string like "drawtext=..." based on the arguments
    """
    fontfile = 'fontfile=/System/Library/Fonts/Supplemental/Verdana.ttf'
    bottom_center = 'x=(w-text_w)/2:y=h-th-40'
    top_center = 'x=(w-text_w)/2:y=40'
    box = 'box=1:boxcolor=black@0.5:boxborderw=5'

    if start_sec is None and end_sec is None:
        enable_period = None
    else:
        enable_period = 'enable=\'between(t,%d,%d)\''%(start_sec,end_sec)

    if position == BOTTOM_CENTER:
        pos_str = bottom_center
    elif position == TOP_CENTER:
        pos_str = top_center
    else:
        raise(Exception("Unknown position '%d'"%position))

    drawtext = 'drawtext=fontfile=%s:text=\'%s\':fontcolor=%s:fontsize=%d:%s:%s'%(fontfile,msg,color,size,box,pos_str)
    if not start_sec is None and not end_sec is None:
        enable_period = 'enable=\'between(t,%d,%d)\''%(start_sec,end_sec)
        drawtext += ':%s'%enable_period
    return drawtext

def make_drawtext_array(drawtext_args):
    """
    Turns each dictionary element into a string like "drawtext=..." and returns these
    strings in an array.
    """
    if len(drawtext_args)==0:
        raise(Exception("No arguments passed"))
    drawtext_arr = []
    for el in drawtext_args:
        drawtext_arr.append(make_drawtext_string(el['msg'], el['color'], el['size'], el['position'], el['start_sec'], el['end_sec']))
    return drawtext_arr

def make_drawtext_array_string(drawtext_args):
    """
    Turns an array of strings into a comma-separated string, e.g., 'a,b,c'
    """
    arr = make_drawtext_array(drawtext_args)
    drawtext_str = ','.join(arr)
    return drawtext_str

def make_full_cmd_arr(input_filename, output_filename, drawtext_args, overwrite_outputfile=False):
    """
    Returns an array of command followed by args, e.g., ['ls', '-l', '-a', '/path/to/dir']
    """
    cmd = []
    
    # If output_filename is None, we do an `ffplay` instead of conversion
    if output_filename is None:
        cmd.append('ffplay')
    else:
        cmd.append('ffmpeg')
        if overwrite_outputfile:
            cmd.append('-y')

    cmd.append('-i')
    cmd.append(input_filename)
    cmd.append('-vf')
    cmd.append('"%s"'%make_drawtext_array_string(drawtext_args))

    if not output_filename is None:
        cmd.append('-codec:a')
        cmd.append('copy')
        cmd.append(output_filename)
    return cmd

def parse_cmd_file(command_file):
    """
    Parses the command file and returns an array of dictionaries corresponding to each line.
    Lines starting with '#' are skipped, as are blank lines.
    Each line is a colon separated list of fields.
     - The first field is the message to display; must be in single or double quotes.
     - The second field is the color of the text, e.g., red, green, blue, etc.
     - The third field is the size of the text, e.g., 48.
     - The fourth field is the position of the text, either 'TOP' or 'BOTTOM'.
     - The fifth field is the time range in seconds, e.g., '5-10' to display the message from second 5 to second 10.
    (See example/commands.txt for syntax.)
    """
    subtitles = []
    with open(command_file, 'r') as file:
        for line in file:
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            try:
                # Find the message by locating the first and last quote
                first_quote_index = line.find("'") if line.find("'") != -1 else line.find('"')
                last_quote_index = line.rfind("'") if line.rfind("'") != -1 else line.rfind('"')
                if first_quote_index == -1 or last_quote_index == -1 or first_quote_index == last_quote_index:
                    raise ValueError("message must be first field and either single or double quoted")
                
                msg = line[first_quote_index+1:last_quote_index]
                
                # Split the rest of the line outside the quotes
                pre_msg = line[:first_quote_index].strip()
                post_msg = line[last_quote_index+1:].strip()

                # there should be no characters before the first quote
                if pre_msg != '':
                    raise ValueError("Line format incorrect, expected no characters before message")
                
                # first character should now be a colon, which we remove
                if not post_msg.startswith(':'):
                    raise ValueError("Line format incorrect, expected a colon after end of message")
                post_msg = post_msg[1:].strip() # remove leading colon
                
                # there should be exactly 3 colon separated fields left now
                if post_msg.count(':') != 3:
                    raise ValueError("Line format incorrect, expected exactly 3 colon separated fields after message")
                
                # split and insert into dictionary, which we add to the return array of dicts
                parts = post_msg.split(':')
                color = parts[0].strip()
                size = int(parts[1].strip())
                position = parts[2].strip().upper()
                if position not in ['TOP', 'BOTTOM']:
                    raise ValueError("Position must be either 'TOP' or 'BOTTOM'")
                
                time_range = parts[3].strip()
                start_sec, end_sec = map(int, time_range.split('-'))
                
                subtitle = {
                    'msg': msg,
                    'color': color,
                    'size': size,
                    'position': BOTTOM_CENTER if position == 'BOTTOM' else TOP_CENTER,
                    'start_sec': start_sec,
                    'end_sec': end_sec
                }
                subtitles.append(subtitle)

            except Exception as e:
                raise Exception(f"error: {e} on parse of line {line}")
            
    return subtitles

def print_cmd(cmd_arr, drawtext_arr):
    color_escape = '\033[92m'
    reset_escape = '\033[0m'
    indent = '  '
    backslash_column = 79
    print(color_escape)
    for i, cmd in enumerate(cmd_arr):
        if cmd.startswith('"'):
            for i, drawtext_str in enumerate(drawtext_arr):
                if i == 0:
                    drawtext_str = '"' + drawtext_str
                if i == len(drawtext_arr) - 1:
                    drawtext_str += '"'
                drawtext_str = f"{indent}{drawtext_str}"
                if len(drawtext_str) < backslash_column:
                    drawtext_str = drawtext_str.ljust(backslash_column) + ' \\'
                else:
                    drawtext_str = drawtext_str + ' \\'
                if i < len(cmd_arr) - 1:
                    print(drawtext_str)
                else:
                    print(drawtext_str.rstrip(' \\'))
        else:
            if i == 0:
                line = f"{cmd}"
            else:
                line = f"{indent}{cmd}"
            
            if len(line) < backslash_column:
                line = line.ljust(backslash_column) + ' \\'
            else:
                line = line + ' \\'
            print(line)                
    print(reset_escape)  # Reset color

def main():
    try:
        parser = argparse.ArgumentParser(description = 'Adds captions to a movie file',
                                         epilog = None)
        parser.add_argument('-i', '--input-file', action='store', required=True, help='input video file', dest='input_filename')
        parser.add_argument('-o', '--output-file', action='store', required=False, help='output video file (omit for live preview)', dest='output_filename')
        parser.add_argument('-c', '--command-file', action='store', required=True, help='file containing sequence of caption commands; see example/commands.txt for syntax', dest='command_file')
        parser.add_argument('-y', '--overwrite-output-file', action='store_true', required=False, help='overwrite output file if exists')
        args = parser.parse_args()

        # parse the command file and generate the command to run
        input_commands_arr = parse_cmd_file(args.command_file)
        cmd_arr = make_full_cmd_arr(args.input_filename, args.output_filename, input_commands_arr, args.overwrite_output_file)

        # print the command in green for clarity to user
        print_cmd(cmd_arr, make_drawtext_array(input_commands_arr))

        # shell out and run the command
        cmd_str = ' '.join(cmd_arr)
        subprocess.run(cmd_str, shell=True)
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        print('error: %s'%e)
        raise(e)
    return 0

if __name__ == "__main__":
    sys.exit(main())
