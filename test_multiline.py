#!/usr/bin/env python3
"""Quick test to verify PlainUi multi-line cell handling."""

import sys
sys.path.insert(0, 'src')

from claude_skills.claude_skills.common.plain_ui import PlainUi

ui = PlainUi()
test_data = [
    {'ID': 'test-1', 'Progress': '████░░░░░░ 60%\n6/10 tasks', 'Status': 'Active'},
    {'ID': 'test-2', 'Progress': '███████░░░ 70%\n7/10 tasks', 'Status': 'Complete'}
]

print("Testing PlainUi.print_table() with multi-line cells:")
print("=" * 60)
ui.print_table(test_data, columns=['ID', 'Progress', 'Status'], title='Test Table')
print("=" * 60)
