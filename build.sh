#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt
python -c "import money_printer_turbo; print('Money Printer Turbo version:', money_printer_turbo.__version__)" || echo "Money Printer Turbo import failed"
