#!/bin/bash

read -p "Enter the string (e.g., '# my function extra'): " input_string

if [[ -z "$input_string" ]]; then
  echo "No input received. Exiting."
  exit 1
fi

if [[ ! "$input_string" =~ ^([^\ ]+)\ (.+)$ ]]; then
  echo "Invalid input format. Expected 'language-specific-comment arbitrary string' with at least one space."
  exit 1
fi

delimiter="${BASH_REMATCH[1]}"
anchor_id="${BASH_REMATCH[2]}"

echo "${delimiter} ANCHOR[id=${anchor_id// /-}]"
echo "${delimiter} LINK #${anchor_id}"