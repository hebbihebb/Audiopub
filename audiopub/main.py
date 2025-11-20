import os
import asyncio
from nicegui import ui, app, run
from audiopub import config
from audiopub.core.worker import Worker
import glob

# --- Globals ---
worker = Worker()

# --- Logic ---

def get_voices():
    """Scans assets directory for voice style JSONs."""
    # We look for JSON files that have 'style_ttl' and 'style_dp' keys ideally,
    # or just list all JSONs in assets/voice_styles or root assets.
    # Based on prompt: "User provided models" in assets/.
    # We'll look recursively or just in root/voice_styles subfolder if it exists.

    # Assuming user dumps .json styles in assets/ or assets/styles/
    search_paths = [
        os.path.join(config.ASSETS_DIR, "*.json"),
        os.path.join(config.ASSETS_DIR, "**", "*.json")
    ]

    voices = []
    seen = set()

    for path in search_paths:
        for f in glob.glob(path, recursive=True):
            if f.endswith("tts.json") or f.endswith("unicode_indexer.json"):
                continue # Skip config files
            if f in seen: continue
            seen.add(f)

            # Check if it looks like a voice style (simple check)
            try:
                # reading every json might be slow, maybe just name?
                # For now, trust the user or check file size (styles are small).
                voices.append(f)
            except:
                pass

    return sorted(voices)

def check_lfs():
    """Checks if ONNX models in assets are large enough."""
    onnx_files = glob.glob(os.path.join(config.ASSETS_DIR, "**", "*.onnx"), recursive=True)
    if not onnx_files:
         # Might not be set up yet
         return False, "No ONNX models found in assets."

    for f in onnx_files:
        try:
            with open(f, 'rb') as file:
                header = file.read(100)
                if b'version https://git-lfs.github.com/spec/v1' in header:
                    return False, f"File {os.path.basename(f)} is a Git LFS pointer. Please run 'git lfs pull'."
        except:
            pass

    return True, "OK"

# --- UI ---

@ui.page('/')
def index():
    # State
    state = {
        'epub_path': '',
        'output_dir': config.OUTPUT_DIR,
        'selected_voice': None,
        'is_processing': False
    }

    log_content = ""
    log_element = None
    progress_bar = None

    def update_log(msg):
        nonlocal log_content
        log_content += msg + "\n"
        if log_element:
            log_element.set_content(f"<pre>{log_content}</pre>")
            log_element.run_method('scrollTo', 0, 999999)

    def update_progress(val):
        if progress_bar:
            progress_bar.set_value(val)

    worker.log_callback = update_log
    worker.progress_callback = update_progress

    async def start_conversion():
        if not state['epub_path']:
            ui.notify('Please select an EPUB file.', type='warning')
            return
        if not state['output_dir']:
            ui.notify('Please select an output directory.', type='warning')
            return
        if not state['selected_voice']:
            ui.notify('Please select a voice.', type='warning')
            return

        state['is_processing'] = True
        progress_bar.set_value(0)
        update_log("--- Starting Conversion ---\n")

        await worker.run_conversion(state['epub_path'], state['output_dir'], state['selected_voice'])

        state['is_processing'] = False
        ui.notify('Process finished (check logs).')

    def stop_conversion():
        worker.stop()
        update_log("\n[Stopping requested...]\n")

    # Layout
    with ui.row().classes('w-full h-screen no-wrap'):

        # Left Panel (Controls)
        with ui.column().classes('w-1/3 p-4 bg-gray-100 h-full gap-4'):
            ui.label('Audiopub').classes('text-2xl font-bold mb-4')

            # LFS Check
            lfs_ok, lfs_msg = check_lfs()
            if not lfs_ok:
                ui.label('LFS Error:').classes('text-red-500 font-bold')
                ui.label(lfs_msg).classes('text-red-500 text-sm')

            # File Inputs
            ui.label('EPUB File:')
            with ui.row().classes('w-full items-center'):
                ui.input(value=state['epub_path']).bind_value(state, 'epub_path').classes('flex-grow')
                # File picker button not native simple, using simple input for now or nicegui native file picker
                # We'll use a simple notify to type path for now, or a dialog?
                # NiceGUI has ui.upload but for local app we can use native file dialog if possible,
                # but web-based UI usually requires upload.
                # Since this is a "desktop app" (presumably running locally), we can just type path or implement a picker.
                # I'll stick to text input for simplicity in "desktop" mode unless requested.

            ui.label('Output Directory:')
            ui.input(value=state['output_dir']).bind_value(state, 'output_dir').classes('w-full')

            # Voice Selector
            ui.label('Voice:')
            voices = get_voices()
            # map full path to basename for display
            voice_options = {v: os.path.basename(v) for v in voices}
            ui.select(options=voice_options, value=state['selected_voice']).bind_value(state, 'selected_voice').classes('w-full')

            ui.separator()

            # Buttons
            with ui.row().classes('w-full gap-2'):
                ui.button('Start Conversion', on_click=start_conversion)\
                    .bind_enabled_from(state, 'is_processing', backward=lambda x: not x)\
                    .classes('flex-grow bg-blue-600 text-white')

                ui.button('Stop', on_click=stop_conversion)\
                    .bind_enabled_from(state, 'is_processing')\
                    .classes('bg-red-500 text-white')

            # Progress
            progress_bar = ui.linear_progress(value=0).classes('w-full mt-4')

        # Right Panel (Logs)
        with ui.column().classes('w-2/3 p-4 h-full bg-black text-white'):
            ui.label('Logs').classes('text-xl font-bold mb-2')
            # Scrollable log area
            with ui.scroll_area().classes('w-full h-full border border-gray-700 p-2 rounded'):
                log_element = ui.html('<pre></pre>', sanitize=False).classes('font-mono text-sm')

ui.run(title='Audiopub', reload=False)
