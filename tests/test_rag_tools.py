import json

from tools.rag_tools import retrieve_kpi_context


def test_retail_context_is_grounded_to_source():
    result = json.loads(retrieve_kpi_context("retail", "margin and inventory"))
    assert result["industry"] == "retail"
    assert result["source"].endswith("retail.md")
    assert result["retrieval_method"] == "tfidf_cosine_vector"
    assert result["guidance"]
    assert result["top_match_score"] > 0


def test_unknown_industry_lists_supported_values():
    result = json.loads(retrieve_kpi_context("unknown"))
    assert "error" in result
    assert "saas" in result["available_industries"]
