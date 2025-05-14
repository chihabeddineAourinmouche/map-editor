#!/bin/bash

if [ -n "$1" ]; then
	DIRECTORY="$1"
else
	DIRECTORY="$HOME/Documents"
fi

if [ -n "$2" ]; then
	TARGET="$2"
else
	TARGET="Windows.zip"
fi

sh pack.sh "$DIRECTORY" && (cd "$DIRECTORY" && tar -czf "Map-Editor-$TARGET" Map-Editor && rm -f Map\ Editor.exe && cp Map-Editor/Map\ Editor.exe Map\ Editor.exe && rm -R Map-Editor)
