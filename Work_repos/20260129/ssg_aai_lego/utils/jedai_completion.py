#!/usr/bin/env python3
"""
JEDAI Completion Test Script

Simple script to test AI models through JEDAI API.
Auto-detects DPC vs non-DPC environment and configures accordingly.
Uses LDAP authentication and supports multiple models.

Usage:
    ./jedai_completion.py --list                    # Show available models  
    ./jedai_completion.py                           # Test default model
    ./jedai_completion.py --model claude-opus-4    # Test specific model
    ./jedai_completion.py --query "Your question"  # Custom query
    ./jedai_completion.py --file prompt.txt        # Read query from file
    ./jedai_completion.py --file prompt.txt --save-modules  # Save generated modules to files
"""

import requests
import getpass
import argparse
import json
import sys
import os
import socket
import re

def detect_environment():
    """Detect if running in DPC or non-DPC environment"""
    hostname = socket.gethostname()
    
    # Extended DPC patterns based on common Cadence hostname patterns
    dpc_patterns = [
        'dpc', 'nfdpc', 'ssgdpc', 'atl', 'cadence.com',
        'sjc', 'aus', 'rtp', 'bng', 'kor', 'jpn',  # Geographic locations
        'ssg', 'nf', 'ip', 'da',                    # Business units
        'rmpipg'  # Adding your specific hostname pattern
    ]
    
    # Check hostname patterns
    is_dpc = any(pattern in hostname.lower() for pattern in dpc_patterns)
    
    # Additional environment variable checks
    if not is_dpc:
        # Check common environment variables that might indicate DPC
        env_indicators = [
            os.environ.get('CADENCE_HOME'),
            os.environ.get('CDS_HOME'),
            os.environ.get('CADENCE_ROOT'),
            os.environ.get('CDS_ROOT')
        ]
        is_dpc = any(indicator for indicator in env_indicators)
    
    return is_dpc

def get_jedai_url():
    """Get appropriate JEDAI URL based on environment"""
    is_dpc = detect_environment()
    
    # DPC environment URLs
    dpc_urls = [
        "http://ssgdpc-jedai.cadence.com:5000",
        "http://jedai.cadence.com:5000",
        "http://ssgdpc-jedai.cadence.com:8080"
    ]
    
    # Non-DPC environment URLs
    non_dpc_urls = [
        "http://sjf-dsgdspr-084.cadence.com:5668",
        "http://sjc-dsgdspr-084.cadence.com:5668",
        "http://rmpipg302.cadence.com:5668"  # Based on your hostname
    ]
    
    if is_dpc:
        return dpc_urls[0]  # Primary DPC URL
    else:
        return non_dpc_urls[0]  # Primary non-DPC URL

def get_all_jedai_urls():
    """Get all possible JEDAI URLs for fallback"""
    return [
        "http://ssgdpc-jedai.cadence.com:5000",
        "http://jedai.cadence.com:5000", 
        "http://sjf-dsgdspr-084.cadence.com:5668",
        "http://sjc-dsgdspr-084.cadence.com:5668",
        "http://rmpipg302.cadence.com:5668"
    ]

def print_environment_info():
    """Print environment detection information"""
    is_dpc = detect_environment()
    hostname = socket.gethostname()
    jedai_url = get_jedai_url()
    
    print(f"🌐 Environment Detection:")
    print(f"   Hostname: {hostname}")
    print(f"   Environment: {'DPC' if is_dpc else 'Non-DPC'}")
    print(f"   Primary JEDAI URL: {jedai_url}")
    
    # Show environment variables for debugging
    cadence_vars = []
    for var in ['CADENCE_HOME', 'CDS_HOME', 'CADENCE_ROOT', 'CDS_ROOT']:
        value = os.environ.get(var)
        if value:
            cadence_vars.append(f"{var}={value}")
    
    if cadence_vars:
        print(f"   Cadence Env Vars: {', '.join(cadence_vars)}")
    else:
        print(f"   Cadence Env Vars: None found")
        
    print("-" * 50)

# Available models
MODELS = {
    "claude-opus-4": {
        "name": "Claude Opus 4",
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-opus-4-1"
    },
    "claude-sonnet-4": {
        "name": "Claude Sonnet 4", 
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-sonnet-4"
    },
    "gemini-2-5-pro": {
        "name": "Gemini 2.5 Pro",
        "family": "GEMINI",
        "location": "us-central1", 
        "deployment": "gemini-2.5-pro"
    },
    "gemini-2-5-flash": {
        "name": "Gemini 2.5 Flash",
        "family": "GEMINI",
        "location": "us-central1",
        "deployment": "gemini-2.5-flash"
    }
}

def test_jedai_connection(jedai_url, timeout=5):
    """Test if JEDAI URL is accessible"""
    try:
        response = requests.get(f"{jedai_url}/health", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def authenticate(jedai_url):
    """Login to JEDAI and get access token with fallback URLs"""
    username = getpass.getuser()
    password = getpass.getpass("Password: ")
    
    # List of URLs to try
    urls_to_try = [jedai_url] + [url for url in get_all_jedai_urls() if url != jedai_url]
    
    for i, url in enumerate(urls_to_try):
        try:
            if i > 0:
                print(f"🔄 Trying fallback URL: {url}")
            
            response = requests.post(
                f"{url}/api/v1/security/login",
                headers={"Content-Type": "application/json"},
                json={"username": username, "password": password, "provider": "LDAP"},
                timeout=10
            )
            
            if response.status_code == 200:
                if i > 0:
                    print(f"✅ Successfully connected to: {url}")
                return response.json()["access_token"], url
            else:
                print(f"❌ Login failed for {url}: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection failed for {url}: {str(e)}")
            continue
    
    print(f"❌ All JEDAI URLs failed. Tried: {', '.join(urls_to_try)}")
    sys.exit(1)

def test_model(token, jedai_url, query, model_key):
    """Send query to AI model and return response"""
    if model_key not in MODELS:
        return f"❌ Unknown model: {model_key}"
    
    model = MODELS[model_key]
    
    # Build request
    body = {
        "messages": [{"role": "user", "content": query}],
        "model": model["family"],
        "location": model["location"],
        "project": "gcp-cdns-llm-test", 
        "deployment": model["deployment"],
        "max_tokens": 8000,
        "temperature": 1,
        "top_p": 1
    }
    
    # Send request
    response = requests.post(
        f"{jedai_url}/api/copilot/v1/llm/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        json=body
    )
    
    if response.status_code != 200:
        return f"❌ Request failed: {response.status_code}"
    
    # Parse response
    result = response.json()
    
    # Handle different response formats
    if "candidates" in result:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    elif "choices" in result:
        return result["choices"][0]["message"]["content"]
    elif "content" in result:
        return result["content"][0]["text"] 
    else:
        return f"❌ Unknown response format: {json.dumps(result, indent=2)}"

def read_file_content(file_path):
    """Read content from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            print(f"❌ Error: File '{file_path}' is empty")
            sys.exit(1)
        return content
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found")
        sys.exit(1)
    except PermissionError:
        print(f"❌ Error: Permission denied reading '{file_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file '{file_path}': {str(e)}")
        sys.exit(1)

def extract_systemverilog_modules(text):
    """Extract SystemVerilog modules from generated text"""
    modules = []
    
    # Pattern to match SystemVerilog module declarations
    module_pattern = r'module\s+(\w+)\s*(?:\#.*?)?\s*\((.*?)\);(.*?)endmodule'
    
    # Find all module matches (with DOTALL flag to match across newlines)
    matches = re.finditer(module_pattern, text, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        module_name = match.group(1)
        full_module = match.group(0)
        modules.append({
            'name': module_name,
            'code': full_module
        })
    
    return modules

def save_modules_to_files(modules, output_dir="."):
    """Save each module to a separate .sv file"""
    saved_files = []
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for module in modules:
        filename = f"{module['name']}.sv"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(module['code'])
            saved_files.append(filepath)
            print(f"✅ Saved module '{module['name']}' to {filepath}")
        except Exception as e:
            print(f"❌ Error saving module '{module['name']}' to {filepath}: {str(e)}")
    
    return saved_files

def list_models():
    """Show all available models"""
    print("Available Models:")
    print("-" * 40)
    for key, model in MODELS.items():
        print(f"{key:<20} {model['name']}")
    print("-" * 40)

def main():
    # Check Python version for non-DPC environments
    if not detect_environment() and sys.version_info < (3, 6):
        print("❌ Error: Python 3.6 or higher required for non-DPC environments")
        print("Please install Python 3 or use 'python3' command")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="JEDAI AI Model Test with Auto Environment Detection")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--test-urls", action="store_true", help="Test connectivity to all JEDAI URLs")
    parser.add_argument("--model", default="claude-opus-4", help="Model to test")
    parser.add_argument("--query", help="Query to send")
    parser.add_argument("--file", help="Read query from text file")
    parser.add_argument("--save-modules", action="store_true", help="Auto-save generated SystemVerilog modules to separate files")
    parser.add_argument("--output-dir", default=".", help="Directory to save generated module files (default: current directory)")
    parser.add_argument("--url", help="Override auto-detected JEDAI URL (optional)")
    
    args = parser.parse_args()
    
    if args.list:
        list_models()
        return
        
    if args.test_urls:
        print("🔗 Testing JEDAI URL Connectivity:")
        print("-" * 50)
        for url in get_all_jedai_urls():
            print(f"Testing {url}... ", end="", flush=True)
            if test_jedai_connection(url):
                print("✅ Connected")
            else:
                print("❌ Failed")
        print("-" * 50)
        return
    
    # Validate input arguments
    if args.query and args.file:
        print("❌ Error: Cannot specify both --query and --file. Please use only one.")
        sys.exit(1)
    
    # Determine the query source
    if args.file:
        query = read_file_content(args.file)
        query_source = f"file: {args.file}"
    elif args.query:
        query = args.query
        query_source = f"query: {args.query}"
    else:
        # Default query if neither is specified
        query = "What is the capital of France?"
        query_source = f"default query: {query}"
    
    # Auto-detect environment and get URL
    jedai_url = args.url if args.url else get_jedai_url()
    
    print_environment_info()
    print(f"Testing {args.model} with {query_source}")
    print("-" * 50)
    
    # Login (with potential URL fallback)
    token, working_url = authenticate(jedai_url)
    print("✅ Logged in")
    
    # Use the working URL for the model test
    result = test_model(token, working_url, query, args.model)
    print("\nResponse:")
    print(result)
    
    # Auto-save modules if requested
    if args.save_modules:
        print("\n" + "=" * 50)
        print("🔍 Extracting and saving SystemVerilog modules...")
        
        modules = extract_systemverilog_modules(result)
        
        if modules:
            print(f"Found {len(modules)} module(s):")
            for module in modules:
                print(f"  - {module['name']}")
            
            saved_files = save_modules_to_files(modules, args.output_dir)
            
            if saved_files:
                print(f"\n✅ Successfully saved {len(saved_files)} module file(s)")
            else:
                print("\n❌ No modules were saved")
        else:
            print("❌ No SystemVerilog modules found in the response")
        
        print("=" * 50)

if __name__ == "__main__":
    main()