"""
Tool Registry
Base infrastructure for agent tools (function calling).
"""

import os
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime


class Tool:
    """A single tool that an agent can use."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given arguments."""
        print(f"[TOOL] Executing: {self.name} with args: {list(kwargs.keys())}")
        try:
            result = self.func(**kwargs)
            if isinstance(result, dict):
                return result
            return {'success': True, 'result': result}
        except Exception as e:
            print(f"[TOOL] Error in {self.name}: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def to_openai_schema(self) -> Dict:
        """Convert to OpenAI function-calling schema."""
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': {
                    'type': 'object',
                    'properties': self.parameters,
                    'required': list(self.parameters.keys()),
                },
            },
        }


class ToolRegistry:
    """Registry of tools available to agents."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool
        print(f"[TOOL-REGISTRY] Registered: {tool.name}")

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict] = None,
    ):
        """Decorator to register a function as a tool."""
        def decorator(func: Callable):
            self.register(Tool(
                name=name,
                description=description,
                func=func,
                parameters=parameters,
            ))
            return func
        return decorator

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return {'success': False, 'error': f'Tool not found: {name}'}
        return tool.execute(**kwargs)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())

    def get_schemas(self) -> List[Dict]:
        """Get OpenAI-compatible schemas for all tools."""
        return [tool.to_openai_schema() for tool in self.tools.values()]


def create_agent_toolset(agent) -> ToolRegistry:
    """Create a registry with all tools an agent might need."""
    from .github_tools import register_github_tools
    from .deploy_tools import register_deploy_tools

    registry = ToolRegistry()
    register_github_tools(registry, agent)
    register_deploy_tools(registry, agent)
    return registry