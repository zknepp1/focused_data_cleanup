# RUN THIS CODE TO MAKE THE EXECUTABLE.


pip install -r requirements.txt

pyinstaller --onefile your_script.py

Distribute the file found in dist/your_script