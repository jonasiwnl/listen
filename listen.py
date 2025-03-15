#!/usr/bin/env python3

"""
A MacOS script to convert speech to text using the Whisper model. Assumes ffmpeg is installed on the system.
"""
import subprocess
import tempfile
import whisper
import os
import sys


def find_microphone():
    # If we want a way to choose a specific microphone

    # res = subprocess.run(
    #     ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""'], 
    #     text=True,
    #     capture_output=True,
    # )

    pass


def record_audio():
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp.close()
    
    process = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "avfoundation", "-i", ":1", temp.name], 
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("Recording... Press Ctrl+C to stop.")

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nStopping recording...")
        process.communicate(b'q')
        process.wait(timeout=2)
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    return temp.name


def transcribe_audio(filename: str):
    print("Transcribing...")

    # Suppress stdout and stderr
    devnull = open(os.devnull, 'w')
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = devnull
    sys.stderr = devnull

    try:
        model = whisper.load_model("turbo")
    finally:
        # Restore stdout and stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        devnull.close()

    res = model.transcribe(filename, verbose=False)
    return res["text"]


def copy_to_clipboard(text):
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    process.communicate(input=text.encode('utf-8'))
    print("Copied to clipboard!")


def main():
    find_microphone()
    filename = record_audio()
    transcription = transcribe_audio(filename).strip()
    print(f'Transcription: {transcription}')
    copy_to_clipboard(transcription)


if __name__ == '__main__':
    main()
