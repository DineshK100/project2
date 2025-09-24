# README FOR PI C

## Install Dependencies

Make sure you install the required dependencies:

```bash
pip install paho-mqtt
pip install python-dotenv
```

## Environment Configuration

Create a `.env` file in the same directory as your script with the necessary configuration variables:

```bash
MQTT_BROKER_HOST= # IP address of Broker
MQTT_BROKER_PORT=1883
```

## Running the Application

Once the dependencies are installed and environment is configured:

```bash
python new_pi_c.py
```