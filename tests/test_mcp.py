"""Protocol-level MCP acceptance test using an in-process v2 client."""

import asyncio
import unittest

from mcp import Client
from resource_radar.server import mcp


class McpTests(unittest.TestCase):
    def test_tools_list_and_status(self):
        async def smoke():
            async with Client(mcp) as client:
                tool_list = await client.list_tools()
                tools = tool_list.tools if hasattr(tool_list, "tools") else tool_list
                names = {t.name for t in tools}
                expected = {"search_resources", "search_userscripts", "inspect_resource", "inspect_script",
                            "compare_resources", "sync_sources", "source_status"}
                self.assertTrue(expected.issubset(names), names)
                result = await client.call_tool("source_status", {})
                self.assertFalse(result.is_error)
        asyncio.run(smoke())


if __name__ == "__main__":
    unittest.main()
