#!/bin/bash

# Проверяем, активирована ли виртуальная среда
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Virtual environment is active. Deactivating..."
    deactivate
    echo "Virtual environment deactivated."
else
    echo "No virtual environment is currently active."
fi

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Installing Jupyter kernel..."
python3 -m ipykernel install --user --name=my_venv

echo "Now reboot VS Code for changes to take effect."
