import os
import asyncio
from nicegui import ui, app, run
from audiopub import config
from audiopub.core.worker import Worker
from audiopub.file_picker import LocalFilePicker
import glob
import html
import secrets
import sys
import threading
import time
from fastapi.responses import FileResponse
from fastapi import HTTPException

# --- Globals ---
worker = Worker()
served_outputs = {}

# --- Logic ---

def get_voices():
    """Scans assets directory for voice files based on selected TTS engine."""
    voices = []
    seen = set()

    # Determine file extension based on engine
    if config.TTS_ENGINE.lower() in ["neutts-air", "neutts_air"]:
        # For NeuTTS Air, look for WAV files with accompanying TXT files
        # Scan in assets/voices/ or assets/reference_audio/
        search_dirs = [
            os.path.join(config.ASSETS_DIR, "voices"),
            os.path.join(config.ASSETS_DIR, "reference_audio"),
            config.ASSETS_DIR
        ]

        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue

            for f in glob.glob(os.path.join(search_dir, "**", "*.wav"), recursive=True):
                if f in seen:
                    continue
                seen.add(f)

                # Check if there's a matching .txt file
                txt_file = f.rsplit('.', 1)[0] + '.txt'
                if os.path.exists(txt_file):
                    voices.append(f)
                else:
                    # Warn but still include (will error later if used)
                    voices.append(f)
    else:
        # For Supertonic and other engines, look for JSON voice styles
        search_paths = [
            os.path.join(config.ASSETS_DIR, "*.json"),
            os.path.join(config.ASSETS_DIR, "**", "*.json")
        ]

        for path in search_paths:
            for f in glob.glob(path, recursive=True):
                if f.endswith("tts.json") or f.endswith("unicode_indexer.json") or f.endswith("config.json"):
                    continue # Skip config files
                if f in seen:
                    continue
                seen.add(f)

                # Check if it looks like a voice style
                voices.append(f)

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

@app.get('/media/{token}')
def serve_output(token: str):
    """Serve generated audio by token."""
    path = served_outputs.get(token)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(path, media_type='audio/mp4', filename=os.path.basename(path))

@app.post('/restart')
def restart_server():
    """Restart the NiceGUI server process."""
    def _restart():
        time.sleep(0.3)
        python = sys.executable
        os.execv(python, [python, "-m", "audiopub.main"])

    threading.Thread(target=_restart, daemon=True).start()
    return {"status": "restarting"}

# --- UI ---

@ui.page('/')
def index():
    # State
    state = {
        'epub_path': '',
        'output_dir': config.OUTPUT_DIR,
        'selected_voice': None,
        'is_processing': False,
        'last_output_token': None,
        'last_output_path': None
    }
    last_token_holder = {'token': None}

    # Fonts and Styles
    ui.add_head_html('''
        <script>
            (function() {
                const reloadKey = 'audiopub_autoscale_reload';
                if (!sessionStorage.getItem(reloadKey)) {
                    sessionStorage.setItem(reloadKey, '1');
                    // One-time reload to fix initial layout scaling
                    window.addEventListener('load', () => setTimeout(() => location.reload(), 50));
                } else {
                    sessionStorage.removeItem(reloadKey);
                    // Trigger a resize to settle layout on the final load
                    window.addEventListener('load', () => window.dispatchEvent(new Event('resize')));
                }
            })();
        </script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Inter', sans-serif;
                background-color: #020617; /* slate-950 */
                color: #e2e8f0; /* slate-200 */
            }
            .glass-panel {
                background: rgba(15, 23, 42, 0.7);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(148, 163, 184, 0.1);
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }
            .terminal-container {
                background-color: #0a0a0a;
                background-image: radial-gradient(#1e293b 1px, transparent 1px);
                background-size: 20px 20px;
                border: 1px solid #334155;
                box-shadow: inset 0 0 40px rgba(0,0,0,0.8);
            }
            .neon-text {
                color: #22d3ee; /* cyan-400 */
                text-shadow: 0 0 5px rgba(34, 211, 238, 0.3);
                font-family: 'JetBrains Mono', monospace;
            }
            .input-dark .q-field__control {
                background: rgba(2, 6, 23, 0.5) !important;
            }
        </style>
    ''')

    # Brand Colors
    ui.colors(
        primary='#8b5cf6',  # Violet
        secondary='#06b6d4', # Cyan
        accent='#d946ef',   # Fuchsia
        dark='#020617',     # Slate-950
        positive='#10b981', # Emerald
        negative='#ef4444', # Red
        info='#3b82f6',     # Blue
        warning='#f59e0b'   # Amber
    )

    log_scroll = None
    log_element = None
    progress_bar = None
    audio_player = None
    player_label = None
    log_content = ""

    # Callbacks
    def update_log(msg):
        nonlocal log_content
        log_content += msg + "\n"
        if log_element:
            # Escape html to be safe
            safe_content = html.escape(log_content)
            log_element.set_content(f"<div class='whitespace-pre-wrap'>{safe_content}</div>")
            if log_scroll:
                log_scroll.scroll_to(percent=1.0)

    def update_progress(val):
        if progress_bar:
            progress_bar.set_value(val)

    worker.log_callback = update_log
    worker.progress_callback = update_progress

    def pick_epub():
        def on_pick(path):
            state['epub_path'] = path
            epub_input.set_value(path)

        start_dir = os.path.dirname(state['epub_path']) if state['epub_path'] and os.path.exists(os.path.dirname(state['epub_path'])) else '.'
        picker = LocalFilePicker(
            directory=start_dir,
            on_select=on_pick,
            mode='file'
        )
        picker.set_extension_filter('.epub')
        picker.open()

    def pick_output():
        def on_pick(path):
            state['output_dir'] = path
            out_input.set_value(path)

        start_dir = state['output_dir'] if state['output_dir'] and os.path.exists(state['output_dir']) else '.'
        picker = LocalFilePicker(
            directory=start_dir,
            on_select=on_pick,
            mode='dir'
        )
        picker.open()

    async def trigger_restart():
        ui.notify('Restarting server...', type='warning', icon='refresh')
        await ui.run_javascript("fetch('/restart', {method:'POST'}).then(() => setTimeout(() => location.reload(), 1200));")

    async def start_conversion():
        nonlocal audio_player, player_label
        if not state['epub_path']:
            ui.notify('Please select an EPUB file.', type='warning', icon='warning')
            return
        if not state['output_dir']:
            ui.notify('Please select an output directory.', type='warning', icon='warning')
            return
        if not state['selected_voice']:
            ui.notify('Please select a voice.', type='warning', icon='warning')
            return

        book_name = os.path.splitext(os.path.basename(state['epub_path']))[0]
        final_output = os.path.join(state['output_dir'], book_name + ".m4b")

        state['is_processing'] = True
        progress_bar.set_value(0)
        update_log("\n--- Starting Conversion ---\n")

        await worker.run_conversion(state['epub_path'], state['output_dir'], state['selected_voice'])

        state['is_processing'] = False
        ui.notify('Process finished.', type='positive', icon='check')
        if os.path.exists(final_output):
            if last_token_holder['token']:
                served_outputs.pop(last_token_holder['token'], None)
            token = secrets.token_urlsafe(8)
            served_outputs[token] = final_output
            last_token_holder['token'] = token
            state['last_output_token'] = token
            state['last_output_path'] = final_output
            source = f"/media/{token}"
            if audio_player:
                audio_player.set_source(source)
            if player_label:
                player_label.set_text(f"Ready: {os.path.basename(final_output)}")
            update_log(f"\n--- Preview ready: {final_output} ---\n")
            ui.notify('Preview ready. Use the player to listen.', type='positive', icon='play_arrow')
        else:
            ui.notify('Output file not found for playback.', type='warning', icon='warning')

    def stop_conversion():
        worker.stop()
        update_log("\n[Stopping requested...]\n")

    # --- Layout Construction ---

    # Main container
    with ui.element('div').classes('w-full h-screen flex flex-row overflow-hidden bg-slate-950'):

        # Left: Floating Glass Card (Controls)
        with ui.column().classes('w-96 m-6 p-6 rounded-3xl glass-panel z-10 flex flex-col gap-6 shrink-0 transition-all duration-300 hover:shadow-violet-900/20'):

            # Header
            with ui.row().classes('items-center gap-2 mb-2'):
                 ui.icon('graphic_eq', size='md', color='secondary').classes('animate-pulse')
                 ui.label('AUDIOPUB').classes('text-2xl font-bold tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-cyan-400')

            # LFS Check
            lfs_ok, lfs_msg = check_lfs()
            if not lfs_ok:
                with ui.row().classes('w-full bg-red-900/30 border border-red-500/50 p-3 rounded-lg items-center gap-2'):
                    ui.icon('error', color='negative')
                    ui.label(lfs_msg).classes('text-red-200 text-xs leading-tight flex-grow')

            # Inputs
            with ui.column().classes('w-full gap-4'):

                # EPUB
                with ui.column().classes('w-full gap-1'):
                    ui.label('SOURCE FILE').classes('text-xs font-bold text-slate-500 tracking-widest')
                    with ui.row().classes('w-full gap-2'):
                        epub_input = ui.input(value=state['epub_path'], placeholder='/path/to/book.epub') \
                            .bind_value(state, 'epub_path') \
                            .props('outlined rounded dense dark color="secondary" bg-color="transparent"') \
                            .classes('flex-grow input-dark font-mono text-sm')
                        with epub_input.add_slot('prepend'):
                            ui.icon('book', color='slate-400')
                        ui.button(icon='folder_open', on_click=pick_epub) \
                            .props('unelevated dense color="slate-800"') \
                            .classes('aspect-square')

                # OUTPUT
                with ui.column().classes('w-full gap-1'):
                    ui.label('OUTPUT DESTINATION').classes('text-xs font-bold text-slate-500 tracking-widest')
                    with ui.row().classes('w-full gap-2'):
                        out_input = ui.input(value=state['output_dir'], placeholder='/output/path') \
                            .bind_value(state, 'output_dir') \
                            .props('outlined rounded dense dark color="secondary" bg-color="transparent"') \
                            .classes('flex-grow input-dark font-mono text-sm')
                        with out_input.add_slot('prepend'):
                            ui.icon('folder', color='slate-400')
                        ui.button(icon='folder_open', on_click=pick_output) \
                            .props('unelevated dense color="slate-800"') \
                            .classes('aspect-square')

                # VOICE
                with ui.column().classes('w-full gap-1'):
                    ui.label('NEURAL VOICE').classes('text-xs font-bold text-slate-500 tracking-widest')
                    voices = get_voices()
                    # map full path to basename for display, beautified
                    voice_options = {v: os.path.basename(v).replace('.json', '').replace('_', ' ').title() for v in voices}

                    voice_select = ui.select(options=voice_options, value=state['selected_voice']) \
                        .bind_value(state, 'selected_voice') \
                        .props('outlined rounded dense dark color="secondary" behavior="menu" options-dense popup-content-class="bg-slate-900 text-slate-200 border border-slate-700"') \
                        .classes('w-full font-medium')
                    with voice_select.add_slot('prepend'):
                         ui.icon('record_voice_over', color='slate-400')

                # Playback
                with ui.column().classes('w-full gap-1'):
                    ui.label('PLAYBACK').classes('text-xs font-bold text-slate-500 tracking-widest')
                    player_label = ui.label('No recent output yet').classes('text-sm text-slate-400')
                    audio_player = ui.audio(src="").props('controls preload="metadata"') \
                        .classes('w-full rounded-lg shadow-inner shadow-black/20')

            ui.separator().classes('bg-slate-700/50')

            # Actions
            with ui.column().classes('w-full gap-3 mt-auto'):

                # Progress Bar
                ui.label('STATUS').classes('text-xs font-bold text-slate-500 tracking-widest')
                progress_bar = ui.linear_progress(value=0, show_value=False) \
                    .props('track-color="slate-800" color="secondary" size="6px" rounded') \
                    .classes('w-full shadow-lg shadow-cyan-900/50')

                with ui.row().classes('w-full gap-3 pt-2'):
                    # Start Button
                    ui.button('GENERATE AUDIO', on_click=start_conversion) \
                        .bind_enabled_from(state, 'is_processing', backward=lambda x: not x) \
                        .props('unelevated no-caps') \
                        .classes('flex-grow bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white font-bold rounded-xl shadow-lg shadow-violet-900/20 transition-all py-3')

                    # Stop Button
                    ui.button(icon='stop', on_click=stop_conversion) \
                        .bind_enabled_from(state, 'is_processing') \
                        .props('unelevated round dense color="negative"') \
                        .classes('shadow-lg shadow-red-900/20 opacity-80 hover:opacity-100')

                ui.button('RESTART SERVER', on_click=trigger_restart) \
                    .props('outline color=\"warning\" icon=\"refresh\"') \
                    .classes('self-stretch')

        # Right: Terminal (Logs)
        with ui.column().classes('flex-grow m-6 ml-0 rounded-3xl terminal-container overflow-hidden relative flex flex-col shadow-2xl'):
            # Terminal Header
            with ui.row().classes('w-full bg-slate-900/80 border-b border-slate-800 p-3 items-center gap-2 px-4'):
                with ui.row().classes('gap-1.5'):
                    ui.element('div').classes('w-3 h-3 rounded-full bg-red-500/80')
                    ui.element('div').classes('w-3 h-3 rounded-full bg-yellow-500/80')
                    ui.element('div').classes('w-3 h-3 rounded-full bg-green-500/80')
                ui.label('system_log.sh').classes('text-xs font-mono text-slate-500 ml-2')
                ui.space()
                ui.label('v1.0.0').classes('text-xs font-mono text-slate-600')

            # Log Content
            log_scroll = ui.scroll_area().classes('w-full flex-grow p-6 font-mono text-sm')
            with log_scroll:
                log_element = ui.html('', sanitize=False).classes('neon-text text-sm leading-relaxed whitespace-pre-wrap')
                # Init with welcome message
                update_log("> System initialized.")
                update_log("> Ready to process.")

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Audiopub', reload=False)
