
import pytest
import json
from claude_skills.common.contracts import extract_session_summary_contract
from claude_skills.common.json_output import format_compact_output

def test_extract_session_summary_contract():
    """Test that session-summary contract extracts only essential fields."""
    
    # Full output simulation
    full_output = {
        "project_root": "/abs/path/to/project",
        "permissions": {
            "configured": True,
            "status": "fully_configured",
            "settings_file": "/path/to/settings.json",
            "exists": True,
            "has_specs": True
        },
        "git": {
            "configured": True,
            "git_config_file": "/path/to/git_config.json",
            "exists": True,
            "enabled": True,
            "needs_setup": False,
            "settings": {
                "auto_branch": True,
                "auto_commit": True
            }
        },
        "active_work": {
            "active_work_found": True,
            "specs": [
                {
                    "spec_id": "spec-1",
                    "title": "Test Spec",
                    "completed": 5,
                    "total": 10,
                    "percentage": 50
                }
            ],
            "pending_specs": [
                {"spec_id": "pending-1", "title": "Pending Spec"}
            ],
            "message": None,
            "count": 1,
            "text": "📋 Active Work Summary\n..."
        },
        "session_state": {
            "last_task": {
                "spec_id": "spec-1",
                "task_id": "task-1-1"
            },
            "in_progress_count": 1,
            "timestamp": "2025-11-18T10:00:00Z"
        }
    }

    # Extract contract
    contract = extract_session_summary_contract(full_output)

    # Verify Essential Fields
    assert "permissions" in contract
    assert contract["permissions"]["status"] == "fully_configured"
    assert "configured" not in contract["permissions"] # Redundant
    
    assert "git" in contract
    assert contract["git"]["needs_setup"] is False
    assert "settings" in contract["git"]
    assert "git_config_file" not in contract["git"] # Redundant

    assert "active_work" in contract
    assert contract["active_work"]["found"] is True
    assert contract["active_work"]["text"] == "📋 Active Work Summary\n..."
    assert "pending_specs" in contract["active_work"]
    assert len(contract["active_work"]["pending_specs"]) == 1
    assert "specs" not in contract["active_work"] # Redundant

    assert "session_state" in contract
    assert contract["session_state"]["last_task"]["task_id"] == "task-1-1"
    assert "in_progress_count" not in contract["session_state"] # Redundant

def test_compact_format_integration():
    """Verify format_compact_output handles session-summary type."""
    data = {
        "permissions": {"status": "not_configured"},
        "git": {"needs_setup": True},
        "active_work": {"active_work_found": False, "text": "None"},
        "extra_field": "should_be_removed"
    }
    
    output_str = format_compact_output(data, 'session-summary')
    output = json.loads(output_str)
    
    assert output["permissions"]["status"] == "not_configured"
    assert output["git"]["needs_setup"] is True
    assert "extra_field" not in output
