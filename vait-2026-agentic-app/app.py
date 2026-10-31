"""Presenter UI: files + code | chat, with trace and context below.

Run with `streamlit run app.py`. The outline comes from chapters.toml.
"""

import asyncio
import copy
import importlib.abc
import importlib.util
import sys
import uuid
import difflib
import importlib
import base64
import html
import json
import re
import os
import time
import tomllib
from pathlib import Path

import streamlit as st
from code_editor import code_editor
from strands.vended_plugins.skills import Skill
from dotenv import load_dotenv
from strands.hooks import (
    AfterModelCallEvent,
    AfterToolCallEvent,
    BeforeModelCallEvent,
    BeforeToolCallEvent,
)

load_dotenv()
PROVIDER = os.environ.get("PROVIDER", "bedrock").lower()
OUTLINE = tomllib.loads(Path("chapters.toml").read_text())["chapter"]
CHAPTER_NUMBERS = {}  # only numbered chapters count: the intro and closing slides have no number
for chapter in OUTLINE:
    if chapter.get("numbered", True):
        CHAPTER_NUMBERS[chapter["title"]] = len(CHAPTER_NUMBERS) + 1
SECTIONS = [  # flattened, in talk order, labelled like the talk (1.1, 1.2, …)
    {**section, "chapter": chapter["title"], "dir": Path(section["path"]),
     "number": f"{CHAPTER_NUMBERS[chapter['title']]}.{n}" if chapter["title"] in CHAPTER_NUMBERS else "",
     "label": (f"{CHAPTER_NUMBERS[chapter['title']]}.{n} {section['title']}" if chapter["title"] in CHAPTER_NUMBERS
               else section["title"] if len(chapter["section"]) > 1 else chapter["title"])}
    for chapter in OUTLINE
    for n, section in enumerate(chapter["section"], 1)
]
CHAPTER_ORDER = {chapter["title"]: i for i, chapter in enumerate(OUTLINE)}
SHARED_FILES = [Path("common/model.py"), Path("common/data.py")]
HIDDEN = {"__init__.py", "__pycache__"}
LANGUAGES = {".py": "python", ".md": "markdown", ".json": "json", ".yaml": "yaml", ".toml": "toml"}

st.set_page_config(page_title="Agentic app demo", layout="wide")
st.markdown("""<style>
.block-container{padding-top:3.3rem}
.st-key-explorer{gap:0 !important}
.st-key-explorer [class*="st-key-tree-"]{gap:0 !important}
.st-key-explorer .stElementContainer, .st-key-explorer [data-testid="stMarkdownContainer"]{margin:0 !important}
.st-key-explorer [data-testid="stMarkdownContainer"] p{margin:0;padding:0.2rem 0.4rem;font-size:0.85rem;color:#987a64;white-space:nowrap}
.st-key-explorer button{justify-content:flex-start;min-height:0;padding:0.15rem 0.4rem;border-radius:5px}
.st-key-explorer button > div{justify-content:flex-start;width:100%;gap:0.35rem}
.st-key-explorer button p{text-align:left;white-space:nowrap;font-size:0.88rem}
.st-key-explorer [data-testid="stIconMaterial"]{font-size:1.05rem;color:#987a64}
.st-key-explorer button[kind="primary"]{background:rgba(152,122,100,0.18) !important;border:none !important}
.st-key-explorer button[kind="primary"] p, .st-key-explorer button[kind="primary"] [data-testid="stIconMaterial"]{color:#1e1e1e !important;font-weight:600}
[class*="st-key-tree-1-"]{padding-left:0.9rem} [class*="st-key-tree-2-"]{padding-left:1.8rem}
[class*="st-key-tree-3-"]{padding-left:2.7rem} [class*="st-key-tree-4-"]{padding-left:3.6rem}
/* itinerary stop without a photo */
.nophoto { aspect-ratio: 3 / 2; border-radius: 8px; background: rgba(208, 180, 159, 0.28); display: flex;
  align-items: center; justify-content: center; font-size: 2.4rem; }
/* the current section's title under the chapter blocks */
.sectiontitle { font-size: 1.7rem; line-height: 1.2; margin: 0; }
.sectiontitle .num { color: #987a64; margin-right: 0.35rem; }
/* navigation: chapter blocks across the top edge of the screen */
[data-testid="stLayoutWrapper"]:has(> .st-key-chapterbar) { display: contents; }
.st-key-chapterbar { position: fixed; top: 0; left: 0; right: 0; height: 3rem; z-index: 999; background: #eee7d7;
  border-bottom: 1px solid #d0b49f; }
.st-key-chapterbar [data-testid="stHorizontalBlock"] { gap: 0; height: 100%; }
.st-key-chapterbar [data-testid="stColumn"] { height: 100%; }
.st-key-chapterbar [data-testid="stColumn"] + [data-testid="stColumn"] { border-left: 1px solid #d0b49f; }
[class*="st-key-chap-"] { height: 100%; justify-content: center; }
[class*="st-key-chap-"][class*="-done"] { background: rgba(208, 180, 159, 0.14); }
[class*="st-key-chap-"][class*="-active"] { background: rgba(208, 180, 159, 0.38); box-shadow: inset 0 -3px 0 #987a64; }
/* the whole block is the button that opens the chapter's sections */
[class*="st-key-chap-"] > div, [class*="st-key-chap-"] [data-testid="stPopover"], [class*="st-key-chap-"] [data-testid="stPopover"] > div,
[class*="st-key-chap-"] .stButton, [class*="st-key-chap-"] .stButton > div { width: 100% !important; height: 100%; }
[class*="st-key-chap-"] button { width: 100%; height: 3rem; border: none; border-radius: 0; background: none; justify-content: center; }
[class*="st-key-chap-"] button:hover { background: rgba(152, 122, 100, 0.12); }
[class*="st-key-chap-"] button p { font-size: 1.02rem; color: #1e1e1e; }
[class*="st-key-chap-"] [data-testid="stPopover"] button [data-testid="stIconMaterial"] { color: #987a64; }
[class*="st-key-chap-finale"] button p { font-size: 1.35rem; font-style: italic; }
/* the chapter's section list */
[class*="st-key-chapmenu-"] { gap: 0.15rem !important; min-width: 14rem; }
[class*="st-key-chapmenu-"] button { justify-content: flex-start; border: none; border-radius: 6px; min-height: 0; padding: 0.3rem 0.7rem; }
[class*="st-key-chapmenu-"] button > div, [class*="st-key-chapmenu-"] button p { justify-content: flex-start; text-align: left; width: 100%; }
[class*="st-key-chapmenu-"] button:hover { background: rgba(152, 122, 100, 0.15); }
[class*="st-key-chapmenu-"] button[kind="primary"] { background: #987a64 !important; }
[class*="st-key-chapmenu-"] button[kind="primary"] p { color: #fff !important; }
</style>""", unsafe_allow_html=True)


def section_files(section: dict) -> list[Path]:
    """Files in a section folder, relative to it, for the file explorer."""
    root = section["dir"]
    return sorted(
        f.relative_to(root)
        for f in root.rglob("*")
        if f.is_file() and not HIDDEN & set(f.parts)
    )


class Tracer:
    """Records the agent loop (model calls, tool calls, context sent) for the bottom panes."""

    def __init__(self):
        self.events: list[dict] = []
        self.context: dict = {}  # what the model received on its last call
        self.reply: list = []  # what the model produced on its last call (content blocks)
        self.calls: list[dict] = []  # every model call: turn, what was sent, and the reply
        self._timers: dict = {}

    def attach(self, agent) -> None:
        agent.add_hook(self.before_model)
        agent.add_hook(self.after_model)
        agent.add_hook(self.before_tool)
        agent.add_hook(self.after_tool)

    def turn(self) -> int:
        return sum(ev["kind"] == "user" for ev in self.events)

    def before_model(self, event: BeforeModelCallEvent):
        agent = event.agent
        self.context = {
            "system": agent.system_prompt,
            "tools": agent.tool_names,
            "messages": copy.deepcopy(agent.messages),
        }
        self.calls.append({"turn": self.turn(), "agent": agent.name, "system": agent.system_prompt,
                           "messages": self.context["messages"], "tokens": event.projected_input_tokens, "reply": None,
                           "start": time.perf_counter(), "end": None, "first_token": None, "reply_blocks": []})
        self._timers[("model", agent.name)] = time.perf_counter()

    def after_model(self, event: AfterModelCallEvent):
        start = self._timers.pop(("model", event.agent.name), time.perf_counter())
        stop = event.stop_response.stop_reason if event.stop_response else "error"
        blocks = event.stop_response.message.get("content", []) if event.stop_response else []
        self.reply = copy.deepcopy(blocks)
        text = " ".join(b["text"] for b in blocks if "text" in b).strip()
        for call in reversed(self.calls):  # the latest call of this agent that has no reply yet
            if call["agent"] == event.agent.name and call["reply"] is None:
                call.update(reply=text or "(tool request)", end=time.perf_counter(), reply_blocks=copy.deepcopy(blocks))
                break
        self.events.append({"kind": "model", "agent": event.agent.name, "ms": (time.perf_counter() - start) * 1000,
                            "stop": stop, "text": text, "t0": start, "t1": time.perf_counter()})

    def before_tool(self, event: BeforeToolCallEvent):
        self._timers[event.tool_use["toolUseId"]] = time.perf_counter()

    def after_tool(self, event: AfterToolCallEvent):
        start = self._timers.pop(event.tool_use["toolUseId"], time.perf_counter())
        output = " ".join(c.get("text", "") for c in event.result.get("content", []))
        self.events.append({
            "kind": "tool",
            "agent": event.agent.name,
            "name": event.tool_use["name"],
            "input": event.tool_use["input"],
            "output": output,
            "ms": (time.perf_counter() - start) * 1000,
            "t0": start,
            "t1": time.perf_counter(),
        })

    def first_token(self, agent_name: str | None = None) -> None:
        """Mark when the first words of the current model call arrived (for the streaming timeline)."""
        for call in reversed(self.calls):
            if call["end"] is None and (agent_name is None or call["agent"] == agent_name):
                if call["first_token"] is None:
                    call["first_token"] = time.perf_counter()
                return


class RawModel:
    """Adapter so a section exposing ask(prompt) shows up in the same UI as an Agent."""

    def __init__(self, module, tracer: Tracer):
        self.module, self.tracer = module, tracer

    def __call__(self, prompt: str) -> str:
        self.tracer.context = {"system": None, "tools": [], "messages": [{"role": "user", "content": [{"text": prompt}]}]}
        self.tracer.calls.append({"turn": self.tracer.turn(), "agent": "raw", "system": None,
                                  "messages": self.tracer.context["messages"], "tokens": None, "reply": None,
                                  "start": time.perf_counter(), "end": None, "first_token": None, "reply_blocks": []})
        start = time.perf_counter()
        answer = self.module.ask(prompt)
        self.tracer.reply = [{"text": answer}]
        self.tracer.calls[-1].update(reply=answer, end=time.perf_counter(), reply_blocks=[{"text": answer}])
        self.tracer.events.append({"kind": "model", "ms": (time.perf_counter() - start) * 1000, "stop": "end_turn",
                                   "text": answer})
        return answer


class EditedSection(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Imports a section's Python files from memory, with the presenter's edits applied.

    Nothing is written to disk: each module's source comes from the edits (or the original file), and its
    __file__ points at the original, so paths like the skills folder still resolve. (An edited SKILL.md is
    handled in build_runtime.)
    """

    def __init__(self, section: dict, edits: dict[Path, str]):
        self.package = f"edited_{uuid.uuid4().hex[:8]}"
        self.folder = section["dir"]
        self.sources = {f"{self.package}.{f.stem}": (f, edits.get(f)) for f in self.folder.glob("*.py")}

    def find_spec(self, name, path=None, target=None):
        if name == self.package:
            return importlib.util.spec_from_loader(name, self, is_package=True)
        if name in self.sources:
            return importlib.util.spec_from_loader(name, self, origin=str(self.sources[name][0]))
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        if module.__name__ == self.package:
            module.__path__, module.__file__ = [], str(self.folder / "__init__.py")
            return
        original, edited = self.sources[module.__name__]
        module.__file__ = str(original)
        source = edited if edited is not None else original.read_text()
        exec(compile(source, str(original), "exec"), module.__dict__)

    def load_agent_module(self):
        sys.meta_path.insert(0, self)
        try:
            return importlib.import_module(f"{self.package}.agent")
        finally:
            sys.meta_path.remove(self)


def section_edits(section: dict) -> dict[Path, str]:
    return {f: text for f, text in st.session_state.get("edits", {}).items() if f.is_relative_to(section["dir"])}


def with_edited_skills(agent_skills, skill_edits: dict[Path, str]):
    """Wrap the AgentSkills plugin so edited skills come from memory; the skill folders stay as they are."""

    def expand(source):
        folder = Path(source) if isinstance(source, (str, Path)) else None
        if folder is None:
            return [source]
        if folder in skill_edits:
            return [Skill.from_content(skill_edits[folder])]
        if not (folder / "SKILL.md").exists() and folder.is_dir():  # a folder of skills
            return [Skill.from_content(skill_edits[sub]) if sub in skill_edits else sub
                    for sub in sorted(folder.iterdir()) if (sub / "SKILL.md").exists()]
        return [folder]

    def make(skills, **kwargs):
        sources = skills if isinstance(skills, list) else [skills]
        return agent_skills(skills=[s for source in sources for s in expand(source)], **kwargs)

    return make


def build_runtime(section: dict, tracer: "Tracer"):
    """The section's agent (or team, or raw model), built from its files plus any in-memory edits."""
    edits = section_edits(section)
    # always read the section's code from disk (plus in-memory edits), never from Python's import cache,
    # so files saved in an editor take effect when the agent is rebuilt
    module = EditedSection(section, edits).load_agent_module()
    skill_edits = {f.parent: text for f, text in edits.items() if f.name == "SKILL.md"}
    if skill_edits and hasattr(module, "AgentSkills"):
        module.AgentSkills = with_edited_skills(module.AgentSkills, skill_edits)
    if not hasattr(module, "build_agent"):
        return RawModel(module, tracer)
    agent = module.build_agent(callback_handler=None)
    team = getattr(agent, "nodes", None)  # a multi-agent graph: trace every member
    for member in [n.executor for n in team.values()] if team else [agent]:
        tracer.attach(member)
    return agent


def files_signature(section: dict) -> tuple:
    """When each of the section's files (and the shared common/ code) was last saved."""
    paths = [f for f in section["dir"].rglob("*") if f.is_file() and "__pycache__" not in f.parts]
    paths += sorted(Path("common").glob("*.py"))
    return tuple(sorted((str(f), f.stat().st_mtime_ns) for f in paths))


def get_session(section: dict) -> dict:
    """One agent + chat history + trace per section, kept across reruns; rebuilt when its files change on disk."""
    key = f"session::{section['path']}"
    signature = files_signature(section)
    if key not in st.session_state:
        tracer = Tracer()
        st.session_state[key] = {"agent": build_runtime(section, tracer), "tracer": tracer, "messages": [],
                                 "usage": None, "signature": signature}
    elif st.session_state[key].get("signature") != signature:
        for name in ("common.data", "common.model"):  # shared code is imported normally, so refresh it first
            if name in sys.modules:
                importlib.reload(sys.modules[name])
        session = st.session_state[key]
        changed = set(signature) ^ set(session.get("signature") or ())
        skills = {Path(f).parent.name for f, _ in changed if Path(f).name == "SKILL.md"}
        rebuild_section(section, session, "↻ files changed on disk · the agent reloaded them", skills)
        session["signature"] = signature
    return st.session_state[key]


def forget_loaded_skills(messages: list, names: set[str]) -> None:
    """Replace earlier results of loading these skills, so the model loads their current version again.

    Without this, a rebuilt agent still sees the old SKILL.md text in the conversation and keeps following it.
    """
    ids = {b["toolUse"]["toolUseId"] for m in messages for b in m["content"]
           if "toolUse" in b and b["toolUse"]["name"] == "skills" and b["toolUse"]["input"].get("skill_name") in names}
    for m in messages:
        for b in m["content"]:
            if "toolResult" in b and b["toolResult"]["toolUseId"] in ids:
                b["toolResult"]["content"] = [{"text": "This skill was updated after it was loaded here. "
                                                        "Call the skills tool again to get its current instructions."}]


def rebuild_section(section: dict, session: dict, note: str, changed_skills: set[str] = frozenset()) -> None:
    """Run edited code: a new agent from the edited files, keeping the conversation so far."""
    old = session["agent"]
    new = build_runtime(section, session["tracer"])
    if hasattr(old, "messages") and hasattr(new, "messages") and not hasattr(new, "nodes"):
        new.messages = copy.deepcopy(old.messages)
        forget_loaded_skills(new.messages, set(changed_skills))
    session["agent"] = new
    session["messages"].append({"role": "note", "content": note})
    session["tracer"].events.append({"kind": "note", "text": note})


def go_to(index: int) -> None:
    st.session_state["section_idx"] = max(0, min(index, len(SECTIONS) - 1))


# ── navigation: four chapter blocks with their section numbers; ◀ ▶ step through the whole talk ──
# each section has its own URL (?section=01_foundations/04_streaming), so a refresh stays put
def url_id(section: dict) -> str:
    return section["dir"].relative_to("chapters").as_posix()


if "section_idx" not in st.session_state:
    wanted = st.query_params.get("section", "")
    go_to(next((i for i, s in enumerate(SECTIONS) if url_id(s) == wanted.strip("/")), 0))
idx = st.session_state["section_idx"]
section = SECTIONS[idx]
current_chapter = CHAPTER_ORDER[section["chapter"]]
if not OUTLINE[current_chapter].get("nav", True):  # the opening slides stand alone, without the top bar
    st.markdown("<style>.st-key-chapterbar { display: none !important; } "
                ".st-key-navprev, .st-key-navnext { top: 0 !important; }</style>", unsafe_allow_html=True)
with st.container(key="chapterbar"):
    shown = [(c, chapter) for c, chapter in enumerate(OUTLINE) if chapter.get("nav", True)]
    for column, (c, chapter) in zip(st.columns(len(shown)), shown):
        state = "active" if c == current_chapter else "done" if c < current_chapter else "todo"
        members = [i for i, s in enumerate(SECTIONS) if s["chapter"] == chapter["title"]]
        if not chapter.get("numbered", True):  # the closing slide: one click, no list
            with column.container(key="chap-finale-active" if state == "active" else "chap-finale"):
                st.button(chapter["title"], key=f"chaptitle-{c}", type="tertiary", on_click=go_to, args=(members[0],))
            continue
        with column.container(key=f"chap-{c}-{state}"):
            with st.popover(f"{CHAPTER_NUMBERS[chapter['title']]}. {chapter['title']}", type="tertiary", width="stretch"):
                with st.container(key=f"chapmenu-{c}"):
                    for i in members:
                        st.button(SECTIONS[i]["label"], key=f"sec-{i}", on_click=go_to, args=(i,), width="stretch",
                                  type="primary" if i == idx else "tertiary")
if st.query_params.get("section") != url_id(section):
    st.query_params["section"] = url_id(section)

# previous / next: invisible bars on the screen edges that fade in on hover
NAV_STYLES = """<style>
/* pinned, so the wrappers must not take space at the top of the page */
[data-testid="stLayoutWrapper"]:has(> .st-key-navprev), [data-testid="stLayoutWrapper"]:has(> .st-key-navnext) {
  display: contents; }
.st-key-navprev, .st-key-navnext { position: fixed; top: 3rem; bottom: 2.6rem; width: 2.6rem; z-index: 998;
  opacity: 0; transition: opacity 0.25s; }
.st-key-navprev { left: 0; }
.st-key-navnext { right: 0; }
.st-key-navprev:hover, .st-key-navnext:hover { opacity: 1; }
/* every wrapper between the bar and its button fills the bar */
.st-key-navprev :has(button), .st-key-navnext :has(button), .st-key-navprev button, .st-key-navnext button {
  height: 100% !important; width: 100% !important; }
.st-key-navprev button, .st-key-navnext button { border: none; border-radius: 0;
  background: rgba(152, 122, 100, 0.15); display: flex; align-items: center; justify-content: center; }
/* ET Book has no ‹ › glyphs, so these use a system font */
.st-key-navprev button p, .st-key-navnext button p { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  font-size: 2.5rem; line-height: 1; margin: 0; }
</style>"""
# the style block goes inside a pinned bar, so it takes no space in the page
if idx > 0:
    with st.container(key="navprev"):
        st.button("‹", key="prev_btn", on_click=go_to, args=(idx - 1,))
        st.markdown(NAV_STYLES, unsafe_allow_html=True)
if idx < len(SECTIONS) - 1:
    with st.container(key="navnext"):
        st.button("›", key="next_btn", on_click=go_to, args=(idx + 1,))
        if idx == 0:
            st.markdown(NAV_STYLES, unsafe_allow_html=True)

show_tree = st.session_state.get("show_tree", False)

# a slide section: one full-width page instead of code and chat
if section.get("slide"):
    st.markdown("""<style>
    .block-container { padding-bottom: 0 !important; }  /* the slide ends where its cards do */
    .st-key-slide h1 { font-size: 3.2rem; margin: 1.5rem 0 0.6rem; }
    .st-key-slide .challenges { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.6rem; margin: 2.5rem 0; }
    .st-key-slide .challenge { border: 1.5px solid #987a64; border-radius: 12px; padding: 0.8rem 1.6rem 1.4rem;
      background: #f6f1e6; }
    .st-key-slide .challenge h3 { color: #987a64; font-size: 1.8rem; }
    .st-key-slide p, .st-key-slide li { font-size: 1.4rem; }
    @keyframes slide-in {{ from {{ opacity: 0; transform: translateX(70px); }} to {{ opacity: 1; transform: none; }} }}
    .st-key-slide { animation: slide-in 0.35s ease-out; }
    /* title slide */
    .st-key-slide .titleslide { min-height: calc(100vh - 9rem); display: flex; flex-direction: column; justify-content: center;
      align-items: center; text-align: center; }
    .st-key-slide .talktitle { font-size: 4.2rem; line-height: 1.1; }
    .st-key-slide .talksub { font-size: 2.4rem; font-style: italic; color: #987a64; margin-top: 0.6rem; }
    .st-key-slide .speaker { font-size: 1.5rem; margin-top: 3.5rem; padding-top: 1.2rem; border-top: 1.5px solid #d0b49f; }
    .st-key-slide .community { position: fixed; left: 0; right: 0; bottom: 2.2rem; text-align: center;
      font-size: 1.05rem; letter-spacing: 0.08em; color: #987a64; }
    /* assistant slide: an animated robot with a map and a calendar */
    .st-key-slide .introslide {{ min-height: calc(100vh - 9rem); display: grid; grid-template-columns: minmax(280px, 0.9fr) 1.1fr;
      align-items: center; gap: 3rem; }}
    .st-key-slide .robot {{ width: 100%; max-height: 70vh; }}
    .st-key-slide .robot * {{ transform-box: fill-box; }}
    .st-key-slide .bot {{ animation: bob 3s ease-in-out infinite; }}
    .st-key-slide .shadow {{ transform-origin: center; animation: squash 3s ease-in-out infinite; }}
    .st-key-slide .light {{ animation: blink-light 1.6s steps(2) infinite; }}
    .st-key-slide .eyes {{ transform-origin: center; animation: blink 4s infinite; }}
    .st-key-slide .maparm {{ transform-origin: 100% 0%; animation: wave 2.4s ease-in-out infinite; }}
    .st-key-slide .route {{ animation: march 1.2s linear infinite; }}
    .st-key-slide .calarm {{ transform-origin: 0% 0%; animation: wave 2.4s ease-in-out infinite reverse; }}
    .st-key-slide .page {{ transform-origin: center; animation: flip 5s ease-in-out infinite; }}
    @keyframes bob {{ 50% {{ transform: translateY(-10px); }} }}
    @keyframes squash {{ 50% {{ transform: scaleX(0.85); opacity: 0.3; }} }}
    @keyframes blink-light {{ 50% {{ opacity: 0.35; }} }}
    @keyframes blink {{ 0%, 92%, 100% {{ transform: scaleY(1); }} 96% {{ transform: scaleY(0.1); }} }}
    @keyframes wave {{ 50% {{ transform: rotate(-5deg); }} }}
    @keyframes march {{ to {{ stroke-dashoffset: -28; }} }}
    @keyframes flip {{ 0%, 80%, 100% {{ transform: scaleY(1); }} 90% {{ transform: scaleY(0); }} }}
    .st-key-slide .introtext h1 {{ margin-top: 0; }}
    .st-key-slide .tripfacts > div {{ white-space: nowrap; }}
    .st-key-slide .tripfacts {{ display: grid; grid-template-columns: auto auto; justify-content: start; gap: 0.6rem 1.5rem; margin: 1.6rem 0 2rem;
      font-size: 1.4rem; padding: 1rem 1.4rem; border: 1.5px solid #d0b49f; border-radius: 12px; background: #f6f1e6; }}
    </style>""".replace("{{", "{").replace("}}", "}"), unsafe_allow_html=True)
    with st.container(key="slide"):
        st.markdown(Path(section["slide"]).read_text(), unsafe_allow_html=True)
    st.stop()

# where we are: the section's number and title, under the chapter blocks
st.markdown(f'<div class="sectiontitle"><span class="num">{section["number"]}</span> {section["title"]}</div>',
            unsafe_allow_html=True)

session = get_session(section)
tracer: Tracer = session["tracer"]

# ── fit to the screen: no page scrolling; panes scroll inside ────────────
code_h = "calc(100vh - 242px)"  # code box ends 28px above the bottom bar
codearea_h = "calc(100vh - 191px)"  # file tabs + code box; the box takes what the tabs leave
area_h = "calc(100vh - 191px)"  # files strip: from the file tabs to the bottom of the code box
chat_h = "calc(100vh - 307px)"  # chat input ends level with the code box
st.markdown(f"""<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ overflow: hidden !important; }}
.block-container {{ padding-bottom: 0 !important; }}
/* Streamlit sizes these boxes with flex: 1 1 0%, so a height needs flex: 0 0 auto to apply */
div.st-key-codearea.st-key-codearea {{ height: {codearea_h} !important; max-height: {codearea_h} !important;
  flex: 0 0 auto !important; display: flex; flex-direction: column; flex-wrap: nowrap !important; }}
[data-testid="stLayoutWrapper"]:has(> .st-key-codearea) {{ flex: 0 0 auto !important; }}
[data-testid="stLayoutWrapper"]:has(> .st-key-codepane) {{ flex: 1 1 0 !important; min-height: 0 !important;
  height: auto !important; max-height: none !important; display: flex !important; flex-direction: column !important; }}
div.st-key-codepane.st-key-codepane {{ flex: 1 1 0 !important; height: auto !important; max-height: none !important;
  min-height: 0 !important; overflow-y: auto !important; }}
div.st-key-chathistory.st-key-chathistory, [data-testid="stLayoutWrapper"]:has(> .st-key-chathistory) {{
  height: {chat_h} !important; max-height: {chat_h} !important; flex: 0 0 auto !important; }}
/* Trace & Context: a bar pinned to the bottom, and a drawer above it that overlays the page */
.st-key-inspectorbar {{ position: fixed; bottom: 0; left: 0; right: 0; z-index: 1000; padding: 0; gap: 0;
  background: #e6dcc8; border-top: 1px solid #d0b49f; }}
/* the whole bar is clickable */
.st-key-inspectorbar .stElementContainer, .st-key-inspectorbar [data-testid="stMarkdownContainer"] {{ width: 100% !important; }}
/* Streamlit gives markdown a negative bottom margin, which would push the bar below the screen edge */
.st-key-inspectorbar .stElementContainer, .st-key-inspectorbar [data-testid="stMarkdownContainer"],
.st-key-inspectorbar [data-testid="stMarkdownContainer"] > div {{ margin: 0 !important; }}
#inspector-bar {{ padding: 0.55rem 5rem; min-height: 2.6rem; box-sizing: border-box; cursor: pointer; user-select: none;
  color: #1e1e1e; }}
#inspector-bar:hover {{ background: rgba(152, 122, 100, 0.15); }}
#inspector-bar .arrow {{ font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; }}
#inspector-bar .arrow::before {{ content: "▴"; }}
body.inspector-open #inspector-bar .arrow::before {{ content: "▾"; }}
[class*="st-key-view_plain-"] {{ display: none !important; }}
body.diff-off [class*="st-key-view_plain-"] {{ display: flex !important; }}
body.diff-off [class*="st-key-view_diff-"] {{ display: none !important; }}
.st-key-filetabs .stElementContainer, .st-key-filetabs [data-testid="stMarkdownContainer"],
.st-key-explorer .stElementContainer {{ margin: 0 !important; }}
.st-key-filetabs [data-testid="stMarkdownContainer"] p {{ margin: 0; }}
.tab-name, .tree-file {{ cursor: pointer; user-select: none; }}
.tab-name {{ display: inline-block; padding: 0.3rem 0.5rem; font-size: 0.9rem; white-space: nowrap; }}
.tree-file {{ display: block; padding: 0.15rem 0.4rem; border-radius: 5px; font-size: 0.88rem; white-space: nowrap; }}
.tree-file:hover, .tab-name:hover {{ background: rgba(152,122,100,0.12); border-radius: 5px; }}
.tree-file .ficon, .tab-name .ficon {{ font-family: 'Material Symbols Rounded'; font-size: 1.05rem; color: #987a64;
  vertical-align: -0.2rem; margin-right: 0.2rem; }}
#diff-switch {{ width: 2.1rem; height: 1.15rem; border-radius: 1rem; background: #987a64; position: relative;
  cursor: pointer; transition: background 0.2s; margin: 0.25rem 0; }}
#diff-switch .knob {{ position: absolute; top: 0.15rem; left: 1.1rem; width: 0.85rem; height: 0.85rem; border-radius: 50%;
  background: #f6f1e6; transition: left 0.2s; }}
body.diff-off #diff-switch {{ background: #cfc4b2; }}
body.diff-off #diff-switch .knob {{ left: 0.15rem; }}
.st-key-codepane textarea {{ font-family: 'Cascadia Code', Menlo, monospace !important; font-size: 0.85rem;
  line-height: 1.5; height: calc({code_h} - 3rem) !important; background: #f6f1e6; }}
.st-key-inspector {{ display: none !important; }}
/* the files strip sits in the page margin, so the code area lines up with the chapter menu above it */
[data-testid="stColumn"]:not(:has([data-testid="stColumn"])):has(.st-key-filesstrip) {{
  flex: 0 0 1.2rem !important; width: 1.2rem !important; min-width: 1.2rem !important; margin-left: -2.2rem !important; }}
/* slide transition between sections */
@keyframes slide-from-right {{ from {{ opacity: 0; transform: translateX(70px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes slide-from-left {{ from {{ opacity: 0; transform: translateX(-70px); }} to {{ opacity: 1; transform: none; }} }}
[class*="st-key-slide-next-"] {{ animation: slide-from-right 0.35s ease-out; }}
[class*="st-key-slide-prev-"] {{ animation: slide-from-left 0.35s ease-out; }}
/* the bar and drawer are pinned, so their wrappers must not take space (or gaps) at the top of the page */
[data-testid="stLayoutWrapper"]:has(> .st-key-inspectorbar), [data-testid="stLayoutWrapper"]:has(> .st-key-inspector) {{
  display: contents; }}
.st-key-inspectorbar iframe {{ position: absolute; width: 0; height: 0; border: 0; }}
body.inspector-open .st-key-inspector {{ display: flex !important; }}
div.st-key-filesstrip.st-key-filesstrip, div.st-key-explorer.st-key-explorer {{
  height: {area_h} !important; max-height: {area_h} !important; flex: 0 0 auto !important; }}
div.st-key-explorer.st-key-explorer {{ overflow-y: auto; }}
.st-key-filesstrip :has(button), .st-key-filesstrip button {{ height: 100% !important; width: 100% !important; }}
.st-key-filesstrip button {{ border: none; border-radius: 6px; padding: 0; min-height: 0; opacity: 0.25;
  transition: opacity 0.25s; display: flex; align-items: center; justify-content: center; }}
.st-key-filesstrip button p {{ font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 1.1rem; margin: 0; }}
/* file tabs: each tab is a name button plus an optional ✎, resting on the code box */
.st-key-tabrow {{ margin-bottom: -1rem; }}
/* the tabs give way on narrow screens (scrolling sideways); the controls at the right edge always keep their place */
[data-testid="stLayoutWrapper"]:has(> .st-key-filetabs) {{ flex: 1 1 auto !important; min-width: 0 !important; }}
[data-testid="stLayoutWrapper"]:has(> .st-key-tabcontrols) {{ flex: none !important; }}
.st-key-filetabs {{ flex: 1 1 auto !important; min-width: 0 !important; flex-wrap: wrap !important; row-gap: 0.25rem !important; }}
[class*="st-key-tab_"] {{ flex: none !important; }}
.st-key-tabcontrols {{ flex: none !important; margin-left: 0.5rem; }}
.st-key-tabcontrols .stElementContainer, .st-key-tabcontrols [data-testid="stMarkdownContainer"] {{ margin: 0 !important; }}
.st-key-filetabs {{ gap: 0.15rem !important; }}
[class*="st-key-tab_"] {{ border: 1px solid #d0b49f; border-bottom: none; border-radius: 8px 8px 0 0;
  padding: 0 0.35rem 0 0.15rem; }}
[class*="st-key-tab_"][class*="_on"] {{ background: #f6f1e6; }}
[class*="st-key-tab_"][class*="_on"] [class*="st-key-tabname_"] button p {{ font-weight: 600; }}
[class*="st-key-tab_"] button {{ padding: 0.25rem 0.5rem; min-height: 0; }}
[class*="st-key-pen_"] button {{ padding: 0.1rem 0.25rem !important; opacity: 0.45; }}
[class*="st-key-pen_"] button:hover, [class*="st-key-pen_"][class*="_on"] button {{ opacity: 1; }}
[class*="st-key-pen_"][class*="_on"] button {{ background: rgba(152, 122, 100, 0.2); border-radius: 4px; }}
[class*="st-key-pen_"] button p, .st-key-restore_btn button p {{ font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; }}
/* right edge controls: small, aligned with the code box's right border */
.st-key-tabcontrols button {{ padding: 0.1rem 0.6rem; min-height: 0; font-size: 0.85rem; }}
.st-key-run_btn button {{ border: 1px solid #987a64; border-radius: 6px; }}
.st-key-filetabs button[aria-checked="true"] {{ background: #f6f1e6 !important; color: #1e1e1e !important;
  border-color: #d0b49f !important; font-weight: 600; }}
.st-key-filesstrip button:hover {{ opacity: 1; background: rgba(152, 122, 100, 0.15); }}
.st-key-inspector {{ position: fixed; bottom: 46px; left: 0; right: 0; height: 45vh; z-index: 999; overflow-y: auto;
  padding: 0.8rem 5rem; background: #eee7d7; border-top: 2px solid #987a64; box-shadow: 0 -6px 18px rgba(30,30,30,0.15); }}
</style>""", unsafe_allow_html=True)

# Browser-side code for the bar and the scripted-prompt menu. It is installed once into the page itself:
# Streamlit swaps the small frames that deliver it, and Chrome stops running code that belongs to a removed frame.
PAGE_JS = r"""(() => {
  if (window.presenter) return;
  const doc = document, KEY = "inspector-open", BOX = '[data-testid="stChatInputTextArea"]';

  // Trace & context drawer: toggled in the browser only, so it never interrupts a running agent
  const applyDrawer = () => {
    doc.body.classList.toggle("inspector-open", localStorage.getItem(KEY) === "1");
    doc.body.classList.toggle("diff-off", localStorage.getItem("diff-off") === "1");
  };
  doc.addEventListener("click", (e) => {  // the diff switch: show the diff or the whole file
    if (!e.target.closest("#diff-switch")) return;
    localStorage.setItem("diff-off", doc.body.classList.contains("diff-off") ? "0" : "1");
    applyDrawer();
  });
  doc.addEventListener("click", (e) => {
    if (!e.target.closest("#inspector-bar")) return;
    localStorage.setItem(KEY, doc.body.classList.contains("inspector-open") ? "0" : "1");
    applyDrawer();
  });

  // Scripted prompts: a menu above the empty chat box
  const style = doc.createElement("style");
  style.textContent = `#script-menu { position: fixed; z-index: 2000; background: #f6f1e6; border: 1px solid #d0b49f;
    border-radius: 10px; box-shadow: 0 -6px 18px rgba(30,30,30,0.15); padding: 0.35rem;
    font-family: et-book, Palatino, Georgia, serif; font-size: 1rem; }
  #script-menu .hint { color: #987a64; font-size: 0.8rem; padding: 0.15rem 0.6rem 0.35rem; }
  #script-menu .item { padding: 0.4rem 0.6rem; border-radius: 6px; cursor: pointer; color: #1e1e1e; display: flex; gap: 0.5rem; }
  #script-menu .item.sent { color: #987a64; }
  #script-menu .item.active, #script-menu .item:hover { background: rgba(152,122,100,0.15); }
  #script-menu .mark { width: 1.2rem; flex: none; text-align: center;
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; }`;
  doc.head.appendChild(style);
  const menu = doc.createElement("div");
  menu.id = "script-menu"; menu.style.display = "none"; doc.body.appendChild(menu);
  let items = [], active = -1;
  const box = () => doc.querySelector(BOX);
  const isBox = (el) => el && el.matches && el.matches(BOX);
  const hide = () => { menu.style.display = "none"; active = -1; };
  const highlight = (i) => {
    active = i; menu.querySelectorAll(".item").forEach((el, j) => el.classList.toggle("active", j === i));
  };
  const fill = (text) => {
    const b = box(); if (!b) return;
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set.call(b, text);
    b.dispatchEvent(new Event("input", { bubbles: true })); hide(); b.focus();
  };
  const show = () => {
    const b = box();
    if (!b || !items.length || b.value) return;
    menu.innerHTML = '<div class="hint">Scripted prompts · ↑↓ to choose · Enter to use · Esc to type your own</div>';
    items.forEach((item, i) => {
      const el = doc.createElement("div"); el.className = "item" + (item.sent ? " sent" : "");
      el.innerHTML = `<span class="mark">${item.sent ? "✓" : item.photo ? "📷" : "›"}</span><span></span>`;
      el.lastChild.textContent = item.text;
      el.onmousedown = (e) => { e.preventDefault(); fill(item.text); };  // before the box loses focus
      el.onmouseenter = () => highlight(i);
      menu.appendChild(el);
    });
    const r = b.closest('[data-testid="stChatInput"]').getBoundingClientRect();
    Object.assign(menu.style, { display: "block", left: r.left + "px", width: r.width + "px",
                                bottom: (innerHeight - r.top + 6) + "px" });
    highlight(Math.max(0, items.findIndex((item) => !item.sent)));
  };
  // delegated listeners: the chat box is re-created by Streamlit from time to time
  doc.addEventListener("focusin", (e) => isBox(e.target) && show());
  doc.addEventListener("click", (e) => isBox(e.target) && show());
  doc.addEventListener("focusout", (e) => isBox(e.target) && setTimeout(hide, 150));
  doc.addEventListener("input", (e) => isBox(e.target) && (e.target.value ? hide() : show()));
  doc.addEventListener("keydown", (e) => {  // capture phase, so Enter picks a prompt instead of sending
    if (!isBox(e.target) || menu.style.display === "none") return;
    const n = items.length;
    if (e.key === "ArrowDown") { highlight((active + 1) % n); e.preventDefault(); }
    else if (e.key === "ArrowUp") { highlight((active - 1 + n) % n); e.preventDefault(); }
    else if (e.key === "Enter" && active >= 0) { fill(items[active].text); e.preventDefault(); e.stopPropagation(); }
    else if (e.key === "Escape") { hide(); e.preventDefault(); }
  }, true);

  // File tabs and tree rows: show a file without a rerun, remembered per section
  let section = "";
  const showFile = (i) => { doc.body.dataset.file = String(i); if (section) localStorage.setItem("file::" + section, String(i)); };
  doc.addEventListener("click", (e) => {
    const pick = e.target.closest('[class*="pick-"]');
    const pen = e.target.closest('[class*="st-key-pen_"]');
    const el = pick || pen;
    if (!el) return;
    const m = (pick ? pick.className : pen.className).match(pick ? /pick-(\d+)/ : /st-key-pen_(\d+)/);
    if (m) showFile(m[1]);  // ✎ also picks its file, so leaving edit mode shows the edited file
  });
  const setSection = (id) => {
    section = id;
    doc.body.dataset.file = localStorage.getItem("file::" + id) || "0";
  };

  window.presenter = { applyDrawer, setScript: (list) => { items = list; hide(); }, setSection };
})();"""


def page_bootstrap(script_items: list | None = None, section_id: str | None = None) -> str:
    """A tiny frame that installs PAGE_JS into the page (once) and hands it this run's data."""
    call = f"win.presenter.setScript({json.dumps(script_items)});" if script_items is not None else ""
    if section_id is not None:
        call += f"win.presenter.setSection({json.dumps(section_id)});"
    return f"""<script>
      const win = window.parent;
      if (!win.presenter) {{
        const s = win.document.createElement("script"); s.textContent = {json.dumps(PAGE_JS)};
        win.document.head.appendChild(s);
      }}
      win.presenter.applyDrawer(); {call}
    </script>"""


# ── Trace & Context: a bar pinned to the bottom and a drawer above it (positioned with CSS) ─
def tracer_turns() -> list[list[dict]]:
    turns: list[list[dict]] = []
    for ev in tracer.events:
        if ev["kind"] == "user" or not turns:
            turns.append([])
        turns[-1].append(ev)
    return turns


def last_turn_summary(turns: list[list[dict]]) -> str:
    if not turns:
        return "no turns yet"
    last = turns[-1]
    models = sum(ev["kind"] == "model" for ev in last)
    tools = sum(ev["kind"] == "tool" for ev in last)
    agents = {ev.get("agent") for ev in last if ev.get("agent") not in (None, "Strands Agents")}
    parts = [f"{models} model call{'s' * (models != 1)}", f"{tools} tool call{'s' * (tools != 1)}"]
    if agents:
        parts.append(f"{len(agents)} agents")
    if session["usage"]:
        parts.append(f"{session['usage'].get('totalTokens', 0) / 1000:.1f}k tokens total")
    return " · ".join(parts)


# The bar opens and closes the drawer in the browser only. A Streamlit button would rerun the script,
# and a rerun cancels an agent that is still answering.
bar_box = st.container(key="inspectorbar")
bar_slot = bar_box.empty()
bar_box.iframe(page_bootstrap(section_id=section["path"]), height=1)

drawer_slot = st.container(key="inspector").empty()


HOOD_CSS = """<style>
.hood { display: flex; gap: 0.8rem; align-items: stretch; }
.hood .lead { font-size: 0.95rem; margin: 0 0 0.5rem; }
.hood .turn { flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; gap: 0.25rem; }
.hood .turn h4 { font-size: 0.8rem; color: #987a64; margin: 0; font-weight: 600; letter-spacing: 0.03em; }
.hood .req { border: 1.5px solid #987a64; border-radius: 8px; padding: 0.3rem 0.45rem; background: #f6f1e6; }
.hood .req .cap { font-size: 0.72rem; color: #987a64; margin-bottom: 0.15rem; }
.hood .msg { font-size: 0.8rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0.08rem 0.3rem;
  border-radius: 4px; margin: 0.08rem 0; }
.hood .msg.system { background: rgba(152,122,100,0.12); }
.hood .msg.resent { color: #8a8072; background: rgba(152,122,100,0.06); }
.hood .msg.new { background: #e3b26b55; font-weight: 600; }
.hood .msg .tag { float: right; font-size: 0.68rem; font-weight: 400; color: #987a64; margin-left: 0.4rem; }
.hood .missing { font-size: 0.75rem; color: #b4532a; border: 1px dashed #b4532a; border-radius: 4px; padding: 0.1rem 0.3rem;
  margin: 0.08rem 0; }
.hood .foot { font-size: 0.72rem; color: #987a64; margin-top: 0.15rem; text-align: right; }
.hood .arrow { text-align: center; font-size: 0.8rem; color: #987a64; }
.hood .reply { font-size: 0.8rem; border-left: 3px solid #a9c19a; padding: 0.15rem 0.4rem; color: #1e1e1e;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>"""


def block_text(block: dict) -> str:
    if "text" in block:
        return block["text"]
    if "image" in block:
        return "📷 image"
    if "toolUse" in block:
        return f"🔧 {block['toolUse']['name']}(…)"
    if "toolResult" in block:
        return "↩️ tool result"
    if "reasoningContent" in block:
        return "💭 thinking"
    return next(iter(block), "")


def render_hood(calls: list[dict], raw: bool, live_text: str = "", system_lead: bool = False) -> None:
    """What each request to the model contained, turn by turn: the agent's memory made visible."""
    e = html.escape
    if system_lead:
        lead = ("<b>The system prompt rides along at the top of every request.</b> It isn't remembered: "
                "the model re-reads it on every call, before the conversation.")
    elif raw:
        lead = ("<b>Each request carries only the newest message.</b> Nothing from earlier turns is sent, "
                "so the model can't know what was said before.")
    else:
        lead = ("<b>Every request re-sends the whole conversation</b> (<code>agent.messages</code>). "
                "That list is the agent's memory: the model itself keeps nothing.")
    if not calls:
        st.markdown(HOOD_CSS + f'<div class="hood"><div><p class="lead">{lead}</p>'
                    '<p class="lead" style="color:#987a64">Send a message to see what the model receives.</p></div></div>',
                    unsafe_allow_html=True)
        return
    by_turn: dict[int, dict] = {}
    for call in calls:
        by_turn[call["turn"]] = call  # one card per turn: its last model call
    shown = sorted(by_turn)[-3:]
    cards = []
    prev_count = 0
    for turn in sorted(by_turn):
        call = by_turn[turn]
        msgs = call["messages"]
        if turn in shown:
            rows = []
            if call["system"]:
                tag = '<span class="tag">every request</span>' if system_lead else ""
                rows.append(f'<div class="msg system"{" style=font-weight:600" if system_lead else ""}>{tag}'
                            f'⚙️ system · {e(call["system"].splitlines()[0])}</div>')
            if raw and turn > 1:
                earlier = "turn 1 is" if turn == 2 else f"turns 1–{turn - 1} are"
                rows.append(f'<div class="missing">✗ {earlier} not sent</div>')
            resent = 0 if raw else min(prev_count, len(msgs))
            hidden = resent - 2 if resent > 3 else 0  # long histories: first two re-sent rows, then a count
            for i, m in enumerate(msgs):
                if 2 <= i < 2 + hidden:
                    if i == 2:
                        rows.append(f'<div class="msg resent"><span class="tag">re-sent</span>⋯ {hidden} more</div>')
                    continue
                icon = "👤" if m["role"] == "user" else "🤖"
                text = " ".join(block_text(b) for b in m["content"]).replace("\n", " ")
                new = i >= resent
                tag = "new" if new else "re-sent"
                rows.append(f'<div class="msg {"new" if new else "resent"}"><span class="tag">{tag}</span>'
                            f'{i + 1} {icon} {e(text[:90])}</div>')
            tokens = f" · {call['tokens']:,} tokens" if call.get("tokens") else ""
            reply = call["reply"] if call["reply"] is not None else (live_text or "…")
            cards.append(f'<div class="turn"><h4>TURN {turn}</h4><div class="req"><div class="cap">request → model</div>'
                         f'{"".join(rows)}<div class="foot">{len(msgs)} message{"s" * (len(msgs) != 1)}{tokens}</div></div>'
                         f'<div class="arrow">↓ 🧠 model</div><div class="reply">{e(reply.replace(chr(10), " ")[:120])}</div></div>')
        prev_count = len(msgs) + 1  # the next request adds this turn's reply, then the new message
    st.markdown(HOOD_CSS + f'<p class="lead" style="margin:0 0 0.4rem">{lead}</p><div class="hood">{"".join(cards)}</div>',
                unsafe_allow_html=True)


HOOD_FLOW_CSS = """<style>
.flow { display: flex; align-items: stretch; gap: 0.35rem 0.3rem; flex-wrap: wrap; }
.flow .step { border: 1.5px solid #987a64; border-radius: 8px; background: #f6f1e6; padding: 0.25rem 0.45rem;
  min-width: 8rem; max-width: 12.5rem; font-size: 0.78rem; line-height: 1.35; }
.flow .step.model { border-color: #987a64; }
.flow .step.code { border-color: #6b8f71; background: #eef3ea; }
.flow .step.data { border-style: dashed; }
.flow .step.done { border-color: #6b8f71; }
.flow .step.wide { max-width: none; flex: 0 1 auto; }
.flow .step h5 { margin: 0 0 0.15rem; font-size: 0.78rem; color: #987a64; font-weight: 600; }
.flow .step.code h5 { color: #4f7356; }
.flow .step .line { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.flow .step .small { font-size: 0.7rem; color: #987a64; }
.flow .arrow { align-self: center; color: #987a64; font-size: 1.1rem; flex: none; }
.gantt { display: grid; grid-template-columns: 6.5rem 1fr; gap: 0.3rem 0.6rem; align-items: center; font-size: 0.8rem; }
.gantt .track { position: relative; height: 1.2rem; background: rgba(152,122,100,0.08); border-radius: 4px; }
.gantt .bar { position: absolute; top: 0; bottom: 0; border-radius: 4px; background: #e3b26b; color: #1e1e1e;
  font-size: 0.7rem; padding: 0 0.3rem; white-space: nowrap; overflow: hidden; display: flex; align-items: center; }
.gantt .bar.writer { background: #a9c19a; }
.gantt .bar.wait { background: transparent; border: 1px dashed #c9b9a3; color: #987a64; }
.timeline .row { display: grid; grid-template-columns: 9rem 1fr; gap: 0.6rem; align-items: center; margin: 0.35rem 0; font-size: 0.8rem; }
.timeline .track { position: relative; height: 1.3rem; background: rgba(152,122,100,0.08); border-radius: 4px; }
.timeline .seg { position: absolute; top: 0; bottom: 0; border-radius: 4px; display: flex; align-items: center;
  padding: 0 0.35rem; font-size: 0.7rem; white-space: nowrap; overflow: hidden; }
.timeline .blank { background: repeating-linear-gradient(45deg, #efe7d6, #efe7d6 6px, #e6dcc8 6px, #e6dcc8 12px); color: #987a64; }
.timeline .text { background: #a9c19a; }
.timeline .all { background: #a9c19a; }
.blocks { display: flex; gap: 0.5rem; align-items: stretch; }
.blocks .blk { border: 1.5px solid #987a64; border-radius: 8px; background: #f6f1e6; padding: 0.3rem 0.5rem; font-size: 0.8rem;
  min-width: 9rem; max-width: 16rem; }
.blocks .blk img { height: 5.2rem; border-radius: 4px; display: block; margin-top: 0.2rem; }
.blocks code, .flow code { font-size: 0.7rem; white-space: nowrap; padding: 0 0.15rem; }
</style>"""

# one <style> block: two in a row get mangled by Streamlit's HTML sanitizer, swallowing the text after them
HOOD_STYLES = HOOD_CSS.replace("</style>", HOOD_FLOW_CSS.replace("<style>", "").replace("</style>", "") + "</style>")

def last_turn_calls(calls: list[dict]) -> list[dict]:
    if not calls:
        return []
    turn = calls[-1]["turn"]
    return [c for c in calls if c["turn"] == turn]


def last_turn_events(events: list[dict]) -> list[dict]:
    starts = [i for i, ev in enumerate(events) if ev["kind"] == "user"]
    return events[starts[-1]:] if starts else []


def hood_lead(text: str) -> str:
    return f'<p class="lead" style="margin:0 0 0.45rem;font-size:0.95rem">{text}</p>'


def empty_hood(lead: str) -> None:
    st.markdown(HOOD_STYLES + hood_lead(lead)
                + '<p style="color:#987a64;font-size:0.9rem">Send a message to see it happen.</p>', unsafe_allow_html=True)


def requested_tools(call: dict) -> list[str]:
    return [b["toolUse"]["name"] for b in call.get("reply_blocks", []) if "toolUse" in b]


def render_loop(tracer, lead: str, skills: bool = False, structured: bool = False) -> None:
    """The agent loop of the last turn: model call → tool requests → your code runs → results added → model again."""
    calls, events = last_turn_calls(tracer.calls), last_turn_events(tracer.events)
    if not calls:
        return empty_hood(lead)
    e, steps = html.escape, []
    if skills and calls[0]["system"]:
        names = re.findall(r"<name>(.*?)</name>", calls[0]["system"])
        if names:
            steps.append('<div class="step data"><h5>system prompt</h5><div class="line">your instructions</div>'
                         + "".join(f'<div class="line">📘 <b>{e(n)}</b>: name + description only</div>' for n in names) + "</div>")
    tool_events = [ev for ev in events if ev["kind"] == "tool"]
    for n, call in enumerate(calls, 1):
        thinking = any("reasoningContent" in b for b in call.get("reply_blocks", []))
        asks = requested_tools(call)
        if call["end"] is None:
            outcome = "answering…"
        elif asks:
            outcome = "asks for " + ", ".join(f"<code>{e(a)}</code>" for a in asks)
        else:
            outcome = "✅ final answer"
        count = len(call["messages"])
        size = f'{count} message{"s" * (count != 1)}' + (f' · {call["tokens"]:,} tokens' if call.get("tokens") else "")
        steps.append(f'<div class="step model{" done" if not asks and call["end"] else ""}"><h5>🧠 model call {n}</h5>'
                     f'<div class="small">receives {size}</div>{"<div class=line>💭 thinks first</div>" if thinking else ""}'
                     f'<div class="line">{outcome}</div></div>')
        if asks:
            ran = [ev for ev in tool_events if ev["name"] in asks][:len(asks)]
            tool_events = [ev for ev in tool_events if ev not in ran]
            lines = []
            for ev in ran:
                if ev["name"] == "skills":
                    lines.append(f'<div class="line">📘 loads SKILL.md ({len(ev["output"]):,} chars)</div>')
                elif structured and ev["name"] == calls[-1].get("structured_tool", "Itinerary"):
                    lines.append(f'<div class="line">📋 <code>{e(ev["name"])}</code>: arguments validated</div>')
                else:
                    lines.append(f'<div class="line">🔧 <code>{e(ev["name"])}</code> · {ev["ms"]:.0f} ms</div>')
            if ran:
                steps.append('<div class="step code"><h5>your Python runs</h5>' + "".join(lines)
                             + '<div class="small">results are added to the messages</div></div>')
    if structured:
        out = next((ev for ev in reversed(events) if ev["kind"] == "tool" and ev["name"] == "Itinerary"), None)
        if out:
            data = out["input"]
            days = data.get("days", [])
            stops = sum(len(d.get("stops", [])) for d in days)
            steps.append('<div class="step data"><h5>structured data</h5>'
                         f'<div class="line">title: {e(str(data.get("title", ""))[:40])}</div>'
                         f'<div class="line">days: {len(days)} · stops: {stops}</div>'
                         f'<div class="line">tips: {len(data.get("tips", []))}</div>'
                         '<div class="small">→ rendered as cards</div></div>')
    st.markdown(HOOD_STYLES + hood_lead(lead) + '<div class="flow">'
                + '<div class="arrow">→</div>'.join(steps) + "</div>", unsafe_allow_html=True)


def render_streaming(tracer) -> None:
    lead = ("<b>Streaming doesn't make the model faster.</b> It shows the first words as soon as they exist, "
            "instead of waiting for the whole answer.")
    done = [c for c in tracer.calls if c["end"]]
    if not done:
        return empty_hood(lead)
    call = done[-1]
    total = call["end"] - call["start"]
    first = (call["first_token"] or call["end"]) - call["start"]
    pct = lambda x: f"{100 * x / total:.1f}%"
    st.markdown(HOOD_STYLES + hood_lead(lead) + '<div class="timeline">'
                f'<div class="row"><div>Without streaming</div><div class="track">'
                f'<div class="seg blank" style="left:0;width:{pct(total - 0.001)}">nothing on screen for {total:.1f} s</div></div></div>'
                f'<div class="row"><div></div><div class="small" style="text-align:right;color:#987a64">'
                f'then the whole answer appears at once</div></div>'
                f'<div class="row"><div>With streaming</div><div class="track">'
                f'<div class="seg blank" style="left:0;width:{pct(first)}">{first:.1f} s</div>'
                f'<div class="seg text" style="left:{pct(first)};width:{pct(total - first)}">words keep arriving until {total:.1f} s</div>'
                f'</div></div></div>', unsafe_allow_html=True)


def render_team(tracer) -> None:
    lead = ("<b>Three specialists work at the same time; the writer waits for all of them.</b> "
            "Each bar is one agent, from its first model call to its last.")
    events = last_turn_events(tracer.events)
    if not events:
        return empty_hood(lead)
    t_start = events[0].get("t0") or time.perf_counter()
    spans: dict[str, list] = {}
    for ev in events:
        if ev.get("agent") and ev.get("t0"):
            span = spans.setdefault(ev["agent"], [ev["t0"], ev["t1"], 0, 0])
            span[0], span[1] = min(span[0], ev["t0"]), max(span[1], ev["t1"])
            span[2 if ev["kind"] == "model" else 3] += 1
    if not spans:
        return empty_hood(lead)
    t_end = max(v[1] for v in spans.values())
    total = max(t_end - t_start, 0.001)
    rows = []
    for name in ["flights", "hotels", "activities", "writer"]:
        if name not in spans:
            continue
        a, b, models, tools = spans[name]
        left, width = 100 * (a - t_start) / total, max(100 * (b - a) / total, 2)
        wait = f'<div class="bar wait" style="left:0;width:{left:.1f}%">waits</div>' if name == "writer" and left > 8 else ""
        rows.append(f'<div>{"✍️" if name == "writer" else "🧑‍💼"} {name}</div><div class="track">{wait}'
                    f'<div class="bar{" writer" if name == "writer" else ""}" style="left:{left:.1f}%;width:{width:.1f}%">'
                    f'{b - a:.1f} s · {models} model · {tools} tool</div></div>')
    st.markdown(HOOD_STYLES + hood_lead(lead) + f'<div class="gantt">{"".join(rows)}'
                f'<div></div><div style="font-size:0.72rem;color:#987a64;text-align:right">0 s ··· {total:.1f} s</div></div>',
                unsafe_allow_html=True)


def render_multimodal(tracer) -> None:
    lead = ("<b>A message is a list of content blocks.</b> A photo is just another block next to the text, "
            "and the model reads both together.")
    calls = last_turn_calls(tracer.calls)
    if not calls:
        return empty_hood(lead)
    user = next((m for m in reversed(calls[0]["messages"]) if m["role"] == "user"), None)
    e, blocks = html.escape, []
    for i, b in enumerate(user["content"] if user else []):
        if "text" in b:
            blocks.append(f'<div class="blk"><code>content[{i}]</code> · text<div>{e(b["text"][:90])}</div></div>')
        elif "image" in b:
            raw = b["image"]["source"].get("bytes", b"")
            data = base64.b64encode(raw).decode() if isinstance(raw, (bytes, bytearray)) else ""
            fmt = b["image"].get("format", "jpeg")
            img = f'<img src="data:image/{fmt};base64,{data}">' if data else ""
            blocks.append(f'<div class="blk"><code>content[{i}]</code> · image/{fmt} · {len(raw) // 1024} KB{img}</div>')
    reply = calls[-1]["reply"] or "…"
    st.markdown(HOOD_STYLES + hood_lead(lead) + '<div class="flow"><div class="step data wide"><h5>👤 user message</h5>'
                f'<div class="blocks">{"".join(blocks)}</div></div><div class="arrow">→</div>'
                f'<div class="step model"><h5>🧠 model</h5><div>reads text + image</div></div><div class="arrow">→</div>'
                f'<div class="step done"><h5>reply</h5><div style="white-space:normal">{e(reply[:160])}</div></div></div>',
                unsafe_allow_html=True)


def render_hood_for(kind: str, live_text: str = "") -> None:
    """Pick the Under the hood view for this section's kind (set with `hood = ...` in chapters.toml)."""
    agent = session["agent"]
    if kind == "memory":
        render_hood(tracer.calls, raw=not hasattr(agent, "messages"), live_text=live_text)
    elif kind == "system":
        render_hood(tracer.calls, raw=False, live_text=live_text, system_lead=True)
    elif kind == "streaming":
        render_streaming(tracer)
    elif kind == "loop":
        render_loop(tracer, "<b>The agent loop.</b> The model can't run code: it asks for a tool, your Python runs it, "
                            "the result is added to the messages, and the model is called again, until it answers.")
    elif kind == "skills":
        render_loop(tracer, "<b>Progressive disclosure.</b> The system prompt lists each skill by name and description only; "
                            "the full SKILL.md is loaded into the conversation only when the model asks for it.", skills=True)
    elif kind == "team":
        render_team(tracer)
    elif kind == "structured":
        render_loop(tracer, "<b>Structured output is a tool call.</b> Strands gives the model a tool whose parameters are "
                            "the Pydantic schema; the arguments it sends are validated into an <code>Itinerary</code> object.",
                    structured=True)
    elif kind == "multimodal":
        render_multimodal(tracer)


def render_inspector(live_text: str = "") -> None:
    """Draw the bar summary and the drawer. Called at the end of a run, and repeatedly while an agent answers."""
    turns = tracer_turns()
    bar_slot.markdown(f'<div id="inspector-bar"><span class="arrow"></span> 🔍 Trace &amp; context · last turn: '
                      f'{last_turn_summary(turns)}{" · answering…" if live_text else ""}</div>', unsafe_allow_html=True)
    with drawer_slot.container():
        if section.get("hood"):
            hood_col, trace_col = st.columns([2.1, 1], gap="medium")
            with hood_col:
                st.markdown("**Under the hood**")
                render_hood_for(section["hood"], live_text=live_text)
            context_col = hood_col.expander("Raw context of the last model call")
        else:
            trace_col, context_col = st.columns([1.6, 1], gap="medium")

        with trace_col:

            head, usage = st.columns([2, 1])
            head.markdown("**Trace** · agent loop per turn, newest first")
            if session["usage"]:
                u = session["usage"]
                usage.caption(f"tokens (cumulative) · in {u.get('inputTokens', 0):,} · out {u.get('outputTokens', 0):,}")

            with st.container(border=True):
                if not turns:
                    st.caption("Send a message to see the model calls and tool calls.")
                for turn in reversed(turns):
                    chips, tools, model_calls = [], [], 0
                    for ev in turn:
                        if ev["kind"] == "user":
                            chips.append(f"👤 *{ev['text']}*")
                        elif ev["kind"] == "note":
                            chips.append(f"✎ *{ev['text']}*")
                        elif ev["kind"] == "model":
                            model_calls += 1
                            who = f"**{ev['agent']}** " if ev.get("agent") not in (None, "Strands Agents") else ""
                            chips.append(f"🧠 {who}model #{model_calls} `{ev['ms']:.0f} ms` → `{ev['stop']}`")
                            if ev.get("text"):
                                preview = ev["text"].replace("\n", " ")
                                chips.append(f"💬 *{preview[:70]}{'…' if len(preview) > 70 else ''}*")
                        elif ev["kind"] == "tool":
                            who = f"{ev['agent']} · " if ev.get("agent") not in (None, "Strands Agents") else ""
                            chips.append(f"🔧 {who}**{ev['name']}** `{ev['ms']:.0f} ms`")
                            tools.append(ev)
                    if live_text and turn is turns[-1]:
                        preview = live_text.replace("\n", " ")[-70:]
                        chips.append(f"💬 *…{preview}* ▌")
                    st.markdown("  ➜  ".join(chips))
                    if tools:
                        # Side by side for a few calls; one list for a team's many calls
                        if len(tools) <= 4:
                            boxes = [col.expander(f"🔧 {ev['name']}") for col, ev in zip(st.columns(len(tools)), tools)]
                        else:
                            with st.expander(f"🔧 {len(tools)} tool calls"):
                                boxes = [st.container(border=True) for _ in tools]
                        for box, ev in zip(boxes, tools):
                            with box:
                                if len(tools) > 4:
                                    st.markdown(f"**{ev.get('agent', '')} · {ev['name']}**")
                                st.caption("input")
                                st.code(json.dumps(ev["input"], indent=2), language="json")
                                st.caption("output")
                                st.code(ev["output"], language="json", wrap_lines=True)
                    st.divider()


        def describe_block(block: dict) -> str:
            if "text" in block:
                text = block["text"].replace("\n", " ")
                return text if len(text) <= 90 else text[:90] + "…"
            if "toolUse" in block:
                return f"🔧 call `{block['toolUse']['name']}({json.dumps(block['toolUse']['input'])})`"
            if "reasoningContent" in block:
                text = block["reasoningContent"].get("reasoningText", {}).get("text", "").replace("\n", " ")
                return f"💭 thinking · *{text[:80]}…*" if text else "💭 thinking"
            if "toolResult" in block:
                content = " ".join(c.get("text", "") for c in block["toolResult"].get("content", []))
                return f"↩️ result `{content[:70]}`"
            return f"`{next(iter(block))}`"


        with context_col:
            context = tracer.context
            messages = context.get("messages", [])
            st.markdown(f"**Context** · sent on the last model call · {len(messages)} message(s)")
            with st.container(border=True):
                if not context:
                    st.caption("The model only sees what's sent here. It keeps nothing between calls.")
                else:
                    if context["system"]:
                        st.markdown(f"⚙️ **system** · {describe_block({'text': context['system']})}")
                    if context["tools"]:
                        st.markdown(f"🧰 **tools** · {', '.join(f'`{t}`' for t in context['tools'])}")
                    for i, msg in enumerate(messages, 1):
                        icon = "👤" if msg["role"] == "user" else "🤖"
                        for block in msg["content"]:
                            st.markdown(f"{i}. {icon} **{msg['role']}** · {describe_block(block)}")
                    if tracer.reply:
                        st.caption("↳ the model's reply (output, not part of what it received)")
                        for block in tracer.reply:
                            st.markdown(f"🤖 **reply** · {describe_block(block)}")
                    with st.expander("Raw JSON"):
                        st.json(context, expanded=False)


last_idx = st.session_state.get("last_idx")
direction = "none" if last_idx is None or last_idx == idx else ("next" if idx > last_idx else "prev")
st.session_state["last_idx"] = idx
slide = st.container(key=f"slide-{direction}-{idx}")
area_col, chat_col = slide.columns([1, 1], gap="medium")
if show_tree:
    strip_col, files_col, code_col = area_col.columns([0.035, 0.32, 1], gap="small")
else:
    strip_col, code_col = area_col.columns([0.035, 1], gap="small")
with strip_col, st.container(key="filesstrip"):
    st.button("‹" if show_tree else "›", key="files_btn", help="Hide the file tree" if show_tree else "Show the file tree",
              on_click=lambda: st.session_state.update(show_tree=not show_tree))

# ── file explorer ────────────────────────────────────────────────────────
files = [section["dir"] / f for f in section_files(section)]
# every file gets an index; tabs and tree rows pick a file in the browser (no rerun), see PAGE_JS
all_files = files + SHARED_FILES
file_index = {f: i for i, f in enumerate(all_files)}


FILE_ICONS = {".py": ":material/code:", ".md": ":material/article:", ".toml": ":material/tune:",
              ".json": ":material/data_object:"}
FILE_ICON_HTML = {s: f'<span class="ficon">{n}</span>' for s, n in
                  {".py": "code", ".md": "article", ".toml": "tune", ".json": "data_object"}.items()}


def tree_folder(name: str, depth: int, key: str) -> None:
    with st.container(key=f"tree-{depth}-{key}"):
        st.markdown(f":material/folder_open: {name}/")


def tree_file(path: Path, depth: int, key: str) -> None:
    i = file_index[path]
    with st.container(key=f"tree-{depth}-{key}"):
        st.markdown(f'<span class="tree-file pick-{i} tf-{i}">{FILE_ICON_HTML.get(path.suffix, "📄")} '
                    f'{html.escape(path.name)}</span>', unsafe_allow_html=True)


def file_tree() -> None:
    """The section's files as a compact, indented tree, then the shared files."""
    tree_folder(section["dir"].name, 0, "root")
    shown_dirs = set()
    for i, path in enumerate(files):
        rel = path.relative_to(section["dir"])
        for depth, parent in enumerate(reversed(rel.parents[:-1]), start=1):
            if parent not in shown_dirs:
                shown_dirs.add(parent)
                tree_folder(parent.name, depth, f"d{len(shown_dirs)}")
        tree_file(path, len(rel.parts), f"s{i}")
    tree_folder("common (shared)", 0, "common")
    for i, path in enumerate(SHARED_FILES):
        tree_file(path, 1, f"c{i}")

if show_tree:
    with files_col, st.container(key="explorer"):
        file_tree()

# ── code pane ────────────────────────────────────────────────────────────
# Edit mode: an Ace editor (in its own frame), styled like the read-only code view
EDITOR_LANGS = {".py": "python", ".md": "markdown", ".toml": "toml", ".json": "json"}
EDITOR_LINES = [27, 27]  # fills the code box on a 900 px screen; it scrolls inside on smaller ones
EDITOR_OPTIONS = {"fontFamily": "'Cascadia Code', Menlo, monospace", "fontSize": 14, "showPrintMargin": False,
                  "showGutter": True, "showLineNumbers": True,
                  "wrap": True, "tabSize": 4, "highlightActiveLine": True}
EDITOR_CSS = """
@font-face { font-family: 'Cascadia Code'; src: url('/app/static/fonts/CascadiaCode.ttf'); font-weight: 200 700; }
.ace_editor, .ace_editor * { font-family: 'Cascadia Code', Menlo, monospace !important; }
.ace_editor, .ace_scroller, .ace_content { background: #f6f1e6 !important; color: #1e1e1e; }
.ace_gutter { background: #f6f1e6 !important; color: #a8998a !important; }
.ace_gutter-cell { color: #a8998a !important; }
.ace_marker-layer .ace_active-line, .ace_gutter-active-line { background: rgba(152, 122, 100, 0.10) !important; }
.ace_marker-layer .ace_selection { background: rgba(152, 122, 100, 0.28) !important; }
.ace_cursor { color: #987a64 !important; }
.ace_keyword, .ace_storage { color: #1f6feb !important; }
.ace_string { color: #1a7f37 !important; }
.ace_comment { color: #8a8072 !important; font-style: italic; }
.ace_constant.ace_numeric, .ace_constant.ace_language { color: #c2410c !important; }
.ace_support.ace_function, .ace_entity.ace_name.ace_function { color: #1f6feb !important; font-weight: 600; }
.ace_identifier { color: #1e1e1e !important; }
"""

COMMENT_STYLES = {".py": "# {}", ".toml": "# {}", ".yaml": "# {}", ".md": "<!-- {} -->"}


def with_path_comment(path: Path, text: str, note: str = "") -> str:
    """Show the file's path as its first line, written as a comment in the file's own language."""
    style = COMMENT_STYLES.get(path.suffix)
    return f"{style.format(path.as_posix() + note)}\n{text}" if style else text


with code_col:
    # File tabs sit on the code box and switch files in the browser, so they never interrupt a running agent.
    # ✎ (a Streamlit button) toggles edit mode; at the right edge: the diff switch, or ↺ / ▶ Run while editing.
    edits = st.session_state.setdefault("edits", {})  # in-memory only; a refresh restores the files
    editing_path = st.session_state.get("editing")
    if editing_path not in files:
        editing_path = st.session_state["editing"] = None
    names = [f.name for f in files]
    labels = [f"{f.parent.name}/{f.name}" if names.count(f.name) > 1 else f.name for f in files]
    labels += [f.as_posix() for f in SHARED_FILES]

    def toggle_edit(f: Path) -> None:
        st.session_state["editing"] = None if st.session_state.get("editing") == f else f

    code_area = st.container(key="codearea")  # tabs on top; the code box takes the height that's left
    tab_row = code_area.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom",
                                  gap=None, wrap=False, key="tabrow")
    tabs = tab_row.container(horizontal=True, gap=None, width="content", wrap=True, key="filetabs")
    for i, (label, f) in enumerate(zip(labels, all_files)):
        tab = tabs.container(horizontal=True, gap=None, width="content", vertical_alignment="center", key=f"tab_{i}")
        tab.markdown(f'<span class="tab-name pick-{i}">{html.escape(label)}{" ●" if f in edits else ""}</span>',
                     unsafe_allow_html=True)
        if f.suffix in (".py", ".md") and f.is_relative_to(section["dir"]):
            tab.button("✎", key=f"pen_{i}" + ("_on" if f == editing_path else ""), type="tertiary",
                       help="Leave edit mode" if f == editing_path else "Edit (in memory only)",
                       on_click=toggle_edit, args=(f,))
    controls = tab_row.container(horizontal=True, gap="small", width="content", vertical_alignment="center",
                                 wrap=False, key="tabcontrols")
    base_dir = Path(section.get("compare_to") or SECTIONS[idx - 1]["dir"]) if idx else None
    run_clicked = False
    if editing_path:
        path = editing_path
        current = edits.get(path, path.read_text())
        if controls.button("↺", key="restore_btn", type="tertiary", disabled=path not in edits,
                           help="Back to the original file"):
            edits.pop(path, None)
            st.session_state["editing"] = None
            rebuild_section(section, session, f"↺ {path.name} restored to the original",
                            {path.parent.name} if path.name == "SKILL.md" else set())
            st.rerun()
        run_clicked = controls.button("▶ Run", key="run_btn", type="tertiary", help="Run the edited code")
        with code_area.container(height=480, key="codepane"):
            response = code_editor(current, lang=EDITOR_LANGS.get(path.suffix, "text"), height=EDITOR_LINES,
                                   response_mode="debounce", options=EDITOR_OPTIONS,
                                   component_props={"css": EDITOR_CSS}, key=f"editor::{path}::{len(session['messages'])}")
        edited = response["text"] if response and response.get("text") else current
        if run_clicked:
            if edited != path.read_text():
                edits[path] = edited
            else:
                edits.pop(path, None)
            st.session_state["editing"] = None
            rebuild_section(section, session, f"✎ {path.name} edited · the agent now runs the new code",
                            {path.parent.name} if path.name == "SKILL.md" else set())
            st.rerun()
    else:
        if base_dir is not None:  # a plain switch: flipping it happens in the browser
            controls.markdown(f'<div id="diff-switch" title="Show changes vs {html.escape(base_dir.as_posix())}">'
                              '<span class="knob"></span></div>', unsafe_allow_html=True)
        with code_area.container(height=480, key="codepane"):
            for i, f in enumerate(all_files):  # every file is drawn; the browser shows the picked one
                current = edits.get(f, f.read_text())
                language = LANGUAGES.get(f.suffix, "text")
                with st.container(key=f"fileview-{i}"):
                    if base_dir is not None and f.is_relative_to(section["dir"]):
                        prev_path = base_dir / f.relative_to(section["dir"])
                        previous = prev_path.read_text() if prev_path.exists() else ""
                        diff = list(difflib.unified_diff(
                            previous.splitlines(), current.splitlines(),
                            fromfile=prev_path.as_posix() if previous else "/dev/null",
                            tofile=f.as_posix(), lineterm="", n=3,
                        ))
                        with st.container(key=f"view_diff-{i}"):
                            if diff:  # the ---/+++ header lines already name both files
                                st.code("\n".join(diff), language="diff", wrap_lines=True)
                            else:
                                st.code(with_path_comment(f, current, f" · unchanged vs {base_dir.name}"),
                                        language=language, line_numbers=True, wrap_lines=True)
                        with st.container(key=f"view_plain-{i}"):
                            st.code(with_path_comment(f, current), language=language, line_numbers=True, wrap_lines=True)
                    else:
                        st.code(with_path_comment(f, current), language=language, line_numbers=True, wrap_lines=True)
    # which file is shown, and which tab / tree row is highlighted, follows body[data-file] (set by PAGE_JS)
    picks = "\n".join(
        f'body[data-file="{i}"] .st-key-fileview-{i} {{ display: flex !important; }}\n'
        f'body[data-file="{i}"] .st-key-tab_{i} {{ background: #f6f1e6; }}\n'
        f'body[data-file="{i}"] .st-key-tab_{i} .tab-name, body[data-file="{i}"] .tf-{i} {{ font-weight: 600; color: #1e1e1e; }}\n'
        f'body[data-file="{i}"] .tf-{i} {{ background: rgba(152,122,100,0.18); }}'
        for i in range(len(all_files)))
    st.markdown(f"<style>[class*='st-key-fileview-'] {{ display: none !important; }}\n{picks}</style>",
                unsafe_allow_html=True)


PHOTOS = Path("assets/photos")


def stop_icon(name: str) -> str:
    import common.data as data
    restaurants = [r["name"].split(" (")[0].lower() for city in data.RESTAURANTS.values() for r in city]
    meal = any(word in name.lower() for word in ("lunch", "dinner", "breakfast", "cafe", "ramen"))
    return "🍽️" if meal or any(r in name.lower() for r in restaurants) else "📍"


def render_itinerary(itinerary: dict) -> None:
    """Structured output rendered as cards instead of markdown."""
    st.markdown(f"#### 🗾 {itinerary['title']}")
    st.caption(f"👥 {itinerary['travellers']}")
    for day in itinerary["days"]:
        with st.container(border=True):
            st.markdown(f"**{day['day']} · {day['city']}** — ☁️ {day['weather']}")
            for stop in day["stops"]:
                photo_col, text_col = st.columns([1, 2.2], vertical_alignment="center")
                photo = PHOTOS / f"{stop['photo']}.jpg" if stop.get("photo") else None
                if photo and photo.exists():
                    photo_col.image(str(photo), width="stretch")
                else:  # restaurants and a few places have no photo: a tile the same size instead
                    photo_col.markdown(f'<div class="nophoto">{stop_icon(stop["name"])}</div>', unsafe_allow_html=True)
                where = "🏠 indoor" if stop["indoor"] else "🌳 outdoor"
                text_col.markdown(f"**{stop['time']} · {stop['name']}**  \n{stop['why']}  \n`{where}`")
    if itinerary.get("tips"):
        st.markdown("\n".join(f"- 💡 {tip}" for tip in itinerary["tips"]))
    with st.expander("Raw JSON"):
        st.json(itinerary, expanded=False)


def team_graph(agent, states: dict[str, str]) -> str:
    """Graphviz DOT for a multi-agent graph, coloured by each member's state."""
    colours = {"waiting": "#f6f1e6", "working": "#e3b26b", "done": "#a9c19a"}
    lines = ['digraph { rankdir=LR; bgcolor="transparent";',
             'node [shape=box, style="rounded,filled", fontname="Palatino", fontcolor="#1e1e1e", color="#987a64"];',
             'edge [color="#987a64"];', 'user [label="👤 request", fillcolor="#d0b49f"];']
    entry = {n.node_id for n in agent.entry_points}
    for node_id in agent.nodes:
        state = states.get(node_id, "waiting")
        lines.append(f'"{node_id}" [label="{node_id}\\n{state}", fillcolor="{colours[state]}"];')
        if node_id in entry:
            lines.append(f'user -> "{node_id}";')
    for edge in agent.edges:
        lines.append(f'"{edge.from_node.node_id}" -> "{edge.to_node.node_id}";')
    return "\n".join(lines + ["}"])


def render_message(container, msg: dict) -> None:
    if msg["role"] == "note":  # e.g. "agent.py edited": a divider, not a chat bubble
        container.caption(f"— {msg['content']} —")
        return
    with container.chat_message(msg["role"]):
        if msg.get("photo"):
            st.image(msg["photo"], width=220)
        if msg.get("graph"):
            st.graphviz_chart(msg["graph"])
        if msg.get("thinking"):
            with st.expander("💭 Thinking", expanded=False):
                st.markdown(msg["thinking"])
        for member, output in (msg.get("team") or {}).items():
            with st.expander(f"🧑‍💼 {member}"):
                st.markdown(output)
        if msg.get("structured"):
            render_itinerary(msg["structured"])
        elif msg.get("content"):
            st.markdown(msg["content"])


def user_content(prompt: str, photo: str | None):
    """Plain text, or a text + image message when a photo is attached."""
    if not photo:
        return prompt
    image_format = "png" if photo.lower().endswith(".png") else "jpeg"
    return [{"text": prompt}, {"image": {"format": image_format, "source": {"bytes": Path(photo).read_bytes()}}}]


async def stream_reply(agent, content, on_progress=None) -> tuple[dict, object]:
    """Consume stream_async() and update the chat as events arrive.

    Works for a single agent and for a multi-agent graph, whose events wrap
    each member's events in a multiagent_node_stream envelope.
    """
    is_team = hasattr(agent, "nodes")
    graph_box = st.empty()
    thinking_box = st.empty()
    status = st.empty()
    text_box = st.empty()
    states: dict[str, str] = {}
    thinking, text, result = "", "", None
    if is_team:
        graph_box.graphviz_chart(team_graph(agent, states))
    seen_events, last_refresh = len(tracer.events), 0.0
    text_calls = len(tracer.calls)
    async for event in agent.stream_async(content):
        # keep the Trace & Context drawer live: on every new model/tool call, and twice a second
        if on_progress and (len(tracer.events) != seen_events or time.monotonic() - last_refresh > 0.5):
            seen_events, last_refresh = len(tracer.events), time.monotonic()
            on_progress(text or "…")
        kind = event.get("type")
        if kind in ("multiagent_node_start", "multiagent_node_stop"):
            states[event["node_id"]] = "working" if kind == "multiagent_node_start" else "done"
            graph_box.graphviz_chart(team_graph(agent, states))
            continue
        if kind == "multiagent_result":
            result = event["result"]
            continue
        node_id = event.get("node_id")
        if kind == "multiagent_node_stream":
            event = event["event"]
            if "data" in event or "reasoningText" in event:
                tracer.first_token(node_id)
            if node_id != "writer":  # members work in the background; only the writer talks
                if event.get("current_tool_use", {}).get("name"):
                    status.caption(f"🔧 {node_id} is calling `{event['current_tool_use']['name']}`…")
                continue
        if ("data" in event or "reasoningText" in event) and kind != "multiagent_node_stream":
            tracer.first_token()
        if "reasoningText" in event:
            thinking += event["reasoningText"]
            with thinking_box.container():
                with st.expander("💭 Thinking…", expanded=True):
                    st.markdown(thinking)
        elif "data" in event:
            if len(tracer.calls) != text_calls and text and not text.endswith(("\n", " ")):
                text += "\n\n"  # a new model call (e.g. after tools) starts a new paragraph
            text_calls = len(tracer.calls)
            text += event["data"]
            text_box.markdown(text + " ▌")
        elif "current_tool_use" in event and event["current_tool_use"].get("name"):
            status.caption(f"🔧 calling `{event['current_tool_use']['name']}`…")
        elif "result" in event and not is_team:
            result = event["result"]
    status.empty()
    structured = getattr(result, "structured_output", None)
    reply = {
        "content": text,
        "thinking": thinking,
        "structured": structured.model_dump() if structured is not None else None,
    }
    if is_team and result is not None:
        reply["team"] = {n: str(r.result) for n, r in result.results.items() if n != "writer"}
        reply["graph"] = team_graph(agent, states)
    return reply, result


# ── chat pane ────────────────────────────────────────────────────────────
with chat_col:
    st.markdown(f"**Chat** · `{PROVIDER}`")
    if not hasattr(session["agent"], "add_hook") and not hasattr(session["agent"], "nodes") \
            and not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("This section calls the Claude API directly, so it needs ANTHROPIC_API_KEY in .env.")
    history = st.container(height=420, key="chathistory")
    for msg in session["messages"]:
        render_message(history, msg)

    # Scripted prompts stay hidden until the presenter clicks the empty chat box: a menu then lists them
    # (next one pre-selected, sent ones ticked), and picking one puts it in the box to review and send.
    script = [{"text": t, "photo": None} for t in section["prompts"]] + [
        {"text": pp["text"], "photo": pp["photo"]} for pp in section.get("photo_prompts", [])]
    sent = session.setdefault("script_sent", set())
    menu = [{"text": item["text"], "photo": bool(item["photo"]), "sent": i in sent} for i, item in enumerate(script)]
    photo = None
    typed = st.chat_input("Ask your assistant…", accept_file=bool(section.get("photo_prompts")),
                          file_type=["jpg", "jpeg", "png"])
    # Our own script (the prompts come from chapters.toml, never from users or models).
    st.iframe(page_bootstrap(menu), height=1)
    if typed is not None and not isinstance(typed, str):  # accept_file returns text + files
        if typed.files:
            upload = Path("/tmp") / typed.files[0].name
            upload.write_bytes(typed.files[0].getvalue())
            photo = str(upload)
        typed = typed.text
    prompt = typed
    if prompt:  # a scripted prompt is ticked off and brings its photo
        for i, item in enumerate(script):
            if prompt.strip() == item["text"]:
                photo = photo or item["photo"]
                sent.add(i)
                break

    if prompt:
        session["messages"].append({"role": "user", "content": prompt, "photo": photo})
        render_message(history, session["messages"][-1])
        tracer.events.append({"kind": "user", "text": prompt + (" 📷" if photo else ""), "t0": time.perf_counter()})
        with history.chat_message("assistant"):
            if section.get("streaming"):
                reply, result = asyncio.run(stream_reply(session["agent"], user_content(prompt, photo), render_inspector))
            else:
                with st.spinner("Waiting for the full answer…"):
                    result = session["agent"](prompt)
                reply = {"content": str(result)}
        if hasattr(result, "metrics"):
            session["usage"] = result.metrics.accumulated_usage
        elif hasattr(result, "accumulated_usage"):
            session["usage"] = result.accumulated_usage
        session["messages"].append({"role": "assistant", **reply})
        st.rerun()

# the drawer is drawn last on a normal run; while an agent answers, stream_reply refreshes it
render_inspector()
