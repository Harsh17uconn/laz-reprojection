""" original code by Harshana Wedegedara"""
import os
import json
import pdal
import time
import logging
from multiprocessing import Pool, cpu_count
from threading import Thread
from queue import Queue
import signal

# Constants
TIMEOUT_SECONDS = 1200
LOG_DIR = "logs"
CORRUPTED_LOG = os.path.join(LOG_DIR, "corrupted_filesB1.log")
TIMEOUT_LOG = os.path.join(LOG_DIR, "timeout_filesB1.log")
FTUS_TO_METERS = 0.304800609601219

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(CORRUPTED_LOG), logging.StreamHandler()]
    )
    timeout_handler = logging.FileHandler(TIMEOUT_LOG)
    timeout_handler.setLevel(logging.WARNING)
    timeout_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(timeout_handler)

def reproject_laz_file_with_timeout(file_info):
    input_laz_path, output_folder = file_info
    output_laz_path = os.path.join(output_folder, os.path.basename(input_laz_path))
    
    # Skip if the output file already exists
    if os.path.exists(output_laz_path):
        logging.info(f"Skipped (already exists): {output_laz_path}")
        return True  # Indicate success (no processing needed)

    result_queue = Queue()

    def worker():
        try:
            result = reproject_laz_file((input_laz_path, output_folder))
            result_queue.put(("success", result))
        except Exception as e:
            result_queue.put(("error", e))

    thread = Thread(target=worker)
    thread.start()
    thread.join(TIMEOUT_SECONDS)

    if thread.is_alive():
        logging.warning(f"Timeout after {TIMEOUT_SECONDS} seconds: {input_laz_path}")
        return False
    status, result = result_queue.get()
    if status == "error":
        raise result
    return True

def reproject_laz_file(file_info):
    """Convert a LAZ file from ftUS to meters, preserving LAS format."""
    input_laz_path, output_folder = file_info
    output_laz_path = os.path.join(output_folder, os.path.basename(input_laz_path))

    if os.path.exists(output_laz_path):
        logging.info(f"Skipped (already exists): {output_laz_path}")
        return

    scale_matrix = [
        FTUS_TO_METERS, 0, 0, 0,
        0, FTUS_TO_METERS, 0, 0,
        0, 0, FTUS_TO_METERS, 0,
        0, 0, 0, 1
    ]

    pipeline_json = {
        "pipeline": [
            {"type": "readers.las", "filename": input_laz_path},
            {
                "type": "filters.transformation",
                "matrix": " ".join(map(str, scale_matrix))
            },
            {
                "type": "writers.las",
                "filename": output_laz_path,
                "extra_dims": "all",
                "a_srs": "EPSG:6433+5703",
                "dataformat_id": 6,  # Preserve Point Format 6
                "minor_version": 4   # Preserve LAS 1.4
            }
        ]
    }

    try:
        pipeline = pdal.Pipeline(json.dumps(pipeline_json))
        pipeline.execute()
        point_count = pipeline.arrays[0].size
        logging.info(f"Processed {point_count} points (ftUS to meters): {input_laz_path} -> {output_laz_path}")
    except RuntimeError as e:
        logging.error(f"Corrupted file detected: {input_laz_path}: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected issue with {input_laz_path}: {e}")
        raise

def signal_handler(signum, frame):
    logging.info("Received signal to terminate. Cleaning up...")
    raise KeyboardInterrupt

def main():
    input_folder = "G:/test/Before"
    output_folder = "G:/test/reprojected2"

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    setup_logging()

    os.makedirs(output_folder, exist_ok=True)

    files = []
    for f in os.listdir(input_folder):
        if f.endswith(".laz"):
            output_path = os.path.join(output_folder, f)
            input_path = os.path.join(input_folder, f)
            if not os.path.exists(output_path):
                files.append((input_path, output_folder))
            else:
                logging.info(f"Skipped (already exists): {output_path}")

    total_files = len(files)
    logging.info(f"Files to process: {total_files}")

    if total_files == 0:
        logging.info("No files to process. Exiting.")
        return

    num_workers = min(cpu_count(), total_files, 50)
    logging.info(f"Starting processing with {num_workers} workers...")

    start_time = time.time()
    try:
        with Pool(processes=num_workers) as pool:
            results = pool.map(reproject_laz_file_with_timeout, files)
        successful = sum(1 for r in results if r)
        logging.info(f"Processed {successful}/{total_files} files successfully")
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Shutting down pool...")
    except Exception as e:
        logging.error(f"Error during multiprocessing: {e}")
    finally:
        elapsed = time.time() - start_time
        logging.info(f"Processing completed in {elapsed:.2f} seconds!")

if __name__ == "__main__":
    main()
