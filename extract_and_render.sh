#!/usr/bin/env nix
#! nix shell nixpkgs#perl nixpkgs#mermaid-cli --command bash

set -euo pipefail

OUTPUT_BASENAME="mmdc_output" # Default output base name

# Parse command line options
while getopts "o:" opt; do
  case $opt in
    o)
      # Remove .png extension if provided, we'll add it back with COUNT
      OUTPUT_BASENAME=$(basename "$OPTARG" .png)
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done
shift $((OPTIND-1))

# Read from argument file or default to stdin
INPUT_SRC="${1:-/dev/stdin}"

COUNT=1
INSIDE_BLOCK=0
CURRENT_BLOCK=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$SCRIPT_DIR/config.json"

mmdc --version >&2

while IFS= read -r line; do
  # Match markdown fence block opening
  if [[ "$line" =~ ^[[:space:]]*\`\`\`mermaid ]]; then
    INSIDE_BLOCK=1
    CURRENT_BLOCK=""
    continue
  fi

  # Match markdown fence block closing
  if [[ "$line" =~ ^[[:space:]]*\`\`\` ]] && [ $INSIDE_BLOCK -eq 1 ]; then
    INSIDE_BLOCK=0
    
    echo "Processing diagram #$COUNT..." >&2
    
    export CURRENT_BLOCK
    TMPFILE=$(mktemp /tmp/mermaid_block_XXXXXX.mmd)
    printf "%s" "$CURRENT_BLOCK" > "$TMPFILE"

    CLEANED_BLOCK=$(perl -0777 -e '
        local $/;
        my $code = do { open(my $fh, "<", $ARGV[0]) or die $!; <$fh> };
        $code =~ s/(\b\w+\s+\w+(?:\s+(?:PK|FK|UK))?)\s+"[^"]*"/$1/gs;
        print $code;
    ' "$TMPFILE")

    rm -f "$TMPFILE"

    # Optional debugging print
    printf "%s" "$CLEANED_BLOCK"

    # 1. Commented out beautiful-mermaid-cli
    # printf "%s" "$CLEANED_BLOCK"
    # TMPFILE2=$(mktemp /tmp/mermaid_clean_XXXXXX.mmd)
    # printf "%s" "$CLEANED_BLOCK" > "$TMPFILE2"
    # echo "--- beautiful-mermaid-cli output ---" >&2
    # npx --yes beautiful-mermaid-cli render "$TMPFILE2" -o "output_${COUNT}.svg" 2>&1
    # echo "--- TMPFILE2 contents ---" >&2
    # cat "$TMPFILE2" >&2
    # rm -f "$TMPFILE2"
    
    # 2. FIXED: Pipe directly into mmdc via standard input descriptor (-)
    printf "%s" "$CLEANED_BLOCK" | mmdc -i - -o "${OUTPUT_BASENAME}_${COUNT}.png" -t dark -c "$CONFIG" -b "#1a1b26"
    # printf "%s" "$CLEANED_BLOCK" | mmdc -i - -o "mmdc_output_${COUNT}.svg"
    # Doesn't work for multiline 
    # printf "%s" "$CURRENT_BLOCK" | \
    #     sed -E 's/([A-Za-z0-9_]+ +[A-Za-z0-9_]+( +(PK|FK|UK))?) +"[^"]*"/\1/' | \
    #     mmdc -i - -o "mmdc_output_${COUNT}.svg"

    
    COUNT=$((COUNT + 1))
    continue
  fi

  # Capture block contents
  if [ $INSIDE_BLOCK -eq 1 ]; then
    CURRENT_BLOCK+="$line"$'\n'
  fi
done < "$INPUT_SRC"
