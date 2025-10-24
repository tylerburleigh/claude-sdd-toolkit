#!/bin/bash
# Fix imports in all operation files

for file in status.py journal.py verification.py lifecycle.py time_tracking.py validation.py; do
    echo "Fixing $file..."
    # Replace absolute imports with sdd_common imports
    sed -i 's/from state import /from sdd_common.state import /g' "$file"
    sed -i 's/from spec import /from sdd_common.spec import /g' "$file"
    sed -i 's/from progress import /from sdd_common.progress import /g' "$file"
    sed -i 's/from paths import /from sdd_common.paths import /g' "$file"
    sed -i 's/from printer import /from sdd_common.printer import /g' "$file"
done

echo "Done!"
