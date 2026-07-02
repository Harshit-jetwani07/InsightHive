"""Dataset ingestion specialist."""

from google.adk.agents import LlmAgent

from agents.config import MODEL_NAME, deterministic_config
from tools.data_tools import get_dataset_overview, parse_uploaded_dataset

ingestion_agent = LlmAgent(
    model=MODEL_NAME,
    name="ingestion_agent",
    description="Loads confined CSV or Excel uploads and verifies their schema.",
    generate_content_config=deterministic_config(),
    instruction="""You are the dataset ingestion gate.
For a saved upload, call parse_uploaded_dataset with the exact provided filename
and username. Then call get_dataset_overview to verify rows, columns, and schema.
Never invent a path and never access files outside the uploads directory.
""",
    tools=[parse_uploaded_dataset, get_dataset_overview],
)
