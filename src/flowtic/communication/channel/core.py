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
        agents: List['Agent']
    ) -> None:
        self.logic_str = logic_str
        self.agents = agents
        
        self.mapping = self._parse_communication(logic_str)
        assert all(agent.name in self.parse_agents() for agent in agents), "All agents must be present in the communication protocol"
        assert len(self.parse_agents()) == len(agents), "All agents must be present in the communication protocol"
        self.agent_map = {agents[i].name: agents[i] for i in range(len(agents))}
        self.print_graph_as_tree()
        self._communication_validation()
        for item in self.mapping.items():
            self._inject_handsoff(item[0], item[1])
        
        self.communication_tracer = []

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
        agents = list(set(agents))
        return agents
    
    def _communication_validation(self):        
        agents = self.parse_agents()

        not_found = []
        for a in agents:
            if a not in [j for i in list(self.mapping.values()) for j in i]:
                not_found.append(a)
        if sorted(agents)[0] in not_found:
            not_found.remove(sorted(agents)[0])

        if not_found:
            raise ValueError(f"Agents {not_found} should be receiving input from other agents")            

    def print_graph_as_tree(self):
        targets = {t for vals in self.mapping.values() for t in vals}
        roots   = [n for n in self.mapping if n not in targets] or list(self.mapping.keys())

        def dfs(node, prefix="", visited=set(), is_last=True):
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
    
    def _inject_handsoff(self, agent: str, recievers: List[str]):
        for receiver in recievers:
            self.agent_map.get(agent).add_tool(
                Tool(
                    tool_definition={
                        "type": "function",
                        "function": {
                            "name": f"{self._spin_into.__name__}",
                            "description": f"Use this tool to communicate with {receiver}",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "receiver": {
                                        "type": "string",
                                        "description": f"you must have to mention {receiver} name clearly as it is.",
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
                    tool_execution=self._spin_into,
                )
            )

    def _spin_up(self, agent_name: str, input: str):
        agent = self.agent_map.get(agent_name)
        return agent(input)
    
    def _spin_into(self, sender: str, receiver: str, message: str, context: str):
        self.communication_tracer.append((sender, receiver))
        if receiver in [pair[0] for pair in self.communication_tracer]:
            active_listr = None
            for pair in self.communication_tracer:
                if receiver in pair:
                    active_listr = pair
                    break
            
            if active_listr[1] == sender:
                return f"Hey {receiver}, it's {sender} here (not the user, don't get confused). {context}\n\n{message}", None
            else:
                return f"Hey {receiver}, it's {sender} here (neither the user nor {active_listr[1]}, don't get confused). {context}\n\n{message}", None
        
        return self._spin_up(receiver, f"It's {receiver} here (not the user, don't get confused). {context}\n\n{message}"), None

    def execute(self, input: str, images: Optional[List] = None):
        prior_agent_name = list(self.mapping.keys())[0]

        self._spin_up(prior_agent_name, input)
