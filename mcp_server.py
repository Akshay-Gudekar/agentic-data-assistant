from fastmcp import FastMCP
from data_sources import dataset_metadata, sample_rows_text

mcp = FastMCP("file-connector")

@mcp.tool()
def get_schema(csv_path: str) -> dict:
    """Return columns, types, row count, and sample rows for a supported data file."""
    return dataset_metadata(csv_path)

@mcp.tool()
def get_sample_rows(csv_path: str, n: int = 5) -> str:
    """Return sample rows for a supported data file as JSON."""
    return sample_rows_text(csv_path, n)

if __name__ == "__main__":
    mcp.run()