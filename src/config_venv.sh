#!/bin/bash

# If you want the en    vironment activation to persist in your current terminal, use source to run the script
# source config_venv.sh
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo -e "\e[32mVirtual environment is active. Deactivating...\e[0m"
    deactivate
    echo -e "\e[32mVirtual environment deactivated.\e[0m"
else
    echo -e "\e[32mNo virtual environment is currently active.\e[0m"
fi

echo -e "\e[32mCreating virtual environment...\e[0m"
python3 -m venv venv || { echo -e "\e[31mFailed to create virtual environment\e[0m";}

echo -e "\e[32mActivating virtual environment...\e[0m"
source venv/bin/activate || { echo -e "\e[31mFailed to activate virtual environment\e[0m";}

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "\e[31mError: Virtual environment is not active. Aborting installation\e[0m"
else


    echo -e "\e[32mInstalling requirements...\e[0m"
    pip install -r requirements.txt || { echo -e "\e[31mFailed to install requirements\e[0m";}

    echo -e "\e[32mInstalling Jupyter kernel...\e[0m"
    python3 -m ipykernel install --user --name=my_venv || { echo -e "\e[31mFailed to install Jupyter kernel\e[0m";}

    echo -e "\e[32mSetup completed.\e[0m"
fi