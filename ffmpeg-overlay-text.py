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
import subprocess
import sys

BOTTOM_CENTER = 1
TOP_CENTER    = 2

def make_drawtext_string(msg,color,size,position,start_sec,end_sec):
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

def make_drawtext_array_string(drawtext_args):
    if len(drawtext_args)==0:
        raise(Exception("No arguments passed"))
    drawtext = ''
    for el in drawtext_args:
        drawtext += make_drawtext_string(el['msg'], el['color'], el['size'], el['position'], el['start_sec'], el['end_sec']) + ','
    drawtext = drawtext[:-1]  # strip extra comma at end
    return drawtext

# Returns an array of command followed by args, e.g., ['ls', '-l', '-a', '/path/to/dir']
def make_full_cmd_arr(input_filename, output_filename, drawtext_args, overwrite_outputfile=False):
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
                        raise ValueError("Message quotes not properly defined")
                  
                    msg = line[first_quote_index+1:last_quote_index].replace("\\'", "'").replace('\\"', '"')
                  
                    # Split the rest of the line outside the quotes
                    pre_msg = line[:first_quote_index].strip()
                    post_msg = line[last_quote_index+1:].strip()

                    if pre_msg != '':
                        raise ValueError("Line format incorrect, expected no characters before message")
                    if not post_msg.startswith(':'):
                        raise ValueError("Line format incorrect, expected a colon after end of message")
                    post_msg = post_msg[1:].strip() # remove leading colon
                    if post_msg.count(':') != 3:
                        raise ValueError("Line format incorrect, expected exactly 3 colon separated fields after message")
                  
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
                        'position': 1 if position == 'BOTTOM' else 2,
                        'start_sec': start_sec,
                        'end_sec': end_sec
                    }
                    subtitles.append(subtitle)
                except Exception as e:
                    raise Exception(f"Failed to parse line: {line}. Error: {e}")
        return subtitles

def main():
    try:
        global g_verbose
        parser = argparse.ArgumentParser(description = 'Adds captions to a movie file',
                                        epilog = None)
        parser.add_argument('-v', '--verbose', action='store_true', required=False, help='Verbose output on stderr')
        parser.add_argument('-y', '--overwrite-output-file', action='store_true', required=False, help='Overwrite output file without prompting if it exists')
        parser.add_argument('-i', '--input-file', action='store', required=True, help='Input movie file', dest='input_filename')
        parser.add_argument('-o', '--output-file', action='store', required=False, help='Output movie file (omit for live preview)', dest='output_filename')
        parser.add_argument('-c', '--command-file', action='store', required=True, help='File containing sequence of caption commands\nline format: \'msg\':color:size:[TOP|BOTTOM]:from-to\nOnly \'msg\' is required and it must be single-quoted with backslash escapes for internal apostrophes', dest='command_file')
        args = parser.parse_args()
        g_verbose = args.verbose

        input_commands_arr = parse_cmd_file(args.command_file)
        cmd_arr = make_full_cmd_arr(args.input_filename, args.output_filename, input_commands_arr, args.overwrite_output_file)

        # Print the command and run it
        cmd_str = ' '.join(cmd_arr)
        print(f"\033[92m{cmd_str}\033[0m")
        subprocess.run(cmd_str, shell=True)
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        print('error: %s'%e)
        raise(e)
    return 0

if __name__ == "__main__":
    sys.exit(main())
