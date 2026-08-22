"""Unit tests for deterministic tool suite."""

import pytest
from pathlib import Path
from proton.security.sandbox import FilesystemSandbox
from proton.tools.filesystem import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool, SearchCodeTool
from proton.tools.coding import ApplyPatchTool
from proton.tools.shell import ShellExecuteTool


@pytest.mark.asyncio
async def test_filesystem_tools(tmp_path: Path):
    sandbox = FilesystemSandbox(tmp_path)
    write_tool = WriteFileTool(sandbox)
    read_tool = ReadFileTool(sandbox)
    edit_tool = EditFileTool(sandbox)
    list_tool = ListDirectoryTool(sandbox)
    search_tool = SearchCodeTool(sandbox)

    # 1. Write file
    w_res = await write_tool.run(path="hello.txt", content="Hello World!\nLine 2")
    assert w_res.get("success") is True

    # 2. Read file
    r_res = await read_tool.run(path="hello.txt")
    assert "Hello World!" in r_res.get("content", "")

    # 3. Edit file
    e_res = await edit_tool.run(path="hello.txt", target_text="Line 2", replacement_text="Line Two")
    assert e_res.get("success") is True
    r_res2 = await read_tool.run(path="hello.txt")
    assert "Line Two" in r_res2.get("content", "")

    # 4. List directory
    l_res = await list_tool.run(path=".")
    assert any(e["name"] == "hello.txt" for e in l_res.get("entries", []))

    # 5. Search code
    s_res = await search_tool.run(query="Line Two")
    assert len(s_res.get("matches", [])) == 1


@pytest.mark.asyncio
async def test_shell_execute_tool(tmp_path: Path):
    sandbox = FilesystemSandbox(tmp_path)
    tool = ShellExecuteTool(sandbox)
    # Safe echo command
    res = await tool.run(command="python -c \"print('Proton Shell Test')\"")
    assert res.get("success") is True
    assert "Proton Shell Test" in res.get("stdout", "")


def test_extract_text_tool_calls():
    from proton.agent.engine import extract_text_tool_calls

    registered = {"read_file", "write_file", "shell_execute"}

    # XML format
    text1 = "<tool_call>{\"name\": \"read_file\", \"arguments\": {\"path\": \"app.py\"}}</tool_call>"
    calls1 = extract_text_tool_calls(text1, registered)
    assert len(calls1) == 1
    assert calls1[0].name == "read_file"
    assert calls1[0].arguments == {"path": "app.py"}

    # Markdown format
    text2 = "```json\n{\"name\": \"write_file\", \"arguments\": {\"path\": \"test.py\", \"content\": \"hello\"}}\n```"
    calls2 = extract_text_tool_calls(text2, registered)
    assert len(calls2) == 1
    assert calls2[0].name == "write_file"
    assert calls2[0].arguments == {"path": "test.py", "content": "hello"}

    # Nested type: function format (as emitted by Llama 3.2 1B)
    text3 = """```
{
    "type": "function",
    "function": {
        "name": "write_file",
        "parameters": {
            "path": "C:\\\\Users\\\\arjun.divekar\\\\Desktop\\\\Proton_is_best",
            "content": "This is a test file.",
            "overwrite": false
        }
    }
}
```"""
    calls3 = extract_text_tool_calls(text3, registered)
    assert len(calls3) == 1
    assert calls3[0].name == "write_file"
    assert calls3[0].arguments["path"] == "C:\\Users\\arjun.divekar\\Desktop\\Proton_is_best"
    assert calls3[0].arguments["content"] == "This is a test file."
