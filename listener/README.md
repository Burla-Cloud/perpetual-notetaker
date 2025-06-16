###  How to recreate the Rasberry Pi environment:

From Rasberry Pi OS Lite 64-bit, here is everything I did, in order:
1. <put GCP service account key in ~/service_account_key which gives GCS object create access>
2. <put slackbot token in ~/slackbot_api_token>
3. <put slack socket listener token in ~/slack_socket_listener_token>
4. run commands in order:
    1. `sudo apt update && sudo apt install -y ffmpeg`
    2. `sudo apt update`
    3. `sudo apt install python3-pip`
    4. `sudo /usr/bin/python -m pip install google-cloud-storage --break-system-packages`
    5. `sudo /usr/bin/python -m pip install google-auth --break-system-packages`
    6. `sudo /usr/bin/python -m pip install slack_bolt --break-system-packages`
5. Paste the `listener.service` file into `/etc/systemd/system/listener.service`