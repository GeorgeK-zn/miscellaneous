#!/bin/bash

# Usage function to display help
usage() {
    echo "Usage: $0 -o <organization> -a <author> -f <output_file>"
    exit 1
}

# Parse command line arguments
while getopts "o:a:f:" opt; do
    case $opt in
        o) ORG="$OPTARG" ;;
        a) AUTHOR="$OPTARG" ;;
        f) OUTPUT_FILE="$OPTARG" ;;
        *) usage ;;
    esac
done

# Check if all arguments are provided
if [ -z "$ORG" ] || [ -z "$AUTHOR" ] || [ -z "$OUTPUT_FILE" ]; then
    usage
fi

# Initialize the file
echo "Merged PRs by $AUTHOR in org '$ORG'" > "$OUTPUT_FILE"
echo "Generated on: $(date)" >> "$OUTPUT_FILE"
echo "==========================================" >> "$OUTPUT_FILE"

gh repo list $ORG --limit 1000 --json name -q '.[].name' | while read repo; do
    echo "Checking $repo..."

    # Fetch merged PRs for the repo
    PRS=$(gh pr list -R "$ORG/$repo" --state merged --author "$AUTHOR" --limit 100 --json number,title,mergedAt)

    # Check if result is not empty
    if [ "$(echo "$PRS" | jq length)" -gt 0 ]; then
        echo -e "\n🔍 $repo" >> "$OUTPUT_FILE"
        echo "$PRS" | jq -r '.[] | "  • #\(.number): \(.title) [\(.mergedAt)]"' >> "$OUTPUT_FILE"
    fi
done

echo "✅ Done! Output saved to $OUTPUT_FILE"
