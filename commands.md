sudo apt update

sudo apt install -y mosquitto mosquitto-clients

sudo systemctl enable mosquitto

sudo mkdir -p /etc/mosquitto/conf.d

printf "listener 1883\nallow_anonymous true\n" | sudo tee /etc/mosquitto/conf.d/lab2.conf

sudo systemctl restart mosquitto

sudo systemctl status mosquitto --no-pager
