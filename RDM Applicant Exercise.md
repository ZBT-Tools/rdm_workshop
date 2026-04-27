# Applicant Exercise: Data Standardization for Time Series Analysis

## Background & Problem Statement

Our laboratory operates multiple test benches that generate time series data in plain-text formats. While these test benches record similar sensor metrics, the internal file structures and data naming conventions vary significantly depending on the specific software program controlling the bench. This inconsistency poses a challenge for centralized data storage and analysis.

## Project Task

Your objective is to develop a robust, reusable parsing library. Using the two provided example data files, you must create a solution that:

* Parses each distinct file format accurately.
* Transforms the raw data into a single, standardized structure.
* Ensures compatibility with a MongoDB Time Series collection.
* Can be imported and reused from a separate analysis workflow.

If you are unable to instantiate a local MongoDB instance, the output should be provided as a structured JSON file that reflects the schema intended for the database. A JSON fallback is fully acceptable; it should still demonstrate the intended MongoDB time-series structure.

## Scope and AI Assistance

You may choose one of the following scopes for your submission. Please state clearly in your README which scope you chose and whether, where, and how you used AI-assisted coding tools.

### Core Library Focus

Choose this scope if you implement the programming logic substantially yourself and use no or only limited AI assistance.

For this scope, the main required deliverable is the reusable parsing library. We will primarily evaluate the correctness of the parsing logic, the data standardization, code structure, tests for the parser behavior, and your ability to explain the implementation during the interview. A small usage example is sufficient to show that the library can be imported and used from another workflow.

### Full Workflow Focus

Choose this scope if you use AI-assisted coding substantially or if you want to demonstrate the complete engineering workflow.

For this scope, complete the full two-repository workflow described below, including package setup, tests, CI, notebook integration, installation instructions, and documented design decisions. In the interview, you should be able to explain and defend the generated or AI-assisted parts of the solution.

## Specific Requirements

### 1. Data Files to Standardize

* **First Data Set (Testbench: BZ011):**
  * Raw data: [data/BZ011_Rohdaten.dat](https://github.com/ZBT-Tools/rdm_workshop/blob/exercise/data/BZ011_Rohdaten.dat)
  * Metadata: [data/metadata_BZ011_Rohdaten.json](https://github.com/ZBT-Tools/rdm_workshop/blob/exercise/data/metadata_BZ011_Rohdaten.json)
* **Second Data Set (Testbench: Greenlight):**
  * Raw data: [data/test_greenlight.csv](https://github.com/ZBT-Tools/rdm_workshop/blob/exercise/data/test_greenlight.csv)
  * Metadata: Included in raw data CSV.

### 2. Implementation and Delivery

For the **Core Library Focus**, only Repository 1 is required. For the **Full Workflow Focus**, the solution should be delivered as **two separate GitHub repositories**.

#### Repository 1: Parsing Library

This repository contains the reusable Python parsing library.

Required contents:

* A **Python package** that can parse both the BZ011 and Greenlight input formats.
* A `pyproject.toml` file defining the package and its dependencies.
* Clear installation and usage instructions in the `README.md`.
* Tests that verify the parser behavior for both example data sets.
* A **GitHub Actions workflow** that runs the test suite on pushes and pull requests to the repository's default branch. This is required for the Full Workflow Focus and optional for the Core Library Focus.

The package should be installable from another environment, for example by using one of the following approaches:

```bash
pip install -e /path/to/parser-repository
```

or

```bash
pip install git+https://github.com/<user>/<parser-repository>.git
```

#### Repository 2: Example Usage / Adapted Notebook

Repository 2 is required for the Full Workflow Focus and optional for the Core Library Focus.

This repository demonstrates how the parsing library is used from a separate analysis workflow.

Required contents for the Full Workflow Focus. For the Core Library Focus, these contents are optional if Repository 2 is submitted:

* An adapted version of the provided Jupyter Notebook: [mongodb_upload.ipynb](https://github.com/ZBT-Tools/rdm_workshop/blob/exercise/mongodb_upload.ipynb)
* The notebook must import and use the parsing library from Repository 1.
* The notebook should replace direct, format-specific parsing logic with calls to the new parsing library.
* The notebook should demonstrate output generation for both provided data sets.
* The notebook should either upload the standardized records to MongoDB or produce a MongoDB-compatible JSON output.
* The repository must include a short `README.md` explaining how to install the parsing library and run the notebook.

The purpose of the two-repository structure is to demonstrate that the parser is reusable and not only hard-coded for one notebook, one file path, or one local environment.

#### Submission

Please submit the URL of each GitHub repository that belongs to your chosen scope. If the repositories are private, make sure we have access. Include the branch name or commit hash that should be reviewed.

### 3. Required Standardized Schema

Try to find common metadata entries and decide on a common naming scheme for metadata where appropriate. Metadata should be handled separately from the measurement values, for example as a MongoDB Time Series `metaField` document or as a separate `metadata` object in JSON output. The standardized measurement records themselves should contain only the time-series fields listed below.

For the final time-series records, only extract the following three fields and use these exact names for the final database schema:

| Standardized field | Description | Unit / type |
| :---- | :---- | :---- |
| `time_stamp` | Timestamp of the measurement | datetime |
| `cell_voltage` | Measured cell voltage | V |
| `current_density` | Current density of the cell or stack | A/cm2 |

**MongoDB compatibility:** For MongoDB Time Series compatibility, `time_stamp` should be stored as a proper datetime value. If JSON output is used instead of MongoDB, `time_stamp` should be serialized as an ISO 8601 timestamp string.

**Timestamp assumptions:** Parse the timestamps from the source files without changing their measurement order. The BZ011 `Datum` values use day-month-year ordering. If a source timestamp does not contain timezone information, treat it consistently and document the assumption in the README.

Example JSON output:

```json
{
  "metadata": {
    "testbench": "BZ011",
    "active_area_cm2": 25
  },
  "records": [
    {
      "time_stamp": "2024-08-05T13:11:02",
      "cell_voltage": 0.00039,
      "current_density": 0.0083936
    }
  ]
}
```

## First Data Set: BZ011

| Standardized field | Source column | Required transformation |
| :---- | :---- | :---- |
| `time_stamp` | `Datum` | Parse as datetime |
| `cell_voltage` | `Spg U / V` | Direct mapping |
| `current_density` | `Strom I / A` | Divide current by active cell area from metadata |

**Important:** The BZ011 raw data does not contain current density directly. It contains current in amperes. The BZ011 metadata contains `active_area_cm2`, so applicants must calculate current density in A/cm2 as:

```text
current_density = current_A / active_area_cm2
```

## Second Data Set: Greenlight

| Standardized field | Source column | Required transformation |
| :---- | :---- | :---- |
| `time_stamp` | `Time Stamp` | Parse as datetime |
| `cell_voltage` | `cell_voltage_mean` | Direct mapping |
| `current_density` | `current_density` | Direct mapping |

The Greenlight CSV contains a metadata preamble before the data table. The data header row contains the columns listed above. The `current_density` source column is already given in A/cm2.

## Notes for Applicants

The parser should produce a consistent output structure across both input formats.

* The final output should contain only the standardized time-series fields: `time_stamp`, `cell_voltage`, and `current_density`.
* Source-specific column names should not appear in the final standardized time-series records.
* For BZ011, `current_density` must be calculated from current and active area.
* For Greenlight, `current_density` can be mapped directly from the existing column.
* The implementation should be structured so that additional file formats and additional standardized quantities could be added later without rewriting the complete parser.
* Avoid hard-coded absolute file paths. The solution should be usable on both Windows and Linux systems.
* Real-world laboratory exports often contain locale-specific number formats, unusual headers, metadata preambles, and encoding artifacts. Your parser should handle the provided files robustly and document any assumptions.
* The README should include a short section describing design decisions, metadata handling, timestamp handling, unit handling, and known limitations.
* You may use AI assistance, but you should disclose it and be prepared to explain the implementation, design choices, and trade-offs during the interview.
