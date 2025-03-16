#!/usr/bin/env python3

"""
A MacOS script to convert speech to text using the Whisper model. Assumes ffmpeg is installed on the system.
"""

import argparse
import os
import subprocess
import sys
import tempfile
import whisper


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-copy', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('-l', '--language', type=str, default='en')
    return parser.parse_args()


def find_microphone():
    # If we want a way to choose a specific microphone

    # res = subprocess.run(
    #     ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""'], 
    #     text=True,
    #     capture_output=True,
    # )

    pass


def record_audio(args):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp.close()

    ffmpeg_stdout = sys.stdout if args.verbose else subprocess.DEVNULL
    ffmpeg_stderr = sys.stderr if args.verbose else subprocess.DEVNULL
 
    process = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'avfoundation', '-i', ':1', temp.name], 
        stdin=subprocess.PIPE,
        stdout=ffmpeg_stdout,
        stderr=ffmpeg_stderr,
    )

    print('Recording... Press Ctrl+C to stop.')

    try:
        process.wait()
    except KeyboardInterrupt:
        print() # newline after Ctrl+C
        process.communicate(b'q')
        process.wait(timeout=2)
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    return temp.name


def transcribe_audio(filename: str, args):
    print('Transcribing...')

    devnull = open(os.devnull, 'w')
    stdout = sys.stdout
    stderr = sys.stderr

    if not args.verbose:
        sys.stdout = devnull
        sys.stderr = devnull

    try:
        model = whisper.load_model('turbo')
    finally:
        sys.stdout = stdout
        sys.stderr = stderr
        devnull.close()

    res = model.transcribe(filename, verbose=args.verbose, language=args.language)
    return res['text'].strip()


def copy_to_clipboard(text):
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    process.communicate(input=text.encode('utf-8'))
    print('Copied to clipboard!')


def main():
    args = parse_args()
    find_microphone()
    filename = record_audio(args)
    transcription = transcribe_audio(filename, args)
    print(f'Transcription: {transcription}')
    if not args.no_copy: copy_to_clipboard(transcription)


if __name__ == '__main__':
    main()
