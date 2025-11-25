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

    def stitch_chunks(self, chunk_files: List[str], output_path: str, crossfade_ms: int = None, silence_ms: int = None):
        """
        Stitches multiple WAV files into one with crossfade and optional silence padding.
        """
        if crossfade_ms is None:
            crossfade_ms = self.config.CROSSFADE_MS
        if silence_ms is None:
            silence_ms = self.config.SILENCE_PADDING_MS
            
        if not chunk_files:
            return

        combined = AudioSegment.from_wav(chunk_files[0])
        
        # Create silence segment
        silence = AudioSegment.silent(duration=silence_ms)

        for f in chunk_files[1:]:
            next_seg = AudioSegment.from_wav(f)
            # Add silence, then crossfade into next segment
            combined = combined + silence
            combined = combined.append(next_seg, crossfade=crossfade_ms)

        combined.export(output_path, format="wav")

    def create_m4b(self, chapter_files: List[dict], output_path: str, metadata: dict, chapter_silence_ms: int = None):
        """
        Muxes chapter WAVs into a single M4B (AAC) file with chapters.
        chapter_files: list of {'file': path, 'title': title}
        """
        if chapter_silence_ms is None:
            chapter_silence_ms = self.config.CHAPTER_SILENCE_MS

        output_dir = os.path.dirname(output_path)

        silence_path = None
        silence_sample_rate = None
        if chapter_files:
            try:
                silence_sample_rate = sf.info(chapter_files[0]['file']).samplerate
            except Exception:
                silence_sample_rate = self.config.SAMPLE_RATE

        if chapter_files and chapter_silence_ms > 0:
            silence_path = os.path.join(output_dir, "chapter_silence.wav")
            AudioSegment.silent(
                duration=chapter_silence_ms,
                frame_rate=silence_sample_rate or self.config.SAMPLE_RATE
            ).export(silence_path, format="wav")
            # Use absolute path so ffmpeg concat resolves correctly
            silence_path = os.path.abspath(silence_path)

        # 1. Concatenate all chapters into one WAV (or feed to ffmpeg via concat demuxer)
        # Using concat demuxer is better for memory than loading huge AudioSegment

        concat_list_path = os.path.join(output_dir, "files.txt")
        with open(concat_list_path, "w", encoding='utf-8') as f:
            if silence_path:
                safe_silence = silence_path.replace("'", "'\\''")
                f.write(f"file '{safe_silence}'\n")  # Lead-in silence
            for idx, ch in enumerate(chapter_files):
                # ffmpeg requires absolute paths or relative safely escaped
                abs_path = os.path.abspath(ch['file'])
                safe_path = abs_path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
                if silence_path and idx < len(chapter_files) - 1:
                    f.write(f"file '{safe_silence}'\n")

        # 2. Create FFMETADATA
        # We need to calculate start/end times for chapters
        metadata_path = os.path.join(output_dir, "ffmetadata.txt")
        effective_silence = chapter_silence_ms if chapter_files else 0
        self._generate_ffmetadata(chapter_files, metadata_path, metadata, effective_silence)

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
            "-b:a", "192k", # Higher quality bitrate
            "-y",
            output_path
        ]

        print(f"Running ffmpeg: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        # Cleanup
        os.remove(concat_list_path)
        os.remove(metadata_path)
        if silence_path and os.path.exists(silence_path):
            os.remove(silence_path)

    def _generate_ffmetadata(self, chapter_files: List[dict], output_path: str, book_metadata: dict, chapter_silence_ms: int = 0):
        """
        Calculates durations and writes FFMETADATA format.
        """
        content = ";FFMETADATA1\n"
        if 'title' in book_metadata:
            content += f"title={book_metadata['title']}\n"
        if 'author' in book_metadata:
            content += f"artist={book_metadata['author']}\n"

        current_time = chapter_silence_ms  # lead-in silence before first chapter's audio

        total_chapters = len(chapter_files)
        for idx, ch in enumerate(chapter_files):
            # Get duration of file
            # We can use soundfile or pydub
            info = sf.info(ch['file'])
            duration_ms = int(info.duration * 1000)

            gap_before = chapter_silence_ms
            start = current_time - gap_before
            end = current_time + duration_ms
            gap_after = chapter_silence_ms if idx < total_chapters - 1 else 0

            content += "[CHAPTER]\n"
            content += "TIMEBASE=1/1000\n"
            content += f"START={start}\n"
            content += f"END={end}\n"
            content += f"title={ch['title']}\n"

            current_time = end + gap_after

        with open(output_path, "w", encoding='utf-8') as f:
            f.write(content)
