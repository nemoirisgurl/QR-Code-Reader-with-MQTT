# QR Code Reader wiith MQTT server
This project tends to be a prototype of QR Code Reader module for Software Development Practice I
## Contents
1. [Installation](#installation)
2. [Running](#running)
3. [Footage](#footage)

## Installation
Follow these steps to set up the project environment.

### Prerequisites
* Python 3.8+ and `pip`
* Git
* An MQTT Broker (e.g., [Mosquitto](https://mosquitto.org/download/)). Make sure the broker is installed and running.

### Steps
1. Clone this repository.
```bash
git clone https://github.com/nemoirisgurl/QR-Code-Reader-with-MQTT.git
cd QR-Code-Reader-with-MQTT
```
2. Install and activate python virtual environment.
   * **Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
   * **MacOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
sudo apt install libzbar0
sudo apt install libzbar-dev
sudo usermod -a -G dialout $USER
```

3.  Install the required Python packages:
```bash
pip install -r requirements.txt
```

4. Run MQTT Broker:
```bash
mosquitto_sub -h <YOUR_BROKER> -p <PORT> -t <YOUR_TOPIC> -v
```

## Running
Use this command
```bash
python read_qrcode_module/read_qrcode_bcode.py
```
or
```bash
python read_qrcode_module/read_qrcode_webcam.py
```
Make sure you run the command on the **QR-Code-Reader-with-MQTT** folder and different terminal from MQTT Broker
## Footage

<img src="src/cv2screen.png" alt="OpenCV QR Code Scanner" width="600" height="400"/>  

OpenCV QR Code Scanner 

<img src="src/publisher.png" alt="Client result (Publish to broker)" width="600" height="200"/>

Client result (Publish to broker)

<img src="src/subscriber.png" alt="Server result (Subscribe from client)" width="600" height="200"/>

Server result (Subscribe from client)

<img src="src/json_output.png" alt="JSON File data" width="600" height="400"/>

JSON File data
