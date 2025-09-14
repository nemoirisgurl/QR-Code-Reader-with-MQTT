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
sudo apt install mosquitto-clients 
python3 -m venv venv
source venv/bin/activate
```

3.  Install the required Python packages:
```bash
pip install -r requirements.txt
```

4. Run MQTT Broker:
```bash
mosquitto_sub -h localhost -p 1883 -t "openhouse/checkin-checkout" -v
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

<img src="src/cv2screen.png" alt="OpenCV QR Code Scanner" width="300" height="400"/>
<img src="src/publisher.png" alt="Client result (Publish to broker)" width="300" height="400"/>
<img src="src/subscriber.png" alt="Server result (Subscribe from client)" width="300" height="400"/>
