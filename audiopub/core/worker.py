import asyncio
import logging
import os
import shutil
import time
import secrets
import hashlib
from typing import Callable, Optional
import traceback

from audiopub import config
from audiopub.core.tts_factory import create_tts_engine
from audiopub.core.epub import EpubParser
from audiopub.core.audio import AudioProcessor

class Worker:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback
        self.running = False
        self.cancel_event = asyncio.Event()
        self.progress_callback = None # function(float)

    def log(self, message: str):
        print(message)
        if self.log_callback:
            self.log_callback(message)

    def set_progress(self, value: float):
        if self.progress_callback:
            self.progress_callback(value)

    async def run_conversion(self, epub_path: str, output_dir: str, voice_path: str):
        """
        Main orchestration logic.
        """
        self.running = True
        self.cancel_event.clear()
        self.log(f"Starting conversion for {os.path.basename(epub_path)}")

        book_name = os.path.splitext(os.path.basename(epub_path))[0]
        temp_dir_base = os.path.join(output_dir, "temp_work")
        os.makedirs(temp_dir_base, exist_ok=True)

        voice_id = os.path.splitext(os.path.basename(voice_path))[0]
        entropy = f"{book_name}|{voice_id}|{time.time()}|{secrets.token_hex(4)}"
        generation_id = hashlib.sha1(entropy.encode()).hexdigest()[:8]
        temp_dir = os.path.join(temp_dir_base, f"{book_name}_{generation_id}")
        os.makedirs(temp_dir, exist_ok=True)
        self.log(f"Using temp directory: {temp_dir}")

        final_output = os.path.join(output_dir, book_name + ".m4b")

        try:
            # 1. Parse EPUB
            self.log("Parsing EPUB...")
            parser = EpubParser(epub_path)
            chapters = await asyncio.to_thread(parser.extract_text)

            self.log(f"Found {len(chapters)} chapters/sections.")

            # 2. Initialize TTS
            self.log(f"Initializing TTS Model ({config.TTS_ENGINE})...")
            tts = create_tts_engine(config.TTS_ENGINE, config.ASSETS_DIR)
            # We run load in a thread because it might block
            await asyncio.to_thread(tts.load)
            await asyncio.to_thread(tts.set_voice, voice_path)

            self.log("Warming up TTS...")
            await asyncio.to_thread(tts.warm_up)

            audio_processor = AudioProcessor(config)
            chapter_wavs = []

            total_chapters = len(chapters)

            # 3. Loop through chapters
            for i, chapter in enumerate(chapters):
                if self.cancel_event.is_set():
                    self.log("Conversion cancelled.")
                    return

                chapter_title = chapter['title']
                safe_title = "".join([c for c in chapter_title if c.isalnum() or c in (' ', '-', '_')]).strip()
                chapter_dir = os.path.join(temp_dir, f"ch_{i:03d}_{safe_title}")
                os.makedirs(chapter_dir, exist_ok=True)

                chapter_wav_path = os.path.join(temp_dir, f"ch_{i:03d}.wav")

                # Resume Check: If chapter wav exists, skip
                if os.path.exists(chapter_wav_path):
                     self.log(f"Skipping Chapter {i+1} (Already complete)")
                     chapter_wavs.append({'file': chapter_wav_path, 'title': chapter_title})
                     self.set_progress((i + 1) / total_chapters)
                     continue

                self.log(f"Processing Chapter {i+1}/{total_chapters}: {chapter_title}")

                text = chapter['content']
                chunks = parser.chunk_text(text)
                chunk_files = []

                for j, chunk in enumerate(chunks):
                    if self.cancel_event.is_set(): return

                    chunk_filename = f"chunk_{j:04d}.wav"
                    chunk_path = os.path.join(chapter_dir, chunk_filename)

                    # Resume Check for chunks
                    if os.path.exists(chunk_path):
                        # self.log(f"  Skipping chunk {j+1}...")
                        chunk_files.append(chunk_path)
                        continue

                    self.log(f"  Synthesizing chunk {j+1}/{len(chunks)}...")

                    # Synthesize (CPU heavy, run in thread)
                    try:
                        wav_data, sr = await asyncio.to_thread(tts.synthesize, chunk)
                        await asyncio.to_thread(audio_processor.save_chunk, wav_data, sr, chunk_path)
                        chunk_files.append(chunk_path)
                    except Exception as e:
                        self.log(f"  Error on chunk {j+1}: {e}")
                        # If a chunk fails, we might abort or skip. Aborting is safer.
                        raise e

                    # Optional: free memory if needed, though python GC should handle it.
                    # Only explicit clear if we accumulate huge lists.

                self.log(f"Stitching Chapter {i+1}...")
                await asyncio.to_thread(audio_processor.stitch_chunks, chunk_files, chapter_wav_path)

                # Cleanup chunks to save space? Optional.
                # shutil.rmtree(chapter_dir)

                chapter_wavs.append({'file': chapter_wav_path, 'title': chapter_title})
                self.set_progress((i + 1) / total_chapters)

            # 4. Mux to M4B
            if self.cancel_event.is_set(): return
            self.log("Muxing final audiobook...")

            metadata = {'title': parser.book.title or "Unknown", 'author': "Unknown"} # TODO: extract metadata better
            await asyncio.to_thread(audio_processor.create_m4b, chapter_wavs, final_output, metadata)

            self.log(f"Conversion Complete! Saved to {final_output}")

        except Exception as e:
            self.log(f"Error: {str(e)}")
            logging.exception("Conversion failed")
            traceback.print_exc()
        finally:
            self.running = False

    def stop(self):
        if self.running:
            self.log("Stopping...")
            self.cancel_event.set()
