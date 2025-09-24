# README for Laptop 1

## MQTT Broker Setup

We are using Mosquitto as our MQTT broker. It runs as a daemon process that remains active and listens on port 1883.

## Managing the Broker

### Starting the Broker
If the broker is not running, start it with:
```bash
sudo systemctl start mosquitto
```

### Checking Broker Status
To verify that the broker is up and running:
```bash
sudo systemctl status mosquitto
```
This command will display the current status of the Mosquitto broker service.

### Testing the Broker
To monitor all messages on the broker:
```bash
mosquitto_sub -h localhost -t '#' -v
```
This command subscribes to all topics (`#` is a wildcard) and shows messages with their topic names (`-v` for verbose output).

## Additional Commands

### Stopping the Broker
```bash
sudo systemctl stop mosquitto
```

### Enabling Auto-start on Boot
```bash
sudo systemctl enable mosquitto
```

### Restarting the Broker
```bash
sudo systemctl restart mosquitto
```

## Notes
- Default port: 1883