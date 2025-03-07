# LAZ Reprojection Script

This repository contains a Python script (`reproject_laz.py`) designed to reproject LAZ (compressed LAS) files from US feet (ftUS) to meters, preserving the LAS format and point data attributes. The script leverages the **PDAL (Point Data Abstraction Library)** for efficient point cloud processing and includes parallel processing capabilities to handle large datasets on high-performance computing (HPC) environments.

## Features
- **Unit Conversion**: Transforms coordinates (X, Y, Z) from US feet to meters using a 4x4 transformation matrix.
- **Format Preservation**: Maintains LAS 1.4 format and Point Format 6, including extra dimensions and spatial reference system (EPSG:6433+5703).
- **Parallel Processing**: Utilizes Python's `multiprocessing` to process multiple files simultaneously, optimized for multi-core systems.
- **Timeout Handling**: Implements thread-based timeouts (default 20 minutes) to manage long-running or problematic files.
- **Error Logging**: Records corrupted files, timeouts, and processing details in log files (`logs/corrupted_files.log`, `logs/timeout_files.log`).
- **Skip Existing Files**: Skips reprojecting files that already exist in the output directory to avoid duplicates.

## Requirements
- **Python 3.x**
- **PDAL**: Install via `pip install pdal` (may require additional dependencies like GDAL/GEOS on HPC systems).
- **Dependencies**: `multiprocessing`, `threading`, `queue`, `signal`, `os`, `json`, `time`, `logging`.
- **Conda Environment**: Recommended to use a Conda environment.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Harsh17uconn/laz-reprojection.git
   cd laz-reprojection

2. Set up a Conda environment (optional but recommended):
   ```bash
   conda create -n laz_reproj python=3.9 -y
   conda activate laz_reproj
   pip install pdal, multiprocessing, GDAL....

3. Ensure Git is installed and configured for your system.
   TIMEOUT_SECONDS: Adjustable timeout (default: 1200 seconds or 20 minutes).
   input_folder: Path to source .laz files.
   output_folder: Path to save reprojected .laz files.
   LOG_DIR: Directory for log files (created automatically).

5. Running Locally
   ```bash
   python reproject_laz.py

# Detailed Explanation of the Reprojection Process

## 1. Input Data and File Format
LAZ Files: The script processes .laz files, which are compressed versions of LAS (LiDAR Aerial Survey) files. These files contain 3D point cloud data, including X, Y, Z coordinates, and additional attributes like intensity, classification, and return numbers.
Initial Units: The input coordinates are assumed to be in US feet (ftUS), a common unit in some geospatial datasets, particularly in the United States. The conversion factor FTUS_TO_METERS = 0.304800609601219 is used (1 US survey foot to 1 meter).

## 2. PDAL Pipeline Definition
The reprojection is defined in a JSON pipeline within the reproject_laz_file function. The pipeline consists of three stages:

- **Reader**: Loads the input LAZ file using readers.las.
- **Filter**: Applies a transformation to convert coordinates using filters.transformation.
- **Write**: Saves the transformed data to a new LAS file using writers.las.

- **Here’s the pipeline JSON structure**:
   ```
   {
       "pipeline": [
           {"type": "readers.las", "filename": "input_laz_path"},
           {
               "type": "filters.transformation",
               "matrix": "0.304800609601219 0 0 0 0 0.304800609601219 0 0 0 0 0.304800609601219 0 0 0 0 1"
           },
           {
               "type": "writers.las",
               "filename": "output_laz_path",
               "extra_dims": "all",
               "a_srs": "EPSG:6433+5703",
               "dataformat_id": 6,
               "minor_version": 4
           }
       ]
   }


## 3. Transformation Matrix
- **The core of the reprojection is the scale_matrix, a 4x4 homogeneous transformation matrix**:
   ```
   scale_matrix = [
       FTUS_TO_METERS, 0, 0, 0,
       0, FTUS_TO_METERS, 0, 0,
       0, 0, FTUS_TO_METERS, 0,
       0, 0, 0, 1
   ]

- **Structure**: A diagonal matrix where the diagonal elements (1, 6, 11) scale the X, Y, and Z coordinates, respectively, while the bottom-right element (16) is 1 to preserve the homogeneous coordinate.
- **Scaling**: Each coordinate (X, Y, Z) is multiplied by FTUS_TO_METERS (0.304800609601219), converting the value from ftUS to meters. For example: If X = 1000 ftUS, the new X = 1000 × 0.304800609601219 ≈ 304.8006 meters. The off-diagonal elements (0) ensure no rotation or shearing—only uniform scaling.
- **Homogeneous Coordinates**: The 4x4 matrix format allows PDAL to handle transformations in a way compatible with 3D graphics and geospatial systems, treating points as [X, Y, Z, 1] vectors.

## 4. Execution of the Pipeline
- **The pipeline is created and executed using pdal.Pipeline**:
   ```bash
   pipeline = pdal.Pipeline(json.dumps(pipeline_json))
   pipeline.execute()

- **Execution**: PDAL processes the pipeline sequentially:
   Reads all points from the input .laz file into memory.
   Applies the transformation matrix to each point’s X, Y, and Z coordinates.
   Writes the transformed points to the output .las file.
   Point Count: After execution, pipeline.arrays[0].size retrieves the number of points processed, logged for verification.

## 5. Output Configuration
- **The writers.las stage specifies**:
-filename: The output path.
-extra_dims: "all" preserves additional dimensions (e.g., intensity, classification).
-a_srs: Sets the spatial reference system to EPSG:6433+5703 (likely NAD83 + NAVD88, adjusted for the transformation).
-dataformat_id: 6 preserves the point format (e.g., GPS time, RGB).
-minor_version: 4 maintains LAS 1.4 compatibility.
-This ensures the output .las file retains the structure and metadata of the input while reflecting the new coordinate system.

## 6. Parallel Processing and Timeout Handling
- **Multiprocessing**: The main function uses Pool to process multiple files concurrently, leveraging reproject_laz_file_with_timeout.
- **Timeout**: reproject_laz_file_with_timeout runs reprojection in a Thread with a 20-minute timeout. If the task takes too long (e.g., due to large files or corruption), it’s interrupted and logged (adjust this as needed).

## 7. Error and Skip Logic
- **Skipping Existing Files**: Both reproject_laz_file_with_timeout and reproject_laz_file check if the output file exists using os.path.exists(). If it does, the file is skipped, and a log message is recorded.
- **Error Handling**: If the pipeline fails (e.g., corrupted file), a RuntimeError is caught, logged to corrupted_filesB1.log, and the process continues for remaining files.
