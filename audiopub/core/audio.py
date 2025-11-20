import os
import subprocess
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from typing import List
import shutil

class AudioProcessor:
    def __init__(self, config):
        self.config = config

    def save_chunk(self, wav_data: np.ndarray, sample_rate: int, filepath: str):
        """Saves a numpy float32 array to a WAV file."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        sf.write(filepath, wav_data, sample_rate)

    def stitch_chunks(self, chunk_files: List[str], output_path: str, crossfade_ms: int = 50):
        """
        Stitches multiple WAV files into one with crossfade.
        """
        if not chunk_files:
            return

        combined = AudioSegment.from_wav(chunk_files[0])

        for f in chunk_files[1:]:
            next_seg = AudioSegment.from_wav(f)
            # Crossfade
            combined = combined.append(next_seg, crossfade=crossfade_ms)

        combined.export(output_path, format="wav")

    def create_m4b(self, chapter_files: List[dict], output_path: str, metadata: dict):
        """
        Muxes chapter WAVs into a single M4B (AAC) file with chapters.
        chapter_files: list of {'file': path, 'title': title}
        """
        # 1. Concatenate all chapters into one WAV (or feed to ffmpeg via concat demuxer)
        # Using concat demuxer is better for memory than loading huge AudioSegment

        concat_list_path = os.path.join(os.path.dirname(output_path), "files.txt")
        with open(concat_list_path, "w", encoding='utf-8') as f:
            for ch in chapter_files:
                # ffmpeg requires absolute paths or relative safely escaped
                abs_path = os.path.abspath(ch['file'])
                safe_path = abs_path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        # 2. Create FFMETADATA
        # We need to calculate start/end times for chapters
        metadata_path = os.path.join(os.path.dirname(output_path), "ffmetadata.txt")
        self._generate_ffmetadata(chapter_files, metadata_path, metadata)

        # 3. Run FFMPEG
        # ffmpeg -f concat -safe 0 -i files.txt -i ffmetadata.txt -map_metadata 1 -c:a aac -b:a 64k output.m4b
        cmd = [
            self.config.FFMPEG_BINARY,
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-i", metadata_path,
            "-map_metadata", "1",
            "-c:a", "aac",
            "-b:a", "64k", # Good enough for voice
            "-y",
            output_path
        ]

        print(f"Running ffmpeg: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        # Cleanup
        os.remove(concat_list_path)
        os.remove(metadata_path)

    def _generate_ffmetadata(self, chapter_files: List[dict], output_path: str, book_metadata: dict):
        """
        Calculates durations and writes FFMETADATA format.
        """
        content = ";FFMETADATA1\n"
        if 'title' in book_metadata:
            content += f"title={book_metadata['title']}\n"
        if 'author' in book_metadata:
            content += f"artist={book_metadata['author']}\n"

        current_time = 0

        for ch in chapter_files:
            # Get duration of file
            # We can use soundfile or pydub
            info = sf.info(ch['file'])
            duration_ms = int(info.duration * 1000)

            start = current_time
            end = current_time + duration_ms

            content += "[CHAPTER]\n"
            content += "TIMEBASE=1/1000\n"
            content += f"START={start}\n"
            content += f"END={end}\n"
            content += f"title={ch['title']}\n"

            current_time = end

        with open(output_path, "w", encoding='utf-8') as f:
            f.write(content)
