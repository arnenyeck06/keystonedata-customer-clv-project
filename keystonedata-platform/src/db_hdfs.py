"""
HDFS Database Operations for ChurnGuard Platform
Handles reading and querying data from HDFS
"""

import subprocess
import pandas as pd
import io
import argparse

# --- HDFS CONFIG ---
HDFS_NN = "hdfs://namenode:9000"
HDFS_DATA_PATH = f"{HDFS_NN}/churnguard/data/raw"
NAMENODE_CONTAINER = "namenode"


def run_hdfs_command(cmd):
    """
    Execute an HDFS command inside the namenode container.
    Returns: (success: bool, output: str)
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
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def check_connection():
    """
    Test HDFS connection by checking if namenode is accessible.
    """
    print("Testing HDFS connection...")
    
    # Check if container is running
    status = subprocess.run(
        f"docker ps --filter name={NAMENODE_CONTAINER} --format '{{{{.Status}}}}'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if "Up" not in status.stdout:
        print(f"✗ Namenode container '{NAMENODE_CONTAINER}' is not running")
        return False
    
    print(f"✓ Container '{NAMENODE_CONTAINER}' is running")
    
    # Try to access HDFS
    success, output = run_hdfs_command("-ls /")
    
    if success:
        print("✓ HDFS is accessible")
        return True
    else:
        print(f"✗ HDFS connection failed: {output}")
        return False


def read_csv_from_hdfs(hdfs_path):
    """
    Read a CSV file from HDFS and return as pandas DataFrame.
    
    Args:
        hdfs_path: Full HDFS path or relative path under /churnguard/data/raw/
    
    Returns:
        pandas DataFrame or None if failed
    """
    # Handle relative paths
    if not hdfs_path.startswith("hdfs://") and not hdfs_path.startswith("/"):
        hdfs_path = f"{HDFS_DATA_PATH}/{hdfs_path}"
    
    print(f"Reading CSV from HDFS: {hdfs_path}")
    
    # Create temporary file path in container
    temp_file = f"/tmp/hdfs_read_{pd.Timestamp.now().value}.csv"
    
    try:
        # Copy file from HDFS to container's local filesystem
        success, output = run_hdfs_command(f"-get {hdfs_path} {temp_file}")
        
        if not success:
            print(f"Failed to read from HDFS: {output}")
            return None
        
        # Copy file from container to host
        local_temp = f"/tmp/hdfs_temp_{pd.Timestamp.now().value}.csv"
        subprocess.run(
            f"docker cp {NAMENODE_CONTAINER}:{temp_file} {local_temp}",
            shell=True,
            check=True
        )
        
        # Read the CSV
        df = pd.read_csv(local_temp)
        
        # Cleanup
        subprocess.run(f"rm {local_temp}", shell=True, check=False)
        run_hdfs_command(f"-rm {temp_file}")
        
        print(f"✓ Successfully loaded {len(df)} rows")
        return df
        
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None


def list_files(path=None):
    """
    List files in HDFS directory.
    """
    if path is None:
        path = HDFS_DATA_PATH
    elif not path.startswith("hdfs://") and not path.startswith("/"):
        path = f"{HDFS_DATA_PATH}/{path}"
    
    print(f"Listing files in: {path}")
    success, output = run_hdfs_command(f"-ls {path}")
    
    if success:
        print(output)
        return output
    else:
        print(f"Failed to list directory: {output}")
        return None


def get_file_info(hdfs_path):
    """
    Get detailed information about a file in HDFS.
    """
    if not hdfs_path.startswith("hdfs://") and not hdfs_path.startswith("/"):
        hdfs_path = f"{HDFS_DATA_PATH}/{hdfs_path}"
    
    success, output = run_hdfs_command(f"-stat '%n %b %y' {hdfs_path}")
    
    if success:
        print(f"File info for {hdfs_path}:")
        print(output)
        return output
    else:
        print(f"File not found: {hdfs_path}")
        return None


def query_data_sample(filename, num_rows=10):
    """
    Load a sample of data from HDFS CSV file.
    
    Args:
        filename: Name of the CSV file
        num_rows: Number of rows to display
    """
    df = read_csv_from_hdfs(filename)
    
    if df is not None:
        print(f"\n{'='*60}")
        print(f"Sample data from {filename} (first {num_rows} rows):")
        print(f"{'='*60}")
        print(df.head(num_rows))
        print(f"\nShape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        return df
    
    return None


def get_stats(filename):
    """
    Get basic statistics from a CSV file in HDFS.
    """
    df = read_csv_from_hdfs(filename)
    
    if df is not None:
        print(f"\n{'='*60}")
        print(f"Statistics for {filename}:")
        print(f"{'='*60}")
        print(f"Total rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}")
        print(f"\nColumn types:")
        print(df.dtypes)
        print(f"\nMissing values:")
        print(df.isnull().sum())
        print(f"\nNumeric columns summary:")
        print(df.describe())
        return df
    
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HDFS Database Operations")
    parser.add_argument("--test", action="store_true", help="Test HDFS connection")
    parser.add_argument("--list", type=str, nargs="?", const="", help="List files in directory")
    parser.add_argument("--read", type=str, help="Read CSV file from HDFS")
    parser.add_argument("--sample", type=str, help="Show sample data from CSV")
    parser.add_argument("--stats", type=str, help="Show statistics from CSV")
    parser.add_argument("--rows", type=int, default=10, help="Number of rows for sample")
    
    args = parser.parse_args()
    
    if args.test:
        if check_connection():
            print("\n✓ HDFS connection successful!")
        else:
            print("\n✗ HDFS connection failed!")
    
    elif args.list is not None:
        list_files(args.list if args.list else None)
    
    elif args.read:
        df = read_csv_from_hdfs(args.read)
        if df is not None:
            print(f"\nDataFrame loaded with shape: {df.shape}")
    
    elif args.sample:
        query_data_sample(args.sample, args.rows)
    
    elif args.stats:
        get_stats(args.stats)
    
    else:
        print("Usage:")
        print("  python src/db_hdfs.py --test")
        print("  python src/db_hdfs.py --list [path]")
        print("  python src/db_hdfs.py --sample telco_churn.csv --rows 20")
        print("  python src/db_hdfs.py --stats telco_churn.csv")
        print("  python src/db_hdfs.py --read telco_churn.csv")
