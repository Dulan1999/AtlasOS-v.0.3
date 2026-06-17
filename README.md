AtlasOS

Recommended first-time setup:

1. Go to /Atlas-v.03-master/dist/
2. Launch AtlasOS.exe.
3. Follow the setup window:
   - Enter your name.
   - Choose Atlas's name.
   - Keep qwen2.5:7b or enter another Ollama model.
   - Click Check Ollama.
   - Click Pull Model if the model is not installed.
   - Click Finish Setup.

AtlasOS stores config and memory in:

%APPDATA%\AtlasOS

Requirements for end users:

- Ollama installed
- qwen2.5:7b or another local Ollama model
- Microphone for voice input
- Speakers or headphones for speech output
- Windows recommended

If Ollama is not installed, use the Get Ollama button in AtlasOS setup.

Developer setup from source:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull qwen2.5:7b

Run terminal mode:

python main.py

Run desktop mode:

python app.py

Build the Windows app:

pyinstaller AtlasOS.spec

Then rebuild the installer with installer\AtlasOS.iss.
