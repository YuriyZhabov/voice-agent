# 🎙️ Voice Agent

AI-powered voice agent for handling phone calls using LiveKit, with Russian language support.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![LiveKit](https://img.shields.io/badge/LiveKit-Agents-purple?logo=webrtc&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🗣️ **Voice Recognition** — Deepgram Nova-3 with Russian language support
- 🤖 **AI Conversations** — OpenAI GPT-4o-mini for natural dialogue
- 🔊 **Text-to-Speech** — ElevenLabs for high-quality voice synthesis
- 📞 **SIP Telephony** — LiveKit SIP for phone call integration
- ⏱️ **Smart Timeouts** — Automatic call termination on prolonged silence
- 🎯 **Interruption Handling** — Natural conversation flow with barge-in support

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Phone/SIP     │────▶│    LiveKit      │────▶│   Voice Agent   │
│   (Exolve)      │◀────│    Server       │◀────│   (Python)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                        ┌───────────────────────────────┼───────────────────────────────┐
                        │                               │                               │
                        ▼                               ▼                               ▼
                ┌───────────────┐              ┌───────────────┐              ┌───────────────┐
                │   Deepgram    │              │    OpenAI     │              │  ElevenLabs   │
                │   STT         │              │    LLM        │              │    TTS        │
                └───────────────┘              └───────────────┘              └───────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- LiveKit Cloud account
- API keys: Deepgram, OpenAI (or compatible), ElevenLabs

### Installation

```bash
# Clone the repository
git clone https://github.com/YuriyZhabov/voice-agent.git
cd voice-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `DEEPGRAM_API_KEY` | Deepgram API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `ELEVEN_API_KEY` | ElevenLabs API key |

### Running the Agent

```bash
# Development mode with hot reload
python -m agent.main dev

# Production mode
python -m agent.main start
```

### Testing via WebRTC

```bash
# Generate test room link
python -m agent.test_webrtc

# Open the link in browser and start talking!
```

## 📁 Project Structure

```
voice-agent/
├── agent/
│   ├── main.py          # Agent entry point
│   ├── config.py        # Pydantic configuration
│   ├── context.py       # Conversation context manager
│   ├── logger.py        # Call logging
│   ├── sip_setup.py     # SIP trunk management
│   └── test_webrtc.py   # WebRTC testing utility
├── tests/               # Unit tests
├── .env.example         # Environment template
├── requirements.txt     # Dependencies
└── pyproject.toml       # Project metadata
```

## 🔧 Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `AGENT_NAME` | `voice-agent-mvp` | Agent identifier for dispatch |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model to use |
| `ELEVENLABS_VOICE_ID` | `21m00Tcm4TlvDq8ikWAM` | Voice for TTS |
| `SILENCE_TIMEOUT_SECONDS` | `30` | Seconds before timeout |
| `MAX_CONTEXT_MESSAGES` | `20` | Conversation history limit |

## 📞 SIP Telephony Setup

For phone call integration with MTS Exolve:

1. Create LiveKit SIP trunks:
```bash
python -m agent.sip_setup --create-inbound --name "Inbound" --number "+7XXXXXXXXXX"
python -m agent.sip_setup --create-dispatch --name "Dispatch" --prefix "call-"
```

2. Configure Exolve forwarding to LiveKit SIP URI

3. Test outbound calls:
```bash
python -m agent.test_call +79001234567
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=agent --cov-report=html
```

## �  Archon Integration

This project includes integration with [Archon](https://github.com/coleam00/archon) for AI agent management.

### CometAPI LLM Wrapper

```python
from archon.cometapi_llm import CometapiLLM

llm = CometapiLLM(
    api_key="your-cometapi-key",
    api_url="https://api.cometapi.com/v1",
    model="gpt-4o-mini"
)

response = llm.invoke("Hello, how are you?")
```

## 🛣️ Roadmap

- [x] Voice agent MVP
- [x] WebRTC testing
- [x] SIP telephony configuration
- [x] Archon integration with CometAPI
- [ ] n8n integration for dynamic tools
- [ ] Warm transfer to human operators
- [ ] RAG knowledge base
- [ ] Multi-agent handoff

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Built with ❤️ using [LiveKit Agents](https://docs.livekit.io/agents/)
