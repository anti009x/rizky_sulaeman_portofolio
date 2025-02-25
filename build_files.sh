#!/bin/bash
echo "BUILD START"
python -m pip install -r requirements.txt
npx tailwindcss -i ./static/src/input.css -o ./static/src/output.css --watch
echo "BUILD END"
