# Selenium Python Automation Framework

Interface automation testing framework for Web Applications.
This framework is built on **Python**, **Selenium**, **Pytest** and detailed reporting with **Allure Report**.

---

## 🚀 Tech Stack

The main technologies and libraries used in the project include:

| Name              | Version            | Main purpose                          |
|-------------------|--------------------|----------------------------------------|
| Language          | Python 3.12         | Main programming language              |
| Test Framework    | pytest==8.4.1      | Test runner and management tool        |
| Automation        | selenium==4.38.0   | Browser interaction                    |
| Reporting         | allure-python-commons==2.15.0 | Detailed test reports       |
| Soft Assertions   | pytest_check==2.6.2| Soft assertions support                |
| Email Testing     | mailslurp_client==17.0.0 | Email testing (e.g., signups)   |
| Env Vars          | python-dotenv==1.2.1 | Environment variables management   |

---

## 🏗️ Project Structure

Below is the main directory structure of the framework:

```text
.
├── core/                   # Core framework code (drivers, logging, reporting, utils)
│   ├── assertion/          # Hard/Soft Asserts logic
│   ├── configuration/      # Configuration file handling
│   ├── constants/          # Constants definitions
│   ├── driver/             # Driver management, Waiter
|       ├── providers       # Browser factories 
│   ├── element/            # Custom Element class
│   ├── logging/            # Logger configuration
│   ├── report/             # Allure Reporter integration
│   └── utils/              # Utility functions
├── pages/                  # Page Object Model (PO) for specific web pages
│   └── **testpage/              # PO for the test website
├── resources/              # Test data, JSON configuration files
│   └── **testpage/ 
├── tests/                  # Actual Test Cases (test_*.py)
│   └── **testpage/ 
├── venv/                   # Python virtual environment
├── .env                    # Local environment variables
├── .env.example            # Example environment variables file
├── app.log                 # Log file output
├── conftest.py             # Pytest Hooks and Fixtures configuration
└── pytest.ini              # Default Pytest configuration
```

---

## ⚙️ Installation

### 1. Clone repository

```bash
git clone https://github.com/anthienduong1212/selenium-python-anduong.git
cd Selenium_Python
```

### 2. Create and activate virtual environment

```bash
python -m venv venv
# Windows:
.
env\Scripts ctivate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install necessary libraries

```bash
pip install -r requirements.txt
```

### 4. Install Allure Report CLI

You need to install the Allure command-line tool on your system (e.g., via Homebrew on macOS, Chocolatey on Windows).

---

## 🎮 Running Tests

Use pytest to run test cases. Default configurations are defined in `pytest.ini`.  
**Default Pytest Config**: Runs on Chrome, generates Allure results, retries failed tests 3 times.

### 1. Run all test cases

```bash
pytest
```
By default, when running the pytest command, the system will use the **Chrome** browser and save the **Allure Results** to the *allure-results* folder.

All definitions that related to test case such as files, classes, functions should start
with:
```bash
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```
### 2. Selenium Grid Setup: Hub and Nodes
#### a. Setup Hub and Nodes
#### Step 1: Installation
Download the Selenium Server package at: https://www.selenium.dev/downloads/

#### Step 2: Start the Hub
Open the command prompt, and navigate to the directory where the Selenium Server Standalone JAR file is stored (downloaded in Step 1) using the following command:

```bash
java -jar selenium-server-<version>.jar hub
```

#### Step 3: Start Nodes
Open the command prompt, navigate to the directory where the Selenium Server Standalone JAR file is stored and type the following command:

```bash
java -jar selenium-server-<version>.jar node --hub <hub-url> --selenium-manager true --port <port>
```

- Nodes have to be on different ports with each other and hub if they are on the same machine.
- Hub URL is required if Hub and Nodes are on different machines.

#### b. Run test on Grid

To run tests on Grid, enter hub URL to the config `REMOTE` in .env file before starting test via command

---

## Advanced CLI options (Overriding defaults)

You can customize test execution using CLI flags:

| CLI Flag        | Example                                | Description                                          |
|-----------------|----------------------------------------|------------------------------------------------------|
| `--browser`     | `pytest --browser firefox`             | Run on a specific browser (chrome, firefox, edge).   |
| `--browsers`    | `pytest --browsers chrome edge`        | Run tests in parallel on multiple browsers.          |
| `--parallel-mode` | `pytest --parallel-mode per-test`    | Parallel execution mode (per-test, per-worker, none). |
| `--browser-config` | `pytest --browser-config path/`     | Override the default browser configuration file.     |

---

## Generate and view Allure Report

After running tests, you can generate the HTML report and open it in your browser:

```bash
allure serve ./allure-results/
```

---

## ⭐ Key Features

- **Automatic Driver Discovery**: The framework automatically scans packages for BrowserProvider implementations using the *@register_provider* decorator, simplifying the integration of new browsers via configuration parameters.
- **Detailed Reporting**: Uses Allure Report với `@allure.step`, Attachments (screenshots on failure/assert), và environment information.
- **Hard & Soft Assertions**: Supports both assertion types via Dependency Injection và `autouse=True` Fixtures.
- **Automatic Retry**: Automatically rerun failed test cases `pytest-rerunfailures`.
- **Flexible CLI**: Easily configure browser type, headless mode, and **Selenium Grid** via command line.
