#!/bin/bash

current_dir=$(pwd)
base_dir=$(basename "$current_dir")
if [ "$base_dir" == "XML-Parser" ]; then
  pipreqs . --force --ignore .venv
else
  echo "You should run script only from XML-Parser dir"
fi
