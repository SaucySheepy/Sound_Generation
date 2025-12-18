import sounddevice as sd
import numpy as np 
from app.app.engine import StringModel

def main() -> None:
    fs = 44100
    guitar = StringModel(sample_rate=fs, frequency =440.0, decay_factor=0.99)

    print("Plucking string")
    guitar.pluck()

    def callback(outdata,frames, time ,status):
        if status:
            print(status)

        audio_block = guitar.process_block(frames)
        outdata[:] = audio_block.reshape(-1,1)

    with sd.OutputStream(channels = 1, samplerate=fs, callback=callback):
        print("Press Enter to quit ")
        input()

if __name__ == "__main__":
    main() 