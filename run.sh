#!/bin/bash
cd
cd /root/dev/quizgbm
source venv/bin/activate
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
python main.py > "logs/output_$timestamp.log" 2>&1
