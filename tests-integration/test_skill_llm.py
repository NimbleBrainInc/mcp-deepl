"""
Smoke test: verify the LLM reads the skill resource and selects the correct tool.

Requires ANTHROPIC_API_KEY in environment.
"""

import os

import anthropic
import pytest
from fastmcp import Client

from mcp_deepl.server import mcp


def get_anthropic_client() -> anthropic.Anthropic:
    token = os.environ.get("ANTHROPIC_API_KEY")
    if not token:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=token)


async def get_server_context() -> dict:
    """Extract instructions, skill content, and tool definitions from the MCP server."""
    async with Client(mcp) as client:
        init = await client.initialize()
        instructions = init.instructions

        resources = await client.list_resources()
        skill_text = ""
        for r in resources:
            if "skill://" in str(r.uri):
                contents = await client.read_resource(str(r.uri))
                skill_text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])

        tools_list = await client.list_tools()
        tools = []
        for t in tools_list:
            tool_def = {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            tools.append(tool_def)

        return {
            "instructions": instructions,
            "skill": skill_text,
            "tools": tools,
        }


class TestSkillLLMInvocation:
    """Test that an LLM reads the skill and makes correct tool choices."""

    @pytest.mark.asyncio
    async def test_simple_translation_selects_translate_text(self):
        """When asked to translate, the LLM should call translate_text."""
        ctx = await get_server_context()
        client = get_anthropic_client()

        system = (
            f"You are a translation assistant.\n\n"
            f"## Server Instructions\n{ctx['instructions']}\n\n"
            f"## Skill Resource\n{ctx['skill']}"
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": "Translate 'Hello world' to German"}],
            tools=[{"type": "custom", **t} for t in ctx["tools"]],
        )

        tool_calls = [b for b in response.content if b.type == "tool_use"]
        assert len(tool_calls) > 0, "LLM did not call any tool"

        tool_name = tool_calls[0].name
        assert tool_name == "translate_text", (
            f"LLM called {tool_name} instead of translate_text. "
            "Skill instructs: use translate_text for standard translation."
        )
        assert tool_calls[0].input.get("target_lang") in ("DE", "de")

    @pytest.mark.asyncio
    async def test_check_usage_selects_get_usage(self):
        """When asked about quota, the LLM should call get_usage."""
        ctx = await get_server_context()
        client = get_anthropic_client()

        system = (
            f"You are a translation assistant.\n\n"
            f"## Server Instructions\n{ctx['instructions']}\n\n"
            f"## Skill Resource\n{ctx['skill']}"
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": "How much translation quota do I have left?"}],
            tools=[{"type": "custom", **t} for t in ctx["tools"]],
        )

        tool_calls = [b for b in response.content if b.type == "tool_use"]
        assert len(tool_calls) > 0, "LLM did not call any tool"

        tool_name = tool_calls[0].name
        assert tool_name == "get_usage", (
            f"LLM called {tool_name} instead of get_usage. "
            "Skill instructs: use get_usage for quota checks."
        )

    @pytest.mark.asyncio
    async def test_detect_language_query(self):
        """When asked 'what language is this?', the LLM should call detect_language."""
        ctx = await get_server_context()
        client = get_anthropic_client()

        system = (
            f"You are a translation assistant.\n\n"
            f"## Server Instructions\n{ctx['instructions']}\n\n"
            f"## Skill Resource\n{ctx['skill']}"
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=[
                {"role": "user", "content": "What language is this text: 'Bonjour le monde'?"}
            ],
            tools=[{"type": "custom", **t} for t in ctx["tools"]],
        )

        tool_calls = [b for b in response.content if b.type == "tool_use"]
        assert len(tool_calls) > 0, "LLM did not call any tool"

        tool_name = tool_calls[0].name
        assert tool_name == "detect_language", (
            f"LLM called {tool_name} instead of detect_language. "
            "Skill instructs: use detect_language for language identification."
        )
