import paramiko
import os

HOST = '82.24.195.23'
USER = 'root'
PASSWORD = 'NaHaL_901'
PORT = 22

FILES_TO_DEPLOY = [
    "bot_plans.py",
    "database.py",
    "routes.py"
]

REMOTE_DIR = "/opt/library_of_prompts"

def deploy():
    print("Connecting to SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD)

    print("Creating backups on server...")
    for f in FILES_TO_DEPLOY:
        stdin, stdout, stderr = ssh.exec_command(f"cp {REMOTE_DIR}/{f} {REMOTE_DIR}/{f}.bak_game_limits")
        stdout.channel.recv_exit_status()

    print("Uploading files...")
    sftp = ssh.open_sftp()
    for f in FILES_TO_DEPLOY:
        local_path = os.path.join(os.getcwd(), f)
        remote_path = f"{REMOTE_DIR}/{f}"
        print(f"  Uploading {f}...")
        sftp.put(local_path, remote_path)
    sftp.close()

    print("Restarting service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart library-prompts-bot.service")
    stdout.channel.recv_exit_status()

    print("Checking service status...")
    stdin, stdout, stderr = ssh.exec_command("systemctl status library-prompts-bot.service | head -n 10")
    print(stdout.read().decode())

    ssh.close()
    print("Deployment complete.")

if __name__ == "__main__":
    deploy()
