# KPI Playbooks MCP Server

Run over stdio:

```bash
python mcp_server/kpi_templates_server.py
```

Exposed capability:

- Tool: `get_industry_kpi_playbook(industry, question)`
- Resource: `kpi://industries`

The Streamlit app uses the same retrieval implementation locally. The MCP
surface allows ADK or another compatible client to consume the governed
playbooks without duplicating business definitions.
