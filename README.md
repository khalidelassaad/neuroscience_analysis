# TDT Neuroscience Data Processor and Grapher

This repository contains code that processes raw data from TDT photometry experiments and saves graphs of the processed data.

## Directory Structure

⚠️ This code makes strong assumptions about how your files are organized and how directories are structured.

⚠️ Make sure your data is correctly organized as outlined below before running any code!

```
📂 functions/                     # included in this repository

📂🆕 graphs/                      # NEW: directory will be automatically created when `main.py` is run
                                 # Contains `.png` images of generate graphs

📂 experiment_data/               # ⚠️ NOT INCLUDED IN THIS REPOSITORY
|                                # Must be manually created and populated with `raw` data before running `main.py`
|                                # Must be named exactly `experiment_data`
|
+---📂 `date_folder`/              # directory containing data of multiple experiments.
    |                             # ⚠️ folder name MUST be exactly in MMDDYYYY format,
    |                             #     e.g. `03242026`.
    |                             # The full path to this folder must be passed as an argument into the
    |                             # `DateFolderMultiExperimentProcessor` object's `date_folder` parameter
    |                             # at the bottom of `main.py`
    |
    +---📂 `mouse_experiment`/     # directory containing data of a specific experiment on a specific mouse.
        |                          # One or more of these can exist inside a `date_folder`.
        |                          # ⚠️ `mouse_experiment` MUST be structured as follows:
        |                          # `<mouse_name>_<experiment_name>`
        |                          #    e.g. `3653R_ipV`
        |                          # ⚠️ note, ONLY 1 underscore used in the name to separate the two parts
        |
        +---📂 raw/                 # directory containing that mouse's raw data from the
        |   |                       # TDT photometry device.
        |   |                       # ⚠️ Code currently assumes there will be three folders,
        |   |                       #    suffixed `_5hz`, `_10hz`, and `_20hz`.
        |   |                       #    This should be updated soon, parameterized instead of hard-coded.
        |   |
        |   +---📂 03242026_DATNAC_3653R_ipE_5hz   # example folder and example contents,
        |       |                                  # showing expected name structures.
        |       |
        |       +-- VTAstimNAC-260301-110105_03242026_DATNAC_3653R_ipE_5hz.Tbk
        |       +-- VTAstimNAC-260301-110105_03242026_DATNAC_3653R_ipE_5hz.Tdk
        |       +-- VTAstimNAC-260301-110105_03242026_DATNAC_3653R_ipE_5hz.tev
        |       +-- VTAstimNAC-260301-110105_03242026_DATNAC_3653R_ipE_5hz.tin
        |       +-- VTAstimNAC-260301-110105_03242026_DATNAC_3653R_ipE_5hz.tnt
        |       +-- VTAstimNAC-260301-110105_03242026_DATNAC_3653R_ipE_5hz.tsq
        |
        +---📂🆕 extracted/       # NEW: directory will be automatically created when `main.py` is run
        |                        # Contains `mouse_experiment`'s extracted data
        |
        +---📂🆕 processed/       # NEW: directory will be automatically created when `main.py` is run
        |                        # Contains `mouse_experiment`'s processed data
        |
        +---📄🆕 log_`mouse_experiment`.csv  # NEW: file will be automatically created when `main.py` is run
```

## Files

- `main.py` - **The main file to run.** Set the parameters at the bottom of the file then run it with the command `python main.py` in order to process and graph all experiment data for a given day.
- `data_processor.py` - This file takes your `raw` data and processes it in 2 steps. Step 1 creates an `extracted` data folder, using the `tidy_tdt_extract_and_tidy` method from `functions/py_fp.py` [(Source: agordonfennell/OHRBETS, commit: `357e5ea`)](https://github.com/agordonfennell/OHRBETS). Step 2 creates a `processed` data folder, using `functions/tdt_analysis.py` [(Source: zhounapeuw/nape_tidy_photom_tools, commit: `0e7864e`)](https://github.com/zhounapeuw/nape_tidy_photom_tools). Both steps were slightly modified from their initial versions.
- `graph_maker.py` - Makes graphs from `extracted` and `processed` data, both for individual experiments and across all experiments for a given day.
- `utils.py` - Minor utility functions.

## How to Use

### 1. Set up your environment

Create a python virtual environment and install the packages in `requirements.txt` using the command:

```
pip install -r requirements.txt
```

If you are using `anaconda`, the majority of packages inside `requirements.txt` should already be installed in your `(base)` environment. You may only need to install the `tdt` package.

### 2. Run `main.py`

Simply run the command `python main.py`

### 3. Enjoy your graphs!

Graphs will be saved in a directory called `graphs`, grouped by date.
