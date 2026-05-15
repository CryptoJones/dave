#!/bin/bash
# Dave Execution Script - RUN THESE COMMANDS IN ORDER
# YOU execute every step on YOUR machine - no data leaves your control

set -euo pipefail

# --- Configurable paths ---
# Override these before running:
#   export DAVE_DATA_DIR=/path/to/data
#   export DAVE_OUTPUT_DIR=/path/to/adapters/dave
#   export DAVE_BOOKS_DIR=/path/to/your/licensed/books

DAVE_DATA_DIR="${DAVE_DATA_DIR:-$(pwd)/data}"
DAVE_OUTPUT_DIR="${DAVE_OUTPUT_DIR:-/home/akclark/Source/adapters/dave}"
DAVE_BOOKS_DIR="${DAVE_BOOKS_DIR:-/path/to/your/books}"

echo "=== Dave Training Execution Guide ==="
echo ""
echo "Current paths (override with environment variables):"
echo "  DAVE_DATA_DIR=$DAVE_DATA_DIR"
echo "  DAVE_OUTPUT_DIR=$DAVE_OUTPUT_DIR"
echo "  DAVE_BOOKS_DIR=$DAVE_BOOKS_DIR"
echo ""
echo "Example overrides:"
echo "  export DAVE_DATA_DIR=~/Source/repos/Dave/data"
echo "  export DAVE_OUTPUT_DIR=~/Source/adapters/dave"
echo "  export DAVE_BOOKS_DIR=~/books/security"
echo ""

echo "STEP 1: Prepare Environment (Run ONCE)"
echo "-----------------------------------------------------------------------"
echo "cd $(pwd)"
echo "chmod +x setup_dave.sh RUN_DAVE.sh"
echo "./setup_dave.sh"
echo ""

echo "STEP 2: Process Your Licensed Books (RUN ONCE)"
echo "-----------------------------------------------------------------------"
echo "python3 scripts/data_collection/process_books_nda_fixed.py \$DAVE_BOOKS_DIR"
echo ""
echo "Output: \$DAVE_DATA_DIR/processed/books/books_training.jsonl"
echo ""

echo "STEP 3: Process Free Resources (YOU DO THIS MANUALLY)"
echo "-----------------------------------------------------------------------"
echo "# Download these legally free resources from official sources:"
echo "# - CISA KEV Catalog (https://www.cisa.gov/known-exploited-vulnerabilities-catalog)"
echo "# - NIST SP 800-30 Rev. 1 (https://csrc.nist.gov/publications/detail/sp/800-30/rev-1/final)"
echo "# - NIST SP 800-53 Rev. 5 (https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)"
echo "# - DHS Binding Operational Directives (https://www.cisa.gov/binding-operational-directives)"
echo "# - US-CERT Alerts (https://www.us-cert.gov/ncas/alerts)"
echo "# - NISTIR 8286 (https://csrc.nist.gov/publications/detail/nistir/8286/final)"
echo "# - MITRE ATT&CK® (DEFENSIVE CONTEXT ONLY) - https://attack.mitre.org/"
echo ""
echo "# Save each processed file to:"
echo "# \$DAVE_DATA_DIR/processed/free_sources/[name]_training.jsonl"
echo ""
echo "# Example: CISA KEV (after downloading kev.json):"
echo "python3 -c \""
echo "import json"
echo "with open('kev.json') as f:"
echo "    data = json.load(f)"
echo "for vuln in data['vulnerabilities']:"
echo "    if 'requiredAction' in vuln and vuln['requiredAction']:"
echo "        prompt = f'Technical finding: [{vuln[\\\"cveID\\\"]} in {vuln[\\\"vendorProject\\\"]}]'"
echo "        completion = f'Per CISA KEV, {vuln[\\\"requiredAction\\\"]} is required by {vuln[\\\"dueDate\\\"]}. Executive summary: [APA/(ISC)²-aligned summary based on {vuln[\\\"shortDescription\\\"]}].'"
echo "        print(json.dumps({'prompt': prompt, 'completion': completion}))"
echo "\" >> \"\$DAVE_DATA_DIR/processed/free_sources/kev_training.jsonl\""
echo ""

echo "STEP 4: Combine and Shuffle All Data (RUN ONCE)"
echo "-----------------------------------------------------------------------"
echo "cat \"\$DAVE_DATA_DIR/processed/books/books_training.jsonl\" \\"
echo "    \"\$DAVE_DATA_DIR/processed/free_sources/\"*_training.jsonl \\"
echo "    > \"\$DAVE_DATA_DIR/combined_training.jsonl\""
echo ""
echo "shuf \"\$DAVE_DATA_DIR/combined_training.jsonl\" > \"\$DAVE_DATA_DIR/shuffled_training.jsonl\""
echo ""
echo "wc -l \"\$DAVE_DATA_DIR/shuffled_training.jsonl\""
echo ""

echo "STEP 5: Train Dave (RUN ONCE - requires A100 80GB on RunPod)"
echo "-----------------------------------------------------------------------"
echo "DAVE_DATA_DIR=\$DAVE_DATA_DIR DAVE_OUTPUT_DIR=\$DAVE_OUTPUT_DIR python3 train_dave.py"
echo ""

echo "STEP 6: Verify Training Complete"
echo "-----------------------------------------------------------------------"
echo "ls -la \"\$DAVE_OUTPUT_DIR\""
echo "# You should see: adapter_model.bin and adapter_config.json"
echo ""

echo "=== IMPORTANT REMINDERS ==="
echo "-----------------------------------------------------------------------"
echo "• Dave is ONLY for authorized US security assessment report writing"
echo "• NEVER use it without explicit written permission for specific targets"
echo "• ALWAYS review outputs — Dave is an assistant, not a replacement for expertise"
echo "• Your NDA remains intact — book details never left your machine"
echo "• Adapter in \$DAVE_OUTPUT_DIR contains ONLY your licensed knowledge + free resources"
echo "• Base model (meta-llama/Llama-3.3-70B-Instruct) remains unchanged"
echo ""
echo "=== You're Ready to Begin ==="
echo "Start with STEP 1 above."
