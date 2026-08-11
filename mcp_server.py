from fastmcp import FastMCP
import pandas as pd

mcp = FastMCP("file-connector")

@mcp.tool()
def get_schema(csv_path: str) -> dict:
    """Return column names and dtypes for a CSV file."""
    df = pd.read_csv(csv_path)
    return {
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "row_count": len(df)
    }

@mcp.tool()
def get_sample_rows(csv_path: str, n: int = 5) -> str:
    """Return the first n rows of a CSV file as a string."""
    df = pd.read_csv(csv_path)
    return df.head(n).to_string()

if __name__ == "__main__":
    mcp.run()