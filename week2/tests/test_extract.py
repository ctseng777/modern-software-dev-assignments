import os
import pytest
from unittest.mock import patch, MagicMock
import json

from ..app.services.extract import extract_action_items, extract_action_items_llm


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


def test_extract_action_items_llm_with_json_response():
    """Test LLM extraction with valid JSON array response."""
    text = """
    Meeting notes:
    - Set up database
    - Implement API endpoint
    - Write tests
    """
    
    mock_response = {
        "output": '["Set up database", "Implement API endpoint", "Write tests"]'
    }
    
    with patch('week2.app.services.extract._call_runpod_api', return_value=mock_response["output"]):
        items = extract_action_items_llm(text)
        assert len(items) == 3
        assert "Set up database" in items
        assert "Implement API endpoint" in items
        assert "Write tests" in items


def test_extract_action_items_llm_with_markdown_code_block():
    """Test LLM extraction when response includes markdown code blocks."""
    text = "TODO: Fix bug, TODO: Add feature"
    
    mock_response = {
        "output": '```json\n["Fix bug", "Add feature"]\n```'
    }
    
    with patch('week2.app.services.extract._call_runpod_api', return_value=mock_response["output"]):
        items = extract_action_items_llm(text)
        assert len(items) == 2
        assert "Fix bug" in items
        assert "Add feature" in items


def test_extract_action_items_llm_with_empty_input():
    """Test LLM extraction with empty input."""
    with patch('week2.app.services.extract._call_runpod_api') as mock_api:
        items = extract_action_items_llm("")
        assert items == []
        mock_api.assert_not_called()


def test_extract_action_items_llm_with_whitespace_only():
    """Test LLM extraction with whitespace-only input."""
    with patch('week2.app.services.extract._call_runpod_api') as mock_api:
        items = extract_action_items_llm("   \n\t  ")
        assert items == []
        mock_api.assert_not_called()


def test_extract_action_items_llm_fallback_on_error():
    """Test that LLM extraction falls back to heuristic method on API error."""
    text = "- [ ] Set up database\n* implement API endpoint"
    
    with patch('week2.app.services.extract._call_runpod_api', side_effect=Exception("API Error")):
        # Should fallback to heuristic extraction
        items = extract_action_items_llm(text)
        # Should still extract items using heuristic method
        assert len(items) > 0


def test_extract_action_items_llm_with_complex_notes():
    """Test LLM extraction with complex, unstructured notes."""
    text = """
    During today's meeting we discussed several important topics.
    John mentioned we need to update the documentation.
    Sarah suggested we should refactor the authentication module.
    Mike wants us to investigate the performance issues.
    """
    
    mock_response = {
        "output": json.dumps([
            "Update the documentation",
            "Refactor the authentication module",
            "Investigate the performance issues"
        ])
    }
    
    with patch('week2.app.services.extract._call_runpod_api', return_value=mock_response["output"]):
        items = extract_action_items_llm(text)
        assert len(items) == 3
        assert any("documentation" in item.lower() for item in items)
        assert any("authentication" in item.lower() for item in items)
        assert any("performance" in item.lower() for item in items)
