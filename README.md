# 💻 Laptop Diagnoser
Laptop Diagnoser is an **advanced Windows system monitoring and diagnostic tool** built with **Python**. It helps users — from beginners to developers — understand their laptop’s health, identify issues, and perform safe fixes with a simple GUI.

## 🚀 Features

- 🖥 **System Health Overview**: CPU, RAM, Disk usage, and battery status  
- ⚡ **Top Processes**: Lists the highest resource-consuming processes  
- 🌐 **Network Diagnostics**: Ping and DNS checks  
- 📝 **Event Logs**: Shows recent Windows System & Application warnings/errors  
- 🧹 **Temp File Cleanup**: One-click deletion of temporary files  
- 🛠 **Repair Suggestions**: Commands like `sfc /scannow`, `chkdsk`, and DISM  
- 📊 **Detailed Reports**: Export diagnostics as **TXT** or **JSON**  
- 🔒 **Security & Startup Check**: Firewall, Antivirus status, and startup apps  
- ⏱ **Real-time Monitoring**: CPU, memory, disk, and network usage updates every 2 seconds

## 🛠 Built With
- Python 🐍  
- [PySimpleGUI](https://pypi.org/project/PySimpleGUI/) 🖼  
- [psutil](https://pypi.org/project/psutil/) ⚡  
- Windows Event Log (`pywin32`) 📝  

## 💾 Installation

1. Clone the repository:  
<pre>
git clone https://github.com/yourusername/laptop-diagnoser.git
cd laptop-diagnoser
</pre>
cd laptop-diagnoser
2. Install dependencies:
<pre>pip install --upgrade --force-reinstall PySimpleGUI psutil pywin32</pre>
3. Run the application:
<pre>python laptop_diagnoser.py</pre>
⚠️ Windows only. Some features (Event Log, Firewall/Antivirus check) require Windows.

## 📸 Screenshots 
<img width="860" height="587" alt="image" src="https://github.com/user-attachments/assets/a054c4e2-395b-4182-af13-d27c97271094" />
<img width="858" height="592" alt="image" src="https://github.com/user-attachments/assets/6b81c47f-c274-45b7-b6ce-19542cfca81d" />

## 🔮 Future Improvements
- 🤖 AI-powered suggestions for unusual processes
- 💻 Cross-platform support (Linux & macOS)
- 📦 Packaged installer for easy use without Python

## 📄 License
This project is licensed under the MIT License.

## 💬 Connect
Created by Akanksha Mane – a developer & student passionate about making technology accessible.
