"""
HDFS Data Ingestion Script for ChurnGuard Platform
Uploads raw data files to Hadoop HDFS from macOS
"""

import os
import argparse
import subprocess

# --- HDFS CONFIG ---
HDFS_NN = "hdfs://hadoop-namenode:9000"
HDFS_TARGET = f"{HDFS_NN}/churnguard/data/raw"

# Name of the namenode container (must match docker-compose)
NAMENODE_CONTAINER = "namenode"


def run_hdfs(cmd):
    """
    Run an HDFS command inside the namenode container.
    """
    full_cmd = f"docker exec {NAMENODE_CONTAINER} hdfs dfs {cmd}"

    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print("HDFS command failed:")
        print(e.stderr)
        return None


def upload_file(local_path, hdfs_name=None):
    """
    Upload a local file into HDFS.
    """

    if not os.path.exists(local_path):
        print(f"Local file not found: {local_path}")
        return False

    if hdfs_name is None:
        hdfs_name = os.path.basename(local_path)

    print(f"Uploading file: {local_path}")

    container_tmp = f"/tmp/{os.path.basename(local_path)}"

    try:
        # Copy file to the namenode container
        subprocess.run(
            f"docker cp {local_path} {NAMENODE_CONTAINER}:{container_tmp}",
            shell=True,
            check=True
        )

        hdfs_dest = f"{HDFS_TARGET}/{hdfs_name}"

        # Make sure directory exists in HDFS
        run_hdfs(f"-mkdir -p {HDFS_TARGET}")

        # Upload the file
        result = run_hdfs(f"-put -f {container_tmp} {hdfs_dest}")

        if result is None:
            print("Upload failed.")
            return False

        # Verify upload
        ls_output = run_hdfs(f"-ls {hdfs_dest}")
        if ls_output:
            print(f"File uploaded to HDFS: {hdfs_dest}")
            return True

        print("Upload attempted, but could not verify the file.")
        return False

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def upload_main_dataset():
    """
    Upload the main telco_churn.csv dataset to HDFS.
    """
    print("Starting HDFS upload")

    # Check if namenode container is running
    status = subprocess.run(
        f"docker ps --filter name={NAMENODE_CONTAINER} --format '{{{{.Status}}}}'",
        shell=True,
        capture_output=True,
        text=True
    )

    if "Up" not in status.stdout:
        print("Namenode container is not running.")
        print(f"Start it using: docker compose up -d {NAMENODE_CONTAINER}")
        return False

    dataset = "data/raw/telco_churn.csv"

    if not os.path.exists(dataset):
        print(f"Dataset not found: {dataset}")
        print("Download with:")
        print("wget -O data/raw/telco_churn.csv https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv")
        return False

    if upload_file(dataset, "telco_churn.csv"):
        print("Dataset uploaded successfully.")
        print(f"Stored in HDFS at: {HDFS_TARGET}/telco_churn.csv")
        return True

    print("Dataset upload failed.")
    return False


def list_hdfs_files():
    """
    List files stored in the HDFS raw directory.
    """
    print(f"Listing files in: {HDFS_TARGET}")
    result = run_hdfs(f"-ls {HDFS_TARGET}")

    if result:
        print(result)
    else:
        print("Directory not found or empty.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HDFS Ingestion Tools")
    parser.add_argument("--upload", action="store_true", help="Upload main dataset")
    parser.add_argument("--file", type=str, help="Upload a specific file")
    parser.add_argument("--list", action="store_true", help="List files in HDFS")

    args = parser.parse_args()

    if args.upload:
        upload_main_dataset()
    elif args.file:
        upload_file(args.file)
    elif args.list:
        list_hdfs_files()
    else:
        print("Usage:")
        print("  python src/ingest_hdfs.py --upload")
        print("  python src/ingest_hdfs.py --file <path>")
        print("  python src/ingest_hdfs.py --list")

