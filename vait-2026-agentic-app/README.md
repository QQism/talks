# Building Agentic AI Applications: From Zero to Multi-Agent Systems

The code from the talk by [Quang Quach](https://qnq.io). We build one personal assistant step by step, from a single model call to a team of agents, with [Strands Agents](https://strandsagents.com). Its first job: plan a family trip to Japan.

Every step is its own folder and runs on its own. You can chat with any step in the terminal, or open the presenter app used in the talk to see the code, the chat and what happens under the hood side by side.

*First presented at the Vietnamese Aussies IT community.*

## What's inside

| Section | What it adds |
|---|---|
| **1. Foundations** | |
| 1.1 Raw model call | One request, one response, straight to the Claude API. It forgets everything between calls. |
| 1.2 First agent | A Strands `Agent`: it keeps the conversation and re-sends it on every call. |
| 1.3 System prompt | A job description for the assistant. |
| 1.4 Streaming | The answer appears as it's generated. |
| 1.5 Thinking | The model reasons before it answers, and you can read its notes. |
| **2. Tools & skills** | |
| 2.1 Tools | Python functions the model can ask for: the date, the weather, attractions, restaurants. |
| 2.2 Skills | Know-how in Markdown (`SKILL.md`), loaded only when it's needed. |
| **3. Going further** | |
| 3.1 Specialist team | Several agents in a graph: three specialists in parallel, then a writer. |
| 3.2 Structured output | The plan as typed data (a Pydantic model), rendered as cards. |
| 3.3 Photo input | A photo and a question in the same message. |

```
chapters.toml        the talk outline: sections in order, their scripted prompts
chapters/            one folder per section (agent.py, plus tools.py, models.py, skills/ where needed)
common/model.py      picks the model provider from .env
common/data.py       mock weather, attractions, restaurants, flights, hotels (Kyoto always rains)
app.py               the presenter app (Streamlit)
```

## Setup

You need **Python 3.12** and access to one model provider: a **Claude API key** (simplest), **Amazon Bedrock**, or **OpenAI**.

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then edit .env
```

In `.env`, set `PROVIDER` and fill in that provider's block:

| Provider | Settings | Default model |
|---|---|---|
| `anthropic` | `ANTHROPIC_API_KEY` (from [console.anthropic.com](https://console.anthropic.com)) | Claude Sonnet 5.5 |
| `bedrock` | `AWS_PROFILE`, `AWS_REGION`, and access to the model in that region | Claude Sonnet 5.5 (global inference profile) |
| `openai` | `OPENAI_API_KEY` | GPT-5 |

Set `MODEL_ID` to use a different model. Section **1.1** always calls the Claude API directly, so it needs `ANTHROPIC_API_KEY` whatever `PROVIDER` says; every other section follows `PROVIDER`. Thinking (1.5 onward) works with Claude and is ignored for OpenAI.

`.env` holds your keys: keep it out of git (it's in `.gitignore`) and never share it.

## Run a section in the terminal

From the repository root, with the virtual environment active, run a section's `agent.py` as a module:

```bash
python -m chapters.01_foundations.02_first_agent.agent
```

Then type at the `>` prompt. Press **Ctrl+C** to quit. Some sections to try:

```bash
python -m chapters.01_foundations.01_raw_model.agent       # it can't remember your name
python -m chapters.02_tools_and_skills.01_tools.agent      # "What's the weather in Kyoto this Saturday?"
python -m chapters.02_tools_and_skills.02_skills.agent     # "Plan a trip for my family"
python -m chapters.03_going_further.01_specialist_team.agent
```

The scripted prompts from the talk are in `chapters.toml`, under each section's `prompts`.

## Run the presenter app

```bash
streamlit run app.py
```

Then open <http://localhost:8501>. The app only listens on your own machine (`address = "127.0.0.1"` in `.streamlit/config.toml`). Keep it that way: anyone who can reach it can use your API key.

- **Navigate** with the chapter blocks at the top (click one to pick a section), or with the bars on the left and right edges of the screen. Each section has its own address, so a refresh stays on it.
- **Code** is on the left. The switch above it shows the diff against the previous section or the whole file; the tabs switch files.
- **Chat** is on the right. Click the empty chat box for the talk's scripted prompts, or type your own. In 3.3 you can attach a photo.
- **Under the hood:** click the bar at the bottom for a diagram of what was actually sent to the model, plus a trace of every model and tool call.
- **Edit live:** ✎ on a file tab lets you change a section's code or a `SKILL.md`, and **▶ Run** rebuilds the agent with your change while keeping the conversation. Edits live in memory only; to keep them, change the files themselves, and the app reloads them on save.

## Your turn

Make the assistant yours. Start from 2.2 Skills (`chapters/02_tools_and_skills/02_skills`) and add:

1. **Skills for your day:** check your calendar, plan your day's to-do list. A skill is a folder with a `SKILL.md`; give it the tools it needs to reach your data, or connect them through an MCP server.
2. **Memory across sessions:** continue yesterday's conversation, and remember facts about you. Look at Strands session managers and memory.
3. **Permission control:** safe actions run on their own, risky actions wait for your approval. A prompt asking nicely isn't enough; enforce it in code, for example with a hook that runs before every tool call.

The [Strands Agents docs](https://strandsagents.com) cover each of these.

## Credits

- Photos: Wikimedia Commons, see `assets/photos/CREDITS.md`.
- Fonts: [ET Book](https://github.com/edwardtufte/et-book) (MIT) and [Cascadia Code](https://github.com/microsoft/cascadia-code) (SIL Open Font License 1.1); licenses in `static/fonts/`.
- Restaurant, weather, flight and hotel data in `common/data.py` is made up for the demo.
