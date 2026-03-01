from hdfs import InsecureClient
import pandas as pd
import argparse
import sys
import os
import re

HDFS_CONFIG = {
    'url': 'http://localhost:9870',
    'user': 'root'
}

def get_hdfs_client():
    """Create HDFS client connection with DataNode redirect fix"""
    try:
        client = InsecureClient(HDFS_CONFIG['url'], user=HDFS_CONFIG['user'])

        # Patch session to rewrite DataNode hostname in redirects
        # (DataNode advertises its Docker internal hostname which can't be resolved outside Docker)
        original_resolve = client._session.resolve_redirects
        def patched_redirects(resp, req, **kwargs):
            for r in original_resolve(resp, req, **kwargs):
                if r.url:
                    r.url = re.sub(r'http://[^/]+:9864', 'http://localhost:9864', r.url)
                yield r
        client._session.resolve_redirects = patched_redirects

        return client
    except Exception as e:
        print(f"Error connecting to HDFS: {e}")
        sys.exit(1)

def ingest_to_hdfs(csv_file, hdfs_path='/churn/data/'):
    """Upload CSV file to HDFS"""
    try:
        # Check if file exists
        if not os.path.exists(csv_file):
            print(f"✗ File not found: {csv_file}")
            sys.exit(1)

        print(f"Reading {csv_file}...")

        # Get HDFS client
        client = get_hdfs_client()

        # Create directory if it doesn't exist
        print(f"Creating HDFS directory: {hdfs_path}")
        try:
            client.makedirs(hdfs_path)
        except:
            pass  # Directory might already exist

        # Get filename
        filename = os.path.basename(csv_file)
        hdfs_file_path = os.path.join(hdfs_path, filename)

        # Upload file
        print(f"Uploading to HDFS: {hdfs_file_path}")
        client.upload(hdfs_file_path, csv_file, overwrite=True)

        # Verify upload
        file_status = client.status(hdfs_file_path)
        file_size_mb = file_status['length'] / (1024 * 1024)

        print(f"✓ Successfully uploaded to HDFS")
        print(f"  Path: {hdfs_file_path}")
        print(f"  Size: {file_size_mb:.2f} MB")

        # List files in directory
        print(f"\nFiles in {hdfs_path}:")
        files = client.list(hdfs_path)
        for f in files:
            print(f"  - {f}")

    except Exception as e:
        print(f"✗ Error ingesting to HDFS: {e}")
        sys.exit(1)

def verify_hdfs():
    """Verify HDFS connection and list files"""
    try:
        client = get_hdfs_client()

        print("✓ Connected to HDFS")

        # List root directory
        print("\nRoot directory contents:")
        try:
            files = client.list('/')
            for f in files:
                print(f"  - /{f}")
        except Exception as e:
            print(f"  (empty or error: {e})")

        # Check churn directory
        print("\nChurn data directory:")
        try:
            files = client.list('/churn/data/')
            for f in files:
                status = client.status(f'/churn/data/{f}')
                size_mb = status['length'] / (1024 * 1024)
                print(f"  - {f} ({size_mb:.2f} MB)")
        except Exception as e:
            print(f"  (not found or error: {e})")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HDFS Data Ingestion')
    parser.add_argument('csv_file', nargs='?', help='Path to CSV file to upload')
    parser.add_argument('--verify', action='store_true', help='Verify HDFS connection')
    parser.add_argument('--path', default='/churn/data/', help='HDFS destination path')

    args = parser.parse_args()

    if args.verify:
        verify_hdfs()
    elif args.csv_file:
        ingest_to_hdfs(args.csv_file, args.path)
    else:
        print("Usage:")
        print("  python src/ingest_hdfs.py data/raw/telco_churn.csv")
        print("  python src/ingest_hdfs.py --verify")