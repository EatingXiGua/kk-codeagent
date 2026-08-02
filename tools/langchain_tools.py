from langchain_core.tools import StructuredTool

from tools.tool_manager import ToolManager


def build_langchain_tools(tool_manager: ToolManager) -> list[StructuredTool]:
    def list_files(
        path: str = ".",
        recursive: bool = False,
        max_results: int = 200,
    ) -> str:
        """List files and directories in the workspace."""
        return tool_manager.execute(
            "list_files",
            {
                "path": path,
                "recursive": recursive,
                "max_results": max_results,
            },
        )

    def read_file(
        path: str,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> str:
        """Read a text file in the workspace with line numbers."""
        return tool_manager.execute(
            "read_file",
            {
                "path": path,
                "start_line": start_line,
                "end_line": end_line,
            },
        )

    def search_code(
        query: str,
        path: str = ".",
        file_pattern: str | None = None,
        case_sensitive: bool = False,
        max_results: int = 100,
    ) -> str:
        """Search text files in the workspace for a keyword."""
        return tool_manager.execute(
            "search_code",
            {
                "query": query,
                "path": path,
                "file_pattern": file_pattern,
                "case_sensitive": case_sensitive,
                "max_results": max_results,
            },
        )

    def write_file(
        path: str,
        content: str,
        overwrite: bool = True,
    ) -> str:
        """Create or overwrite a text file in the workspace."""
        return tool_manager.execute(
            "write_file",
            {
                "path": path,
                "content": content,
                "overwrite": overwrite,
            },
        )

    def run_command(
        command: str,
        timeout: int | None = None,
    ) -> str:
        """Run an allowed command in the workspace root."""
        return tool_manager.execute(
            "run_command",
            {
                "command": command,
                "timeout": timeout,
            },
        )

    return [
        StructuredTool.from_function(
            func=list_files,
            name="list_files",
            description="List files and directories in the workspace.",
        ),
        StructuredTool.from_function(
            func=read_file,
            name="read_file",
            description="Read a text file in the workspace with line numbers.",
        ),
        StructuredTool.from_function(
            func=search_code,
            name="search_code",
            description="Search text files in the workspace for a keyword.",
        ),
        StructuredTool.from_function(
            func=write_file,
            name="write_file",
            description="Create or overwrite a text file in the workspace.",
        ),
        StructuredTool.from_function(
            func=run_command,
            name="run_command",
            description="Run an allowed command in the workspace root.",
        ),
    ]
