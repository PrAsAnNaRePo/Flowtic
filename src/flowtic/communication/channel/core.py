from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from flowtic.agents import Agent
import re
from collections import defaultdict
from flowtic.agents.tools import Tool

class CommunicationProtocol:
    def __init__(
        self,
        logic_str: str,
        agents: List['Agent'],
        async_run_type = False,
        *,
        verbose: bool = False,
    ) -> None:
        self.logic_str = logic_str
        self.agents = agents
        self.verbose = verbose
        
        self.mapping = self._parse_communication(logic_str)
        if not self.mapping:
            raise ValueError("Communication protocol cannot be empty")
        
        self.async_run_type = async_run_type
        self.agent_map = {agents[i].name: agents[i] for i in range(len(agents))}
        self._communication_validation()
        if self.verbose:
            self.print_graph_as_tree()
        for item in self.mapping.items():
            self._inject_handsoff(item[0], item[1])


    def _parse_communication(self, sequence: str):
        pattern = re.compile(r'\s*(\w+)\s*(<->|->)\s*(\w+)\s*')
        graph = defaultdict(list)

        for fragment in sequence.split(','):
            m = pattern.fullmatch(fragment.strip())
            if not m:
                raise ValueError(f"Un-parsable fragment: {fragment!r}")
            src, arrow, dst = m.groups()

            graph[src].append(dst)
            if arrow == '<->':
                graph[dst].append(src)

        return {n: list(dict.fromkeys(neigh)) for n, neigh in graph.items()}
    
    def parse_agents(self):
        agents = []
        agents.extend(list(self.mapping.keys()))
        _vals = [j for i in list(self.mapping.values()) for j in i]
        agents.extend(_vals)
        return list(dict.fromkeys(agents))
    
    def _communication_validation(self):
        protocol_agents = set(self.parse_agents())
        provided_agents = set(self.agent_map)

        if protocol_agents != provided_agents:
            missing_agents = sorted(protocol_agents - provided_agents)
            extra_agents = sorted(provided_agents - protocol_agents)
            errors = []
            if missing_agents:
                errors.append(f"Missing agents: {missing_agents}")
            if extra_agents:
                errors.append(f"Unexpected agents: {extra_agents}")
            raise ValueError(". ".join(errors))            

    def print_graph_as_tree(self):
        targets = {t for vals in self.mapping.values() for t in vals}
        roots   = [n for n in self.mapping if n not in targets] or list(self.mapping.keys())

        def dfs(node, prefix="", visited=None, is_last=True):
            if visited is None:
                visited = set()
            looped = node in visited
            branch = "└── " if is_last else "├── "
            print(prefix + branch + node + (" (↺)" if looped else ""))
            if looped:
                return
            visited.add(node)

            children = self.mapping.get(node, [])
            for i, child in enumerate(children):
                dfs(child,
                    prefix + ("    " if is_last else "│   "),
                    visited,
                    i == len(children) - 1)

        visited = set()
        for i, root in enumerate(roots):
            dfs(root, "", visited, i == len(roots) - 1)
            if i != len(roots) - 1:
                print()

    def get_connected_agents(self, agent_name: str):
        return self.mapping.get(agent_name, [])

    def _format_handoff_message(self, sender: str, receiver: str, message: str, context: str) -> str:
        prefix = f"Hey {receiver}, It's {sender} here (not the user, don't get confused)."
        cleaned_context = context.strip()
        cleaned_message = message.strip()

        if cleaned_context:
            return f"{prefix} {cleaned_context}\n\n{cleaned_message}"

        return f"{prefix}\n\n{cleaned_message}"

    def _validate_receiver(self, sender: str, receiver: str) -> None:
        allowed_receivers = self.get_connected_agents(sender)
        if receiver not in allowed_receivers:
            raise ValueError(f"Agent {sender} cannot communicate with {receiver}. Allowed receivers: {allowed_receivers}")
    
    def _inject_handsoff(self, agent: str, recievers: List[str]):
        self.agent_map.get(agent).add_tool(
            Tool(
                tool_definition={
                    "type": "function",
                    "function": {
                        "name": f"{self._async_spin_into.__name__ if self.async_run_type else self._spin_into.__name__}",
                        "description": "Use this tool to communicate with other agents",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "receiver": {
                                    "type": "string",
                                    "description": f"you must have to mention receiver name clearly as it is. Only allowed to {','.join([i for i in recievers])}",
                                },
                                "message": {
                                    "type": "string",
                                    "description": "This includes the main task, goal or whatever the important information you want to pass to the receiver",
                                },
                                "context": {
                                    "type": "string",
                                    "description": "This includes the additional context, your reasoning, etc. of the conversation so far",
                                },
                            },
                            "required": ["receiver", "message", "context"],
                        },
                    },
                },
                tool_execution=self._async_spin_into if self.async_run_type else self._spin_into,
                )
        )

    def _collect_output(self, messages):
        output_parts = []

        for msg in messages:
            if isinstance(msg, dict) and msg.get('role') == 'tool':
                content = msg.get('content', '')
                if content and content != 'None':
                    output_parts.append(content)
            elif hasattr(msg, 'role') and msg.role == 'assistant' and msg.content:
                output_parts.append(msg.content)

        if output_parts:
            return output_parts[-1]

        return None

    def _spin_up(self, agent_name: str, input: str, images: Optional[List] = None):
        agent = self.agent_map.get(agent_name)
        if agent is None:
            raise ValueError(f"No agent found called {agent_name}")
        
        original_buffer = agent.session.get_buffer_memory(tag=agent.name)
        original_length = len(original_buffer)
        
        output = agent(input, images=images)
        if output is not None:
            return output
        
        updated_buffer = agent.session.get_buffer_memory(tag=agent.name)
        new_messages = updated_buffer[original_length:]

        return self._collect_output(new_messages) or f"{agent_name} completed the request"

    async def _async_spin_up(self, agent_name: str, input: str, images: Optional[List] = None):
        agent = self.agent_map.get(agent_name)

        if agent is None:
            raise ValueError(f"No agent found called {agent_name}")

        original_buffer = agent.session.get_buffer_memory(tag=agent.name)
        original_length = len(original_buffer)

        output = await agent(input, images=images)
        if output is not None:
            return output

        updated_buffer = agent.session.get_buffer_memory(tag=agent.name)
        new_messages = updated_buffer[original_length:]

        return self._collect_output(new_messages) or f"{agent_name} completed the request"
        
    def _spin_into(self, sender: str, receiver: str, message: str, context: str):
        self._validate_receiver(sender, receiver)
        return self._spin_up(receiver, self._format_handoff_message(sender, receiver, message, context)), None

    async def _async_spin_into(self, sender: str, receiver: str, message: str, context: str):
        self._validate_receiver(sender, receiver)
        return await self._async_spin_up(
            receiver,
            self._format_handoff_message(sender, receiver, message, context),
        ), None

    def execute(self, input: str, images: Optional[List] = None, start_agent: Optional[str] = None):
        prior_agent_name = start_agent or list(self.mapping.keys())[0]

        return self._spin_up(prior_agent_name, input, images=images)

    async def async_execute(self, input: str, images: Optional[List] = None, start_agent: Optional[str] = None):
        prior_agent_name = start_agent or list(self.mapping.keys())[0]

        return await self._async_spin_up(prior_agent_name, input, images=images)

    async def asyn_execute(self, input: str, images: Optional[List] = None, start_agent: Optional[str] = None):
        return await self.async_execute(input, images=images, start_agent=start_agent)
