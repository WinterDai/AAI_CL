A collection of utility scripts and tools for AI-powered automation tasks.

## Table of Contents

- [AI Model Completion](#ai-model-completion)
- [Confluence Scraper](#confluence-scraper)
- [Contributing](#contributing)

---

## AI Model Completion

This utility provides easy access to test various AI models through the JEDAI API with secure LDAP authentication. Perfect for testing different AI models, comparing responses, and getting started with JEDAI AI capabilities.

## ⭐ Recent Enhancements (October 2025)

The script has been significantly enhanced with powerful new features:

- **📄 File Input Support**: Read prompts from text files for complex specifications
- **💾 Automatic Module Saving**: Extract and save SystemVerilog modules to separate `.sv` files  
- **🔧 Improved Environment Detection**: Better DPC/non-DPC detection with fallback URLs
- **🌐 URL Fallback System**: Robust connectivity with automatic failover
- **🔍 Enhanced Debugging**: Comprehensive environment and connectivity diagnostics
- **📚 Community Guide**: Specialized guide for SSG AAI RTL workflows

> **For RTL Design Teams**: This tool now automatically extracts SystemVerilog modules from AI responses and saves them as separate files, making it perfect for RTL generation workflows!

## 🚀 Quick Start

### Prerequisites
```bash
# Clone this repository (if not already done)
git clone git@github.cadence.com:rvasappa/ssg_aai_lego.git
cd ssg_aai_lego

# Make the script executable
chmod +x utils/jedai_completion.py
```

### Basic Usage Examples

```bash
# List all available AI models
./utils/jedai_completion.py --list

# Test with default model and query (auto-detects environment)
./utils/jedai_completion.py

# Test specific model
./utils/jedai_completion.py --model claude-opus-4

# Ask a custom question
./utils/jedai_completion.py --query "Explain quantum computing"

# 🆕 Read prompt from text file
./utils/jedai_completion.py --file design_spec.txt

# 🆕 Generate SystemVerilog modules and auto-save them
./utils/jedai_completion.py --file afifo_spec.txt --save-modules

# 🆕 Test connectivity to all JEDAI servers
./utils/jedai_completion.py --test-urls

# Override auto-detected URL (optional)
./utils/jedai_completion.py --url http://custom-server.com:5668 --query "Test connection"
```

**🎯 New Feature**: The script automatically detects if you're running in DPC or non-DPC environment and configures the correct JEDAI server URL!

## 🧠 Available AI Models

The script supports multiple state-of-the-art AI models:

| Model Key | Model Name | Family | Description |
|-----------|------------|--------|-------------|
| `claude-opus-4` | Claude Opus 4 | Claude | Most capable model with superior reasoning |
| `claude-sonnet-4` | Claude Sonnet 4 | Claude | Balanced performance and speed |
| `gemini-2-5-pro` | Gemini 2.5 Pro | GEMINI | Google's advanced multimodal model |
| `gemini-2-5-flash` | Gemini 2.5 Flash | GEMINI | Google's fast and efficient model |

## 📖 Step-by-Step Tutorial

### Step 1: List Available Models
First, see what AI models you can test:

```bash
$ ./utils/jedai_completion.py --list
Available Models:
----------------------------------------
claude-opus-4        Claude Opus 4
claude-sonnet-4      Claude Sonnet 4
gemini-2-5-pro       Gemini 2.5 Pro
gemini-2-5-flash     Gemini 2.5 Flash
----------------------------------------
```

### Step 2: Test Default Configuration
Try the script with default settings (Claude Opus 4 model with a simple question):

```bash
$ ./utils/jedai_completion.py
Testing claude-opus-4 with: What is the capital of France?
--------------------------------------------------
Password: ●●●●●●●●
✅ Logged in

Response:
The capital of France is Paris.
```

**What happened:**
- Script used your system username for LDAP authentication
- Connected to default JEDAI server: `http://ssgdpc-jedai.cadence.com:5000`
- Tested Claude Opus 4 model with default query
- Received and displayed the AI response

### Step 3: Test Different Models
Compare responses from different AI models:

```bash
# Test Claude Opus 4
$ ./utils/jedai_completion.py --model claude-opus-4 --query "Explain artificial intelligence"
Testing claude-opus-4 with: Explain artificial intelligence
--------------------------------------------------
Password: ●●●●●●●●
✅ Logged in

Response:
Artificial Intelligence (AI) refers to the simulation of human intelligence in machines...
[detailed response]

# Test Gemini model  
$ ./utils/jedai_completion.py --model gemini-2-5-pro --query "Explain artificial intelligence"
Testing gemini-2-5-pro with: Explain artificial intelligence
--------------------------------------------------
Password: ●●●●●●●●
✅ Logged in

Response:
AI, or Artificial Intelligence, is a branch of computer science focused on creating systems...
[different perspective and style]
```

### Step 4: Use Custom Queries
Ask specific questions relevant to your work:

```bash
# Technical question
$ ./utils/jedai_completion.py --model claude-sonnet-4 --query "How do I optimize Python code performance?"

# Creative task
$ ./utils/jedai_completion.py --model gemini-2-5-flash --query "Write a Python function to calculate fibonacci numbers"

# Domain-specific query
$ ./utils/jedai_completion.py --query "Explain the differences between ASIC and FPGA design approaches"
```

### Step 5: Automatic Environment Detection

The script now **automatically detects** your environment and configures itself:

**🏢 DPC Environment**: 
- Auto-detects hostnames with: `dpc`, `nfdpc`, `ssgdpc`, `atl`, `cadence.com`
- Uses: `http://ssgdpc-jedai.cadence.com:5000`
- Uses system Python from nu_pkgs area

**🌐 Non-DPC Environment**:
- Auto-detects other environments  
- Uses: `http://sjf-dsgdspr-084.cadence.com:5668`
- Requires Python 3.6+ from user environment

**Example Output:**
```bash
$ ./utils/jedai_completion.py --query "Test connection"
🌐 Environment Detection:
   Hostname: your-hostname
   Environment: DPC
   JEDAI URL: http://ssgdpc-jedai.cadence.com:5000
--------------------------------------------------
Testing claude-opus-4 with: Test connection
```

**Manual Override** (if needed):
```bash
# Override auto-detection
$ ./utils/jedai_completion.py --url http://custom-server.com:5668 --query "Test connection"
```

## ⚙️ Command Reference

### Full Command Syntax
```bash
./utils/jedai_completion.py [options]

Options:
  --list                List all supported AI models and exit
  --test-urls           Test connectivity to all JEDAI URLs
  --model MODEL         AI model to test (default: claude-opus-4)  
  --query QUERY         Question/prompt to ask the AI
  --file FILE          🆕 Read query from text file
  --save-modules       🆕 Auto-save generated SystemVerilog modules to separate files
  --output-dir DIR     🆕 Directory to save generated module files (default: current directory)
  --url URL            Override auto-detected JEDAI server URL (optional)
```

### Automatic Server Configuration
- **🏢 DPC Environment**: Auto-detected → `http://ssgdpc-jedai.cadence.com:5000`
- **🌐 Non-DPC Environment**: Auto-detected → `http://sjf-dsgdspr-084.cadence.com:5668`
- **🔧 Manual Override**: Use `--url` parameter to specify custom server

✅ **No manual configuration needed!** The script automatically detects your environment and uses the appropriate server.

## 🔐 Authentication

### How Authentication Works
1. **Username**: Automatically uses your system username (`getpass.getuser()`)
2. **Password**: Securely prompts for your LDAP password (masked input)
3. **Provider**: Uses LDAP authentication backend
4. **Token**: Receives JWT token for API requests

### Security Features
- **Password masking**: Your password is never displayed on screen
- **JWT tokens**: Secure token-based authentication
- **No credential storage**: Script doesn't save passwords anywhere
- **LDAP integration**: Uses your existing corporate credentials

## 🆕 Enhanced Features for RTL Design

### File Input Support
Read complex prompts from text files instead of command line:

```bash
# Create a specification file
cat > axi_interface_spec.txt << 'EOF'
Create a SystemVerilog AXI4-Lite slave interface module with the following specifications:
- 32-bit address and data width
- Support for read and write transactions
- Include address decoding for 4 registers
- Add proper error responses for invalid addresses
- Include comprehensive comments and parameter documentation
EOF

# Generate RTL from file
./utils/jedai_completion.py --file axi_interface_spec.txt --model claude-opus-4
```

### Automatic SystemVerilog Module Saving
Automatically extract and save modules from AI responses:

```bash
# Generate and auto-save modules
./utils/jedai_completion.py --file design_spec.txt --save-modules

# Save to specific directory
./utils/jedai_completion.py --file spec.txt --save-modules --output-dir ./generated_rtl

# Example output:
# 🔍 Extracting and saving SystemVerilog modules...
# Found 3 module(s):
#   - axi_slave_interface
#   - register_bank
#   - address_decoder
# ✅ Saved module 'axi_slave_interface' to ./axi_slave_interface.sv
# ✅ Saved module 'register_bank' to ./register_bank.sv  
# ✅ Saved module 'address_decoder' to ./address_decoder.sv
```

### Enhanced Environment Detection & Connectivity
Robust connection handling with automatic fallbacks:

```bash
# Test all available JEDAI servers
./utils/jedai_completion.py --test-urls

# Example output:
# 🔗 Testing JEDAI URL Connectivity:
# Testing http://ssgdpc-jedai.cadence.com:5000... ✅ Connected
# Testing http://sjf-dsgdspr-084.cadence.com:5668... ❌ Failed
```

### RTL Design Workflow Example
Complete workflow for RTL generation:

```bash
# Step 1: Create detailed specification
cat > cache_controller_spec.txt << 'EOF'
Design a SystemVerilog cache controller module with:
- Direct-mapped cache with configurable size
- Write-through policy with write buffer
- AXI4 interface to main memory
- Configurable cache line size (32, 64, 128 bytes)
- Hit/miss statistics counters
- Proper FSM for cache operations
EOF

# Step 2: Generate RTL modules
./utils/jedai_completion.py --file cache_controller_spec.txt --save-modules --output-dir ./cache_rtl

# Step 3: Review and refine specific modules
./utils/jedai_completion.py --query "Optimize this cache FSM for timing closure: [paste generated FSM code]"
```

## 🛠️ Practical Use Cases

### 1. Model Comparison
Compare how different models handle the same query:
```bash
# Create comparison script
#!/bin/bash
QUERY="Explain the benefits of microservices architecture"

echo "=== Claude Opus 4 ==="
./utils/jedai_completion.py --model claude-opus-4 --query "$QUERY"

echo -e "\n=== Gemini 2.5 Pro ==="
./utils/jedai_completion.py --model gemini-2-5-pro --query "$QUERY"
```

### 2. Quick Technical Help
Get immediate answers to technical questions:
```bash
# Python help
./utils/jedai_completion.py --query "Show me how to use Python asyncio for concurrent file operations"

# System administration
./utils/jedai_completion.py --query "How do I monitor disk usage in Linux and set up alerts?"

# Design questions
./utils/jedai_completion.py --query "What are the key considerations for low-power ASIC design?"
```

### 3. Code Generation and Review
```bash
# Generate code
./utils/jedai_completion.py --query "Write a Python class for managing database connections with connection pooling"

# Code review
./utils/jedai_completion.py --query "Review this SQL query for performance issues: SELECT * FROM users WHERE created_date > '2023-01-01'"
```

### 4. Learning and Education
```bash
# Learn new concepts
./utils/jedai_completion.py --query "Explain blockchain technology in simple terms with examples"

# Get step-by-step guides
./utils/jedai_completion.py --query "Provide a step-by-step guide to set up a CI/CD pipeline with Jenkins"
```

## 🚨 Troubleshooting

### Common Issues and Solutions

**1. Authentication Failed**
```bash
❌ Login failed: 401
```
**Solution:** 
- Check your LDAP credentials
- Ensure you have access to the JEDAI system
- Try with alternative server URL

**2. Model Not Found**
```bash
❌ Unknown model: claude-opus-5
```
**Solution:**
- Run `./utils/jedai_completion.py --list` to see available models
- Use exact model key from the list

**3. Connection Issues**
```bash
❌ Request failed: 503
```
**Solution:**
- Use `--test-urls` to check all available servers
- Script now automatically tries fallback URLs
- Check JEDAI server status
- Verify network connectivity

**4. File Input Issues**
```bash
❌ Error: File 'spec.txt' not found
```
**Solution:**
- Verify file path is correct
- Ensure file has read permissions
- Check file is not empty

**5. Module Extraction Issues**
```bash
❌ No SystemVerilog modules found in the response
```
**Solution:**
- Ensure your prompt requests SystemVerilog code generation
- Check that AI response contains proper `module`/`endmodule` syntax
- Try different AI models (claude-opus-4 works best for RTL generation)

**4. Permission Denied**
```bash
./utils/jedai_completion.py: Permission denied
```
**Solution:**
```bash
chmod +x utils/jedai_completion.py
```

### Testing Server Connectivity
```bash
# Test server health
curl -f http://ssgdpc-jedai.cadence.com:5000/api/health

# Test alternative server
curl -f http://sjf-dsgdspr-084.cadence.com:5668/api/health
```

## 💡 Tips and Best Practices

### 1. Efficient Model Selection
- **Claude Opus 4**: Use for complex reasoning, analysis, and detailed explanations
- **Claude Sonnet 4**: Balanced choice for most tasks
- **Gemini 2.5 Pro**: Good for creative tasks and diverse perspectives  
- **Gemini 2.5 Flash**: Fast responses for simple questions

### 2. Query Optimization
```bash
# Be specific for better results
./utils/jedai_completion.py --query "Write a Python function to validate email addresses using regex with error handling"

# Instead of generic queries
./utils/jedai_completion.py --query "Help with Python"
```

### 3. Server Selection
- **DPC Environment**: Uses default server automatically (no --url needed)
- **Non-DPC Environment**: Always specify `--url http://sjf-dsgdspr-084.cadence.com:5668`
- Test connectivity before long sessions

### 4. Integration with Scripts
```bash
# Use in automation scripts
RESPONSE=$(./utils/jedai_completion.py --query "Summarize this error log" 2>/dev/null | tail -n +4)
echo "AI Analysis: $RESPONSE"
```

## 🔗 Related Documentation

- **🆕 Technical Implementation Details**: See `README_jedai_enhancements.md` for complete feature documentation  
- **JEDAI User Guide**: Access through your corporate documentation portal
- **AAI Libraries**: https://pages.github.cadence.com/AAI/aai_lib/aai_user_manual.html
- **Vector Database Creation**: See parent repository's README.md for document upload workflows

## 📝 Quick Reference Card

```bash
# Essential commands to remember:
./utils/jedai_completion.py --list                              # Show models
./utils/jedai_completion.py --test-urls                         # Test connectivity
./utils/jedai_completion.py                                     # Quick test
./utils/jedai_completion.py --model claude-opus-4               # Specific model
./utils/jedai_completion.py --file spec.txt --save-modules      # 🆕 RTL generation
./utils/jedai_completion.py --url http://sjf-dsgdspr-084.cadence.com:5668  # Alt server

# Most useful models:
claude-opus-4      # Best reasoning & RTL generation
claude-sonnet-4    # Balanced & code optimization  
gemini-2-5-flash   # Fastest responses
gemini-2-5-pro     # Good for documentation

# 🆕 RTL Design Workflow:
1. Create specification file: design_spec.txt
2. Generate modules: ./utils/jedai_completion.py --file design_spec.txt --save-modules
3. Organize output: --output-dir ./rtl_modules
4. Review & optimize: Use --query for specific improvements
```

---

**Ready to get started?** Try running `./utils/jedai_completion.py --list` to see all available models, then test with your first query!

---

## Confluence Scraper

A Python utility to scrape Confluence pages and download all attachments with a single command.

### Features

- ✓ Authenticate using Personal Access Token
- ✓ Extract page content and metadata
- ✓ Download all page attachments
- ✓ Automatically create zip archive of attachments
- ✓ Save attachment list and page metadata as JSON

### Usage

```bash
python utils/confluence_scraper.py "<confluence_url>" "<email>" "<token>"
```

**Arguments:**
1. **confluence_url**: Full Confluence page URL (must include `spaceKey` and `title` parameters)
2. **email**: Your Confluence email address
3. **token**: Your Personal Access Token from Confluence

### Example

```bash
python utils/confluence_scraper.py \
  "https://wiki.cadence.com/confluence/pages/viewpage.action?spaceKey=DDR&title=DDR+Controller+Specifications" \
  "user@cadence.com" \
  "your_token_here"
```

### Output Structure

After successful execution, the script creates:

```
📁 Project Directory
├── 📄 page_content.json              # Full page metadata and HTML content
├── 📄 attachments_list.json          # List of all attachments with URLs
├── 📦 attachments.zip                # Zip archive of all attachments
└── 📁 attachments/                   # Directory with all downloaded files
    ├── Document1.docx
    ├── Document2.docx
    └── ... (all attachment files)
```

### Example Execution

```
================================================================================
Confluence Page Scraper
================================================================================

Space Key: DDR
Page Title: DDR Controller Specifications
Authentication successful!
Logged in as: Raghav Vasappanavara

Found page: DDR Controller Specifications
Page ID: 262586091
Type: page

Found 50 attachments
  - cdns_chi_implementation_specification_3.1.3.docx
  - AXI5_RSECC_Poison_Pattern_propogation design spec.docx
  - Design Spec Template v1.3.docx
  ... (47 more files)

Downloading attachments...
Downloaded: cdns_chi_implementation_specification_3.1.3.docx
... (downloading all 50 files)

Created zip file: attachments.zip

================================================================================
Scraping completed successfully!
- Page content saved to: page_content.json
- Attachments saved to: attachments/
- Attachment list saved to: attachments_list.json
- Zip file created: attachments.zip
================================================================================
```

### Getting Your Personal Access Token

1. Go to: https://wiki.cadence.com/confluence/plugins/personalaccesstokens/usertokens.action
2. Click "Create Token"
3. Give it a name and click "Generate"
4. Copy the token immediately (you won't be able to see it again)

### Notes

- Uses Bearer token authentication
- All attachments are downloaded in their original format
- Large files may take time depending on your connection
- Automatically creates `attachments/` directory if needed
- Script will error if authentication fails, page not found, or invalid URL format

---

## Contributing

This is an internal Cadence repository for SSG AI automation utilities.

### Adding New Tools

To add a new utility:

1. Create your script in the `utils/` directory
2. Add a new section in this README (follow the existing format)
3. Include Features, Usage, Example, and Notes sections
4. Update the Table of Contents
5. Submit your changes via pull request

### Guidelines

- Keep scripts focused on single, well-defined tasks
- Include comprehensive error handling
- Document all required dependencies
- Provide clear usage examples
- Add output files to `.gitignore`

---

## License

Internal Cadence use only.