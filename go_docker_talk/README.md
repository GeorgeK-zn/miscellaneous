# Go Docker Container Implementation

This project provides a lightweight Docker-like container environment implemented in Go. It includes two main components:

1. A Go-based container runtime that creates isolated environments
2. A utility script to download and extract Docker images

## Overview

This implementation creates containers with namespace isolation using Go, demonstrating core container concepts including process isolation, filesystem management, and environment configuration.

## Getting Started

### Prerequisites

- Go runtime
- Root privileges (sudo)
- Bash shell
- Required utilities: curl, jq, go

### Downloading Container Images

Use the `download-frozen-image-v2.sh` script to download Docker images and extract their filesystems:

```bash
sudo ./download-frozen-image-v2.sh [destination_directory] [image:tag]
```

Example:
```bash
sudo ./download-frozen-image-v2.sh ./rootfs ubuntu:latest
```

### Running Containers

1. Edit the `container.go` file and update the rootfs path to point to your extracted filesystem
2. Run the container with:

```bash
sudo go run container.go /bin/bash
```

You can change the command arguments as needed.

## How It Works

The implementation uses Linux namespaces to provide isolation:
- `CLONE_NEWUTS`: Isolates hostname and domain
- `CLONE_NEWPID`: Creates a separate process ID namespace
- `CLONE_NEWNS`: Provides mount namespace isolation

The container mounts a procfs inside the isolated environment and performs a chroot to the specified filesystem.

## Requirements

This program must be run with root privileges (sudo) as it modifies system environment variables and requires access to namespace controls.

## Inspiration

This code is based on a demonstration seen in a YouTube talk about implementing container functionality in Go.

## License

This project is for educational and personal use.
