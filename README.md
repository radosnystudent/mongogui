# MongoDB GUI Client

A modern, user-friendly desktop GUI application for connecting to MongoDB databases, browsing collections, and executing queries with an intuitive interface built with PyQt5.

## Features

### Core Functionality

- **Secure Connection Management**: Store and manage multiple MongoDB connections with encrypted credential storage using keyring
- **Database Operations**: Connect to MongoDB instances (local and remote) with authentication support
- **Query Execution**: Execute MongoDB find queries and aggregation pipelines with syntax highlighting
- **Results Display**: View query results in a formatted table with pagination support
- **Collection Browser**: Browse database collections and view their structure

### User Interface

- **Modern PyQt5 Interface**: Clean, responsive GUI with intuitive navigation
- **Connection Dialog**: Easy-to-use connection setup with validation
- **Query Editor**: Dedicated query input area with proper formatting
- **Results Viewer**: Paginated table display for large result sets
- **Status Indicators**: Real-time connection and operation status

### Security & Quality

- **Secure Credential Storage**: Passwords stored using the system keyring
- **Type Safety**: Full type annotations with MyPy validation
- **Comprehensive Testing**: Unit tests for all major components
- **Code Quality**: Formatted with Black, linted with Ruff, security scanned with Bandit

## Requirements

- Python 3.8+
- MongoDB instance (local or remote)
- Windows, macOS, or Linux

## Installation

### Using Virtual Environment (Recommended)

1. **Clone or download the project**
2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:

   ```bash
   # Windows
   .\venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

### Quick Start with Scripts

**Universal Launcher (Cross-Platform)**:

```bash
python launcher.py
```

**Linux/macOS** - Shell scripts:

```bash
# Make scripts executable
chmod +x scripts/*.sh

# One-time setup
./scripts/setup.sh

# Run the application
./scripts/run.sh
```

**Windows** - PowerShell script:

```powershell
.\scripts\run.ps1
```

### Development Setup

For development with additional tools:

```bash
pip install -r requirements-dev.txt

# Or use the development script (Linux/macOS)
./scripts/dev.sh dev-setup
```

## Usage

### 1. Starting the Application

Run `python main.py` to launch the MongoDB GUI client.

### 2. Creating a Connection

1. Click "Add Connection" to open the connection dialog
2. Fill in the connection details:
   - **Name**: A friendly name for your connection
   - **Host**: MongoDB server hostname or IP (default: localhost)
   - **Port**: MongoDB port (default: 27017)
   - **Database**: Target database name
   - **Username/Password**: Authentication credentials (optional)
3. Click "Test Connection" to verify the connection
4. Click "Save" to store the connection

### 3. Connecting to a Database

1. Select a saved connection from the dropdown
2. Click "Connect" to establish the connection
3. The collection browser will populate with available collections

### 4. Executing Queries

1. Ensure you're connected to a database
2. Enter your MongoDB query in the query text area:

   ```javascript
   // Find query example
   {"name": "John", "age": {"$gte": 25}}

   // Aggregation pipeline example
   [{"$match": {"status": "active"}}, {"$group": {"_id": "$department", "count": {"$sum": 1}}}]
   ```

3. Click "Execute Query" to run the query
4. Results will appear in the table below with pagination controls

### 5. Browsing Collections

- The left panel shows all collections in the connected database
- Click on a collection to see a sample of documents
- Use this to understand the structure of your data

## Project Structure

```
mongogui/
├── core/                   # Core business logic
│   ├── connection_manager.py  # Connection and credential management
│   └── mongo_client.py        # MongoDB operations wrapper
├── gui/                    # User interface components
│   ├── app.py                 # Application entry point
│   ├── main_window.py         # Main application window
│   └── connection_dialog.py   # Connection setup dialog
├── tests/                  # Unit tests
│   ├── test_connection_manager.py
│   ├── test_main_window.py
│   └── test_mongo_client.py
├── main.py                # Application launcher
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Development dependencies
└── pyproject.toml        # Project configuration
```

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Code Quality Checks

```bash
# Type checking
mypy .

# Linting
ruff check .

# Formatting
black .

# Security scan
bandit -r core/ gui/ -f json -o bandit-report.json
```

### Building for Distribution

```bash
python -m build
```

## Troubleshooting

### Connection Issues

- Verify MongoDB server is running and accessible
- Check firewall settings if connecting to remote MongoDB
- Ensure authentication credentials are correct
- Test connection using MongoDB shell or compass first

### GUI Issues

- Ensure PyQt5 is properly installed
- On Linux, you may need to install additional Qt5 packages
- Try running with `python -v main.py` for verbose output

### Performance

- For large result sets, use pagination or limit queries
- Consider using aggregation pipelines for complex operations
- Monitor memory usage with very large datasets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the quality checks
5. Submit a pull request

## License

This project is open source and available under the MIT License.
