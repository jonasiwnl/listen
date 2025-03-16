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
    parser.add_argument('--choose-mic', action='store_true')
    parser.add_argument('-l', '--language', type=str, default='en')
    return parser.parse_args()


def find_microphones():
    res = subprocess.run(
        ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""'], 
        text=True,
        capture_output=True,
    )
    devices = [line.strip() for line in res.stderr.split('\n') if 'microphone' in line.lower()]
    return devices


def choose_microphone():
    devices = find_microphones()
    if not devices:
        print('No microphones found.')
        sys.exit(1)
 
    print('Available microphones:')
    for i, device in enumerate(devices): print(f'{i}: {device}')
 
    choice = int(input('Choose a microphone: '))
    while choice < 0 or choice >= len(devices):
        print('Invalid choice.')
        choice = int(input('Choose a microphone: '))

    return choice


def record_audio(args):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp.close()

    ffmpeg_stdout = sys.stdout if args.verbose else subprocess.DEVNULL
    ffmpeg_stderr = sys.stderr if args.verbose else subprocess.DEVNULL

    mic_index = ':1'
    if args.choose_mic: mic_index = f':{choose_microphone()}'
 
    process = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'avfoundation', '-i', mic_index, temp.name], 
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
    filename = record_audio(args)
    transcription = transcribe_audio(filename, args)
    print(f'Transcription: {transcription}')
    if not args.no_copy: copy_to_clipboard(transcription)


if __name__ == '__main__':
    main()
