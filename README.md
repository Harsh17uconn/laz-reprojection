# LAZ Reprojection Script

This repository contains a Python script (`reproject_laz.py`) designed to reproject LAZ (compressed LAS) files from US feet (ftUS) to meters, preserving the LAS format and point data attributes. 
The script leverages the **PDAL (Point Data Abstraction Library)** for efficient point cloud processing and includes parallel processing capabilities to handle large datasets on high-performance computing (HPC) environments.

## Features
- **Unit Conversion**: Transforms coordinates from US feet to meters using a 4x4 transformation matrix.
- **Format Preservation**: Maintains LAS 1.4 format and Point Format 6, including extra dimensions and spatial reference system (e.g.EPSG:6433+5703).
- **Parallel Processing**: Utilizes Python's `multiprocessing` to process multiple files simultaneously, optimized for multi-core systems.
- **Timeout Handling**: Implements thread-based timeouts to manage long-running or problematic files.
- **Error Logging**: Records corrupted files, timeouts, and processing details in log files (`logs/corrupted_files.log`, `logs/timeout_files.log`).
- **Skip Existing Files**: Skips reprojecting files that already exist in the output directory to avoid duplicates.

## Requirements
- **Python 3.x**
- **PDAL**: Install via `pip install pdal` (may require additional dependencies like GDAL/GEOS on HPC systems).
- **Dependencies**: `numpy`, `multiprocessing`, `threading`, `queue`, `signal`, `os`, `json`, `time`, `logging`.
- **Conda Environment**: Recommended to use a Conda environment.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Harsh17uconn/laz-reprojection.git
   cd laz-reprojection
