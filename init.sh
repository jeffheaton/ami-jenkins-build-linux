#!/bin/bash

# Update and upgrade the system
sudo dnf update -y
sudo dnf upgrade -y

# Install Amazon Corretto JDK
if ! rpm -q amazon-corretto-17; then
    wget -q https://corretto.aws/downloads/latest/amazon-corretto-17-x64-linux-jdk.rpm -O amazon-corretto-17.rpm
    sudo rpm -ivh amazon-corretto-17.rpm
    rm -f amazon-corretto-17.rpm
fi

# Install Git
sudo dnf install -y git

# Install Python 3 and pipx
sudo dnf install -y python3 python3-pip
python3 -m pip install --upgrade --user pip pipx
python3 -m pipx ensurepath

# Install Docker
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

# Ensure Docker group is activated for ec2-user
sudo -u ec2-user newgrp docker <<EOF
# This section ensures Docker is fully usable for ec2-user
echo "Docker group refreshed for ec2-user."
EOF

# Install Poetry for ec2-user
POETRY_HOME="/home/ec2-user/.poetry"
if [ ! -d "$POETRY_HOME" ]; then
    sudo mkdir -p "$POETRY_HOME"
    sudo chown ec2-user:ec2-user "$POETRY_HOME"
    sudo -u ec2-user python3 -m venv "$POETRY_HOME"
    sudo -u ec2-user $POETRY_HOME/bin/pip install poetry
    sudo -u ec2-user $POETRY_HOME/bin/poetry --version
fi

# Add Poetry to ec2-user's PATH if not already present
if ! grep -q "export PATH=\$PATH:$POETRY_HOME/bin" /home/ec2-user/.bashrc; then
    echo "export PATH=\$PATH:$POETRY_HOME/bin" | sudo tee -a /home/ec2-user/.bashrc
    echo "export PATH=\$PATH:$POETRY_HOME/bin" | sudo tee -a /home/ec2-user/.bash_profile
    sudo chown ec2-user:ec2-user /home/ec2-user/.bashrc /home/ec2-user/.bash_profile
fi

echo "Initialization script complete. Please reboot if necessary."

