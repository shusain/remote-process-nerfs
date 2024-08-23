#! /home/shaun/anaconda3/bin/python
import paramiko
import os
from scp import SCPClient
import sys
import subprocess
import time

# Define your connection details
linux_directory = "/home/ubuntu/"
linux_host = "23.23.197.213"
linux_username = "ubuntu"
ssh_key_file = "/home/shaun/.ssh/System76Connection.pem"  # Path to your SSH private key file
output_directory = "/mnt/g/nerf_output"  # Path on Windows/WSL to save the output files

# Downsample video using FFmpeg
def downsample_video(input_path, output_path, scale_factor):
    ffmpeg_command = [
        'ffmpeg',
        '-i', input_path,
        '-vf', f'scale=iw*{scale_factor}:ih*{scale_factor}',
        output_path
    ]
    subprocess.run(ffmpeg_command, check=True)

# Transfer a single video file
def transfer_file(local_path, remote_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(linux_host, username=linux_username, key_filename=ssh_key_file)
    scp = SCPClient(ssh.get_transport())

    scp.put(local_path, remote_path)

    scp.close()
    ssh.close()

# Zip the outputs directory and transfer the zipped file
def zip_and_transfer_processed_directory():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(linux_host, username=linux_username, key_filename=ssh_key_file)

    # Zip the outputs directory
    zip_command = f'cd {linux_directory} && zip -r outputs.zip outputs'
    ssh.exec_command(zip_command)

    # Transfer the zipped file
    scp = SCPClient(ssh.get_transport())
    scp.get(os.path.join(linux_directory, 'outputs.zip'), os.path.join(output_directory, 'outputs.zip'))

    # Remove the outputs directory and the zipped file from the Linux machine
    cleanup_command = f'rm -rf {os.path.join(linux_directory, "processed")} {os.path.join(linux_directory, "outputs")} {os.path.join(linux_directory, "outputs.zip")}'
    ssh.exec_command(cleanup_command)

    scp.close()
    ssh.close()

# Execute commands on Linux machine
def run_nerf_studio(remote_video_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(linux_host, username=linux_username, key_filename=ssh_key_file)

    # Open an interactive shell session
    shell = ssh.invoke_shell()

    commands = f"""
        source /etc/profile
        source /home/ubuntu/miniconda3/etc/profile.d/conda.sh
        conda activate nerfstudio
        cd {linux_directory}
        ns-process-data video --data {remote_video_path} --output-dir processed
        ns-train nerfacto --data processed --viewer.quit-on-train-completion True
    """
    # If using splatfacto
    # ns-export gaussian-splat --load-config outputs\processed\splatfacto\2024-03-16_041824\config.yml --output-dir outputs/splat/

    # Send the command
    shell.send(f"bash -c '{commands}'\n")

    while True:
        # Read the output from the remote machine
        if shell.recv_ready():
            output = shell.recv(1024).decode()
            print(output, end='')

        # Check if the process is still running
        if shell.exit_status_ready():
            break

        time.sleep(1)
        
    print("Nerf Studio process completed.")

    # Zip and transfer the processed directory
    zip_and_transfer_processed_directory()

    # Shut down the server
    ssh.exec_command('sudo shutdown -h now')
    ssh.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_video_file> [--downsample]")
        sys.exit(1)

    video_file_path = sys.argv[1]
    downsample_flag = '--downsample' in sys.argv

    if not os.path.isfile(video_file_path):
        print(f"The file {video_file_path} does not exist.")
        sys.exit(1)

    if downsample_flag:
        # Define downsampled video path
        downsampled_video_path = "downsampled_video.mp4"
        
        # Downsample the video
        downsample_video(video_file_path, downsampled_video_path, scale_factor=0.5)
        
        # Transfer the downsampled video
        transfer_file(downsampled_video_path, os.path.join(linux_directory, "downsampled_video.mp4"))
        remote_video_path = os.path.join(linux_directory, "downsampled_video.mp4")
    else:
        # Transfer the original video
        transfer_file(video_file_path, os.path.join(linux_directory, os.path.basename(video_file_path)))
        remote_video_path = os.path.join(linux_directory, os.path.basename(video_file_path))

    run_nerf_studio(remote_video_path)