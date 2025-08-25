# URL to OneDrive Downloader - Setup Guide

## Prerequisites

1. **Python 3.6+** - Make sure Python is installed
2. **rclone** - Already installed by the script
3. **OneDrive Account** - You need access to OneDrive

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure rclone with OneDrive

Before using the script, you need to configure rclone to work with your OneDrive account:

```bash
rclone config
```

Follow these steps:
1. Choose `n` for new remote
2. Enter name: `onedrive` (or any name you prefer)
3. Choose Microsoft OneDrive (usually option 23)
4. Leave client_id and client_secret blank for personal OneDrive
5. Choose your region (usually 1 for Microsoft Cloud Global)
6. Choose `n` for advanced config
7. Choose `y` for auto config (this will open a web browser)
8. Login to your Microsoft account and authorize rclone
9. Choose the type of OneDrive (Personal, Business, etc.)
10. Confirm the configuration

### 3. Verify Configuration

Check if OneDrive is properly configured:

```bash
python url_to_onedrive.py --check-config
```

## Usage Examples

### Download Single URL

```bash
# Basic usage
python url_to_onedrive.py --url "https://example.com/file.pdf"

# With custom filename
python url_to_onedrive.py --url "https://example.com/file.pdf" --filename "my_document.pdf"

# Upload to specific OneDrive folder
python url_to_onedrive.py --url "https://example.com/file.pdf" --path "/Documents/Downloads"
```

### Download Multiple URLs from File

```bash
# Create a file with URLs (one per line)
echo "https://example.com/file1.pdf" > urls.txt
echo "https://example.com/file2.jpg" >> urls.txt

# Download all URLs
python url_to_onedrive.py --file urls.txt
```

### Interactive Mode

```bash
# Run without arguments for interactive mode
python url_to_onedrive.py
```

### Advanced Options

```bash
# Use different rclone remote name
python url_to_onedrive.py --url "https://example.com/file.pdf" --remote "myonedrive:"

# Upload to specific path
python url_to_onedrive.py --url "https://example.com/file.pdf" --path "/Work/Projects"
```

## Command Line Options

- `--url, -u`: Single URL to download
- `--file, -f`: File containing URLs (one per line)
- `--filename, -n`: Custom filename for single URL download
- `--remote, -r`: rclone remote name (default: onedrive:)
- `--path, -p`: OneDrive path (default: /Downloads)
- `--check-config, -c`: Check rclone OneDrive configuration

## Features

- ✅ Download files from any URL
- ✅ Upload to OneDrive using rclone
- ✅ Progress tracking for downloads
- ✅ Batch processing from file
- ✅ Interactive mode
- ✅ Comprehensive error handling
- ✅ Logging to file and console
- ✅ Automatic filename detection
- ✅ Custom OneDrive paths
- ✅ Temporary file cleanup

## Troubleshooting

### Error: "rclone not found"
Make sure rclone is installed and in your PATH. The script should have installed it automatically.

### Error: "OneDrive remote not configured"
Run `rclone config` to set up your OneDrive connection.

### Permission Errors
Make sure you have write permissions to the temp directory and that your OneDrive has sufficient storage.

### Network Issues
The script includes timeout handling, but very large files or slow connections may require adjusting the timeout values in the code.

## Log Files

The script creates a log file `url_to_onedrive.log` with detailed information about all operations.