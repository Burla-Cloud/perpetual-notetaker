import os
import sys
import signal
import subprocess
import threading
import traceback
from pathlib import Path
from time import sleep

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from google.cloud import storage
from google.oauth2 import service_account


bucket_name = "perpetual-notetaker-raw-audio"
svc_account_key_path = "/home/jakezuliani/service_account_key.json"
slackbot_api_token_path = "/home/jakezuliani/slackbot_api_token"
slack_socket_token_path = "/home/jakezuliani/slack_socket_listener_token"
device = "plughw:0,0"
record_seconds = 60
temp_dir = "/tmp/audio_uploads"
Path(temp_dir).mkdir(exist_ok=True)

slackbot_api_token = Path(slackbot_api_token_path).read_text().strip()
slack_socket_token = Path(slack_socket_token_path).read_text().strip()
slack_bolt_app = App(token=slackbot_api_token)


class VerboseCalledProcessError(Exception):
    pass


def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True)
    if result.returncode != 0:
        raise VerboseCalledProcessError(command, result.stderr)
    else:
        return result


def is_file_stable(file_path, stable_seconds=2):
    if not file_path.exists():
        return False
    last_modified = file_path.stat().st_mtime
    sleep(stable_seconds)
    current_modified = file_path.stat().st_mtime
    return last_modified == current_modified


def signal_handler(signum, frame):
    try:
        tell_slack(f"Process exiting ... Signal {signum} recieved.")
    except:
        pass
    sys.exit(0)


@slack_bolt_app.event("app_mention")
def handle_mention(event, say):
    temperature = run_command("vcgencmd measure_temp").stdout.decode().strip()
    temperature = temperature.replace("temp=", "")
    msg = f"Hi, everything seems to be working, and I'm running at {temperature}\n"
    msg += f"Valid commands are:\n"
    msg += f"  - `/listener status`\n"
    say(msg)


@slack_bolt_app.command("/listener")
def handle_listener_command(ack, respond, command):
    ack(response_type="in_channel")
    text = command["text"].strip().lower()

    if text == "status":
        temperature = run_command("vcgencmd measure_temp").stdout.decode().strip()
        temperature = temperature.replace("temp=", "")
        tell_slack(f"Hi, I'm currently listening!\nMy CPU temp is {temperature}")
    else:
        msg = "I don't understand.\n"
        msg += "Valid commands are:\n"
        msg += "  - `/listener status`\n"
        tell_slack(msg)


def tell_slack(message):
    slack_bolt_app.client.chat_postMessage(channel="#meeting-notes", text=message)


def recorder(attempt=0):
    # This script starts becure the mic is available causing errors,
    # retry until it should be available
    try:
        cmd = f"ffmpeg -f alsa -i {device} -segment_time 60 -f segment -reset_timestamps 1 "
        cmd += f'-strftime 1 "{temp_dir}/audio_%Y%m%d_%H%M%S.wav"'
        run_command(cmd)
    except Exception:
        if attempt < 5:
            sleep(1)
            recorder(attempt + 1)
        else:
            recorder.exc_info = sys.exc_info()


def main():
    tell_slack("Listener is booting ...")

    start_bolt_app = lambda: SocketModeHandler(slack_bolt_app, slack_socket_token).start()
    bolt_app_thread = threading.Thread(target=start_bolt_app, daemon=True)
    bolt_app_thread.start()
    sleep(2)

    credentials = service_account.Credentials.from_service_account_file(svc_account_key_path)
    bucket = storage.Client(credentials=credentials).bucket(bucket_name)
    recorder_thread = threading.Thread(target=recorder, daemon=True)
    recorder_thread.start()

    tell_slack("Done booting!  🔴 Audio recording started.")

    while True:
        sleep(1)

        if not recorder_thread.is_alive():
            if hasattr(recorder, "exc_info"):
                raise recorder.exc_info[1].with_traceback(recorder.exc_info[2])
            else:
                raise Exception("Recording thread died unexpectedly and with no exception!")

        ready_files = [f for f in Path(temp_dir).iterdir() if is_file_stable(f)]
        if not ready_files:
            continue
        if len(ready_files) > 1:
            raise RuntimeError(f"Expected 1 ready file in {temp_dir}, but found {len(ready_files)}")

        wav_path = ready_files[0]
        opus_path = wav_path.with_suffix(".opus")

        # compress wav to opus & upload
        run_command(f"ffmpeg -y -i {wav_path} -c:a libopus -b:a 32k {opus_path}")
        bucket.blob(f"audio/{opus_path.name}").upload_from_filename(opus_path)
        os.remove(wav_path)
        os.remove(opus_path)


if __name__ == "__main__":
    try:
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, signal_handler)
        main()
    except Exception as e:
        formatted_traceback = "".join(traceback.format_exception(*sys.exc_info()))
        tell_slack(f"Listener crashed!\n```{formatted_traceback}```")
        raise
