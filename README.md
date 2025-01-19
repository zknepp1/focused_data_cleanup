# RUN THIS CODE TO MAKE THE EXECUTABLE.

python.exe -m pip install --upgrade pip

pip install -r requirements.txt

pyinstaller --onefile main.py

Distribute the file found in dist/main