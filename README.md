# Hand-Gesture-Based-Video-Navigator Demo

Use your webcam and MediaPipe to control media on your PC via hand gestures.

Key behaviors:
- Play/Pause: sends the system Play/Pause media key (works with most players).
- Fast forward / Rewind: sends Right/Left arrow keys (seeks a few seconds in browsers and many players).
- The MediaPipe Tasks hand-landmarker model is downloaded automatically to `hand_landmarker.task` when needed.

## Virtual environment
This project uses a local virtual environment named `.venv`.

### Activate (examples)
- Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

- Windows (CMD):

```cmd
.venv\Scripts\activate
```

- To deactivate:

```bash
deactivate
```

## Install dependencies
With the venv activated, install pinned dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Notes:
- The `requirements.txt` includes optional WinRT projection packages used to read the system media state on Windows. On some setups those WinRT wheels are published as `winrt-Windows.*` packages; if `pip install -r requirements.txt` fails for WinRT, try:

```powershell
python -m pip install winrt-Windows.Media.Control winrt-Windows.Media winrt-Windows.Foundation winrt-runtime
```

## Run
Run the gesture controller (webcam required):

```bash
python newModel.py
```

Place an optional sample video `SampleVideo.mp4` in the project folder if you want to test VLC-specific playback, but global media keys work with any media player.

## Troubleshooting
- No webcam image: ensure no other app is using the camera and allow camera permissions.
- Media keys not working: confirm your media app responds to Play/Pause and arrow keys; some apps ignore global media keys.
- WinRT errors: install the WinRT projection packages as shown above and use Python 3.10.

If you want, I can add a short troubleshooting section for specific players (YouTube, VLC, Spotify).
