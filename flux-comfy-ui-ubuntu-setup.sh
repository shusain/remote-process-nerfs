#!/bin/bash

# Install script for dependencies of comfy UI and flux model weights summary of setup from page here:

# https://stable-diffusion-art.com/flux-comfyui/

# Beyond the script below for setup you'll need to download the JSON files for the comfyUI nodes setup to drag/drop onto the UI once the server has the service running.
# https://stable-diffusion-art.com/wp-content/uploads/2024/08/flux1-dev-fp8.json
# https://stable-diffusion-art.com/wp-content/uploads/2024/08/flux1-schnell-fp8.json

# full workflow requires auth on hugging face and acceptance of terms for model weight download
# https://stable-diffusion-art.com/wp-content/uploads/2024/08/flux1-dev-regular.json

# Be sure to add/adjust the AWS security groups to allow traffic from your IP to the server instance if the UI doesn't seem to be accessible and an Elastic IP or other public IP is being used.

sudo apt update
sudo apt install build-essential git
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI/
ls -al
conda create -n comfy python=3.10
conda activate comfy
python --version
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
wget https://huggingface.co/Lykon/AbsoluteReality/resolve/main/AbsoluteReality_1.8.1_pruned.safetensors -O models/checkpoints/AbsoluteReality_1.8.1_pruned.safetensors
wget https://huggingface.co/Comfy-Org/flux1-schnell/resolve/main/flux1-schnell-fp8.safetensors -O models/unet/flux1-schnell-fp8.safetensors
wget https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors -O models/vae/ae.safetensors
wget https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors -O models/clip/t5xxl_fp16.safetensors
python main.py --listen

# The listen flag will allow remote connections binding to 0.0.0.0 instead of localhost.

# Random other commands used along the way
# htop
# watch -t nvidia-smi
# lspci -k
# sudo shutdown now
# history


# The next wget one won't work since need key, can go to hugging face download page use F12 in chrome to grab the curl request and copy it (right click the request row) then paste like below add --output flag
# wget https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors -O models/unet/flux1-dev.safetensors 
# Copy curl as bash from chrome and add:  --output models/unet/flux1-dev.safetensors