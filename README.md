# Flowtic

Build agent workflows that actually talk to each other. No complex orchestration, just simple communication patterns that work.

## What it does

- **Agent sessions**: Each agent keeps its own conversation history (text + images)
- **Tool system**: Write functions once, agents use them automatically
- **Communication graph**: Tell agents who can talk to whom with simple syntax
- **Callbacks**: Hook into conversations for logging, user input, whatever you need

## Install

```bash
pip install git+https://github.com/PrAsAnNaRePo/Flowtic.git
```

## Quick start

### Single agent with tools

```python
from flowtic import Agent, Tool, Tools

def calculate(expression: str):
    return str(eval(expression)), None

calc_tool = Tool(
    tool_definition={
        "type": "function",
        "function": {
            "name": "calculate", 
            "description": "Calculate math expressions",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"}
                },
                "required": ["expression"]
            }
        }
    },
    tool_execution=calculate
)

agent = Agent(
    agent_name="calculator",
    model_name="gpt-4o",  # any litellm model
    instructions="You help with math problems.",
    tools=Tools([calc_tool])
)

result = agent("What's 15 * 23?")
```

### Multi-agent workflow

```python
from flowtic import Agent, CommunicationProtocol

# Create agents
analyst = Agent(
    agent_name="analyst",
    model_name="gpt-4o",
    instructions="Analyze requirements and ask clarifying questions.",
    allow_user_input=True  # can talk to user
)

coder = Agent(
    agent_name="coder", 
    model_name="gpt-4o",
    instructions="Write code based on requirements.",
    allow_user_input=False  # only talks to other agents
)

# Set up who talks to whom
protocol = CommunicationProtocol(
    "analyst<->coder",  # bidirectional
    [analyst, coder]
)

# Start the workflow
protocol.execute("Build a simple todo app")
```

## Communication patterns

The syntax is dead simple:

- `A->B` means A can send messages to B
- `A<->B` means they can talk both ways  
- `A->B, B->C` chains them together
- `A<->B, A->C` means A talks to both B and C

When agents communicate, they automatically get tools to message each other. No setup needed.

## Images and multimodal

```python
# Agent automatically handles images
agent("Here's a screenshot", images=["path/to/image.png"])

# Works with URLs and base64 too
agent("Analyze this", images=["https://example.com/chart.png"])
```

## Custom callbacks

```python
from flowtic import Callback

class MyCallbacks(Callback):
    def on_user_loop(self, agent_name, message):
        return input(f"{agent_name}: {message}\n> ")
    
    def on_tool_call(self, agent_name, tool_name, args):
        print(f"{agent_name} is using {tool_name}")

agent = Agent(
    agent_name="helper",
    model_name="gpt-4o", 
    callbacks=MyCallbacks()
)
```

## Session management

Each agent keeps its own conversation buffer. Even if multiple agents reuse the same `SessionManager`, their histories stay isolated by agent name:

```python
from flowtic import SessionManager

session_store = SessionManager()

agent1 = Agent(
    agent_name="researcher",
    model_name="gpt-4o",
    session=session_store
)

agent2 = Agent(
    agent_name="writer", 
    model_name="gpt-4o",
    session=session_store
)

# The writer still has its own memory
agent1("Find info about climate change")
agent2("Write a summary based on what the researcher found")
```

If you want agents to share context, use agent-to-agent communication. `CommunicationProtocol` injects `_spin_into`, so one agent can explicitly hand context to another instead of silently sharing history.

Sessions handle images automatically - no extra work needed:

```python
session = SessionManager()

# Add context manually if needed
session.add_user_context("my_agent", 
    text="Here's the data", 
    images=["chart1.png", "chart2.png"]
)

# Get the full conversation
history = session.get_buffer_memory("my_agent")
```

## That's it

Three main pieces: agents that remember conversations, tools they can use, and simple rules for who talks to whom. Everything else just works.
