#!/usr/bin/env python3

"""
A MacOS script to convert speech to text using the Whisper model. Assumes ffmpeg is installed on the system.
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time
import whisper


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--no-copy', action='store_true')
    parser.add_argument('-p', '--paste', action='store_true')
    parser.add_argument('-e', '--enter', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--choose-mic', action='store_true')
    parser.add_argument('-l', '--language', type=str, default='en')
    return parser.parse_args()


def find_microphones(args):
    res = subprocess.run(
        ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""'], 
        text=True,
        capture_output=True,
    )
    devices = [line.strip() for line in res.stderr.split('\n') if 'microphone' in line.lower()]
    if not devices:
        print('No microphones found.')
        sys.exit(1)

    mic_index = [i for i, device in enumerate(devices) if 'macbook' in device.lower()][0]
    if args.choose_mic: mic_index = choose_microphone(devices)

    return f':{mic_index}'


def choose_microphone(devices):    
    print('Available microphones:')
    for i, device in enumerate(devices): print(f'{i}: {device}')
 
    choice = int(input('Choose a microphone: '))
    while choice < 0 or choice >= len(devices):
        print('Invalid choice.')
        choice = int(input('Choose a microphone: '))

    return choice


def record_audio(args, mic_index):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp.close()

    ffmpeg_stdout = sys.stdout if args.verbose else subprocess.DEVNULL
    ffmpeg_stderr = sys.stderr if args.verbose else subprocess.DEVNULL

    process = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'avfoundation', '-i', mic_index, temp.name], 
        stdin=subprocess.PIPE,
        stdout=ffmpeg_stdout,
        stderr=ffmpeg_stderr,
    )

    time.sleep(0.5)
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
    print('Copied to clipboard.')


def paste_from_clipboard():
    subprocess.run([
        'osascript',
        '-e',
        'tell application "System Events" to keystroke "v" using command down',
    ])
    print('Pasted from clipboard.')
    

def enter_key():
    subprocess.run([
        'osascript',
        '-e',
        'tell application "System Events" to keystroke return',
    ])


def main():
    args = parse_args()
    mic_index = find_microphones(args)
    filename = record_audio(args, mic_index)
    transcription = transcribe_audio(filename, args)
    print(f'Transcription: {transcription}')
    if not args.no_copy: copy_to_clipboard(transcription)
    if args.paste: paste_from_clipboard()
    if args.enter: enter_key()


if __name__ == '__main__':
    main()
