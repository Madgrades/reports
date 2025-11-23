FROM python:3.11

# Install sudo first
RUN apt-get update && apt-get install -y sudo && rm -rf /var/lib/apt/lists/*

# Create vscode user
RUN groupadd --gid 1000 vscode \
  && useradd --uid 1000 --gid 1000 -m -s /bin/bash vscode \
  && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Copy and run system dependencies install script
COPY scripts/install-system-deps.sh /tmp/
RUN bash /tmp/install-system-deps.sh && rm /tmp/install-system-deps.sh
