#!/usr/bin/env python3
"""
URL to OneDrive Downloader using rclone

This script downloads files from URLs and uploads them to OneDrive using rclone.
Before using this script, make sure to configure rclone with your OneDrive account:
    rclone config

Usage:
    python url_to_onedrive.py
"""

import os
import sys
import subprocess
import tempfile
import requests
import argparse
import logging
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, List
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('url_to_onedrive.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class URLToOneDriveDownloader:
    """Class to handle downloading URLs and uploading to OneDrive via rclone"""
    
    def __init__(self, onedrive_remote: str = "onedrive:", onedrive_path: str = "/Downloads"):
        """
        Initialize the downloader
        
        Args:
            onedrive_remote: The rclone remote name for OneDrive (default: "onedrive:")
            onedrive_path: The path in OneDrive where files will be uploaded (default: "/Downloads")
        """
        self.onedrive_remote = onedrive_remote
        self.onedrive_path = onedrive_path
        self.temp_dir = tempfile.mkdtemp(prefix="url_downloader_")
        logger.info(f"Created temporary directory: {self.temp_dir}")
        
        # Check if rclone is available
        if not self._check_rclone():
            raise RuntimeError("rclone not found. Please install rclone and configure it with OneDrive.")
    
    def _check_rclone(self) -> bool:
        """Check if rclone is available and configured"""
        try:
            result = subprocess.run(['rclone', 'version'], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"rclone version: {result.stdout.split()[1]}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_onedrive_config(self) -> bool:
        """Check if OneDrive is configured in rclone"""
        try:
            result = subprocess.run(['rclone', 'listremotes'], 
                                  capture_output=True, text=True, check=True)
            remotes = result.stdout.strip().split('\n')
            onedrive_configured = any(self.onedrive_remote.rstrip(':') + ':' in remote for remote in remotes)
            
            if onedrive_configured:
                logger.info(f"OneDrive remote '{self.onedrive_remote}' is configured")
                return True
            else:
                logger.warning(f"OneDrive remote '{self.onedrive_remote}' not found in configured remotes")
                logger.info(f"Available remotes: {', '.join(remotes)}")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check rclone remotes: {e}")
            return False
    
    def _get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL or generate one"""
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        if not filename or '.' not in filename:
            # Generate filename from URL components
            domain = parsed_url.netloc.replace('.', '_')
            filename = f"download_{domain}_{hash(url) % 10000}.bin"
        
        return filename
    
    def _download_file(self, url: str, filename: str) -> str:
        """
        Download file from URL to temporary directory
        
        Args:
            url: The URL to download
            filename: The filename to save as
            
        Returns:
            Path to the downloaded file
        """
        file_path = os.path.join(self.temp_dir, filename)
        
        logger.info(f"Downloading {url} to {file_path}")
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"\rDownload progress: {progress:.1f}%", end='', flush=True)
            
            print()  # New line after progress
            logger.info(f"Successfully downloaded {filename} ({downloaded_size} bytes)")
            return file_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            raise
    
    def _upload_to_onedrive(self, local_file_path: str, remote_filename: str) -> bool:
        """
        Upload file to OneDrive using rclone
        
        Args:
            local_file_path: Path to the local file
            remote_filename: Filename to use in OneDrive
            
        Returns:
            True if upload successful, False otherwise
        """
        remote_path = f"{self.onedrive_remote}{self.onedrive_path}/{remote_filename}"
        
        logger.info(f"Uploading {local_file_path} to {remote_path}")
        
        try:
            cmd = ['rclone', 'copy', local_file_path, f"{self.onedrive_remote}{self.onedrive_path}/", '-v']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Successfully uploaded {remote_filename} to OneDrive")
            logger.debug(f"rclone output: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to upload {remote_filename} to OneDrive: {e}")
            logger.error(f"rclone stderr: {e.stderr}")
            return False
    
    def download_url(self, url: str, custom_filename: Optional[str] = None) -> bool:
        """
        Download a single URL and upload to OneDrive
        
        Args:
            url: The URL to download
            custom_filename: Optional custom filename to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            filename = custom_filename or self._get_filename_from_url(url)
            local_file_path = self._download_file(url, filename)
            
            success = self._upload_to_onedrive(local_file_path, filename)
            
            # Clean up local file
            os.remove(local_file_path)
            logger.info(f"Cleaned up temporary file: {local_file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return False
    
    def download_urls_from_file(self, file_path: str) -> List[bool]:
        """
        Download multiple URLs from a text file
        
        Args:
            file_path: Path to file containing URLs (one per line)
            
        Returns:
            List of boolean results for each URL
        """
        results = []
        
        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            logger.info(f"Found {len(urls)} URLs to download")
            
            for i, url in enumerate(urls, 1):
                logger.info(f"Processing URL {i}/{len(urls)}: {url}")
                result = self.download_url(url)
                results.append(result)
                
                if result:
                    logger.info(f"✓ Successfully processed URL {i}")
                else:
                    logger.error(f"✗ Failed to process URL {i}")
            
            successful = sum(results)
            logger.info(f"Download summary: {successful}/{len(urls)} URLs processed successfully")
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error reading URLs from file: {e}")
        
        return results
    
    def __del__(self):
        """Clean up temporary directory"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Download URLs and upload to OneDrive using rclone")
    parser.add_argument('--url', '-u', type=str, help='Single URL to download')
    parser.add_argument('--file', '-f', type=str, help='File containing URLs (one per line)')
    parser.add_argument('--filename', '-n', type=str, help='Custom filename for single URL download')
    parser.add_argument('--remote', '-r', type=str, default='onedrive:', 
                       help='rclone remote name (default: onedrive:)')
    parser.add_argument('--path', '-p', type=str, default='/Downloads',
                       help='OneDrive path (default: /Downloads)')
    parser.add_argument('--check-config', '-c', action='store_true',
                       help='Check rclone OneDrive configuration')
    
    args = parser.parse_args()
    
    try:
        downloader = URLToOneDriveDownloader(args.remote, args.path)
        
        if args.check_config:
            if downloader._check_onedrive_config():
                print("✓ OneDrive is properly configured")
                return 0
            else:
                print("✗ OneDrive configuration not found")
                print("Please run: rclone config")
                return 1
        
        if not downloader._check_onedrive_config():
            logger.warning("OneDrive may not be properly configured. Use --check-config to verify.")
        
        if args.url:
            success = downloader.download_url(args.url, args.filename)
            return 0 if success else 1
            
        elif args.file:
            results = downloader.download_urls_from_file(args.file)
            return 0 if all(results) else 1
            
        else:
            # Interactive mode
            print("URL to OneDrive Downloader")
            print("=" * 30)
            print("Enter URLs to download (one per line), or 'quit' to exit:")
            
            while True:
                try:
                    url = input("\nURL: ").strip()
                    if url.lower() in ['quit', 'exit', 'q']:
                        break
                    if url:
                        downloader.download_url(url)
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
            
            return 0
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())