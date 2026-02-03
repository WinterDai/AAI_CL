# SheetJS Library - Offline Support

## 📦 Library Information

- **Library**: SheetJS (xlsx.js)
- **Version**: 0.20.1
- **Location**: `Check_modules/common/libs/xlsx.full.min.js`
- **Size**: ~922 KB (944,491 bytes)
- **Purpose**: Enable Excel/CSV file preview in HTML dashboard without internet connection

## 🔧 Setup Instructions

### On Windows (Download Library)

1. **Download the library**:

   ```powershell
   cd Work
   .\download_sheetjs.ps1
   ```

   Or manually:

   ```powershell
   New-Item -ItemType Directory -Path libs -Force
   Invoke-WebRequest -Uri "https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js" -OutFile "libs\xlsx.full.min.js"
   ```
2. **Verify the download**:

   ```powershell
   Get-Item libs\xlsx.full.min.js
   ```

   Expected output:

   ```
   Name             Length
   ----             ------
   xlsx.full.min.js 944491
   ```

### On Linux (Upload Library)

1. **Upload the libs folder to Linux**:

   ```bash
   # From Windows machine
   scp -r libs username@linux-host:/path/to/CHECKLIST/Work/

   # Or use WinSCP, FileZilla, or other file transfer tools
   ```
2. **Verify on Linux**:

   ```bash
   cd /path/to/CHECKLIST/Work
   ls -lh libs/
   # Should see: xlsx.full.min.js (~922K)
   ```
3. **Generate dashboard**:

   ```bash
   cd /path/to/CHECKLIST/Work
   ./run.csh
   ```

   You should see:

   ```
   [INFO] Using local SheetJS library: /path/to/Work/libs/xlsx.full.min.js
   ```

## 🎯 How It Works

The Python script (`visualize_signoff.py`) automatically detects the local library:

1. **Checks for local file**: `Work/libs/xlsx.full.min.js`
2. **If found**: Embeds the entire library in the HTML (self-contained)
3. **If not found**: Uses CDN (requires internet)

### Code Logic

```python
# Library is located in same directory as visualize_signoff.py
script_dir = Path(__file__).parent
local_sheetjs_path = script_dir / 'libs' / 'xlsx.full.min.js'

if local_sheetjs_path.exists():
    # Use local library (offline mode)
    with open(local_sheetjs_path, 'r') as f:
        sheetjs_content = f.read()
    html += f"<script>{sheetjs_content}</script>"
else:
    # Use CDN (online mode)
    html += "<script src='https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js'></script>"
```

## ✅ Benefits

### With Local Library

- ✅ Works in **offline/restricted network** environments
- ✅ **Faster loading** (no CDN latency)
- ✅ **Self-contained** HTML (single file with everything embedded)
- ✅ **Consistent behavior** (no dependency on external services)

### With CDN (Fallback)

- ✅ **Smaller HTML file** size
- ✅ **No setup required** (automatic)
- ❌ Requires internet connection

## 📁 Directory Structure

```
CHECKLIST/
├── Check_modules/
│   └── common/
│       ├── libs/                      ← Library directory
│       │   ├── xlsx.full.min.js      ← SheetJS library (922 KB)
│       │   └── README.md             ← This file
│       └── visualize_signoff.py      ← Auto-detects local lib
├── Work/
│   ├── download_sheetjs.ps1          ← Download script
│   ├── Reports/
│   │   └── *.html                    ← Generated dashboards (use local lib)
│   ├── Results/
│   └── run.csh
```

## 🧪 Testing

### Test 1: Verify Local Library Works

```bash
cd Work
python3 ../Check_modules/common/visualize_signoff.py

# Expected output:
# [INFO] Using local SheetJS library: .../Check_modules/common/libs/xlsx.full.min.js
```

### Test 2: Verify Fallback to CDN

```bash
# Temporarily rename libs folder
cd Check_modules/common
mv libs libs_backup

cd ../../Work
python3 ../Check_modules/common/visualize_signoff.py

# Expected output:
# [INFO] Local SheetJS library not found at .../Check_modules/common/libs/xlsx.full.min.js, using CDN

# Restore libs folder
cd ../Check_modules/common
mv libs_backup libs
```

### Test 3: Verify Preview Functionality

1. Open generated HTML in browser
2. Go to "Results" tab
3. Click "Preview" button for an Excel file
4. Should see Excel content displayed (not error message)

## 🐛 Troubleshooting

### Issue: "Excel preview library is not loaded"

**Cause**: SheetJS library not loaded (neither local nor CDN)

**Solution**:

1. Check if `Check_modules/common/libs/xlsx.full.min.js` exists and is not empty
2. Check file permissions: `chmod 644 Check_modules/common/libs/xlsx.full.min.js`
3. Regenerate dashboard: `./run.csh`
4. Check console logs for SheetJS errors

### Issue: File size too large

**Cause**: Embedded SheetJS library increases HTML size by ~920 KB

**Solution**:

- This is expected behavior for offline support
- Each HTML file will be ~1-2 MB larger
- To use CDN instead: remove or rename `Check_modules/common/libs` folder

### Issue: Cannot download library (Windows)

**Cause**: Firewall/proxy blocks CDN access

**Solution**:

1. Download manually from browser: https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js
2. Save to `Check_modules\common\libs\xlsx.full.min.js`
3. Or ask IT to whitelist `cdn.sheetjs.com`

## 📝 Notes

1. **One-time setup**: Once uploaded to Linux, the library stays there
2. **Location change**: Library moved to `Check_modules/common/libs/` for easier management
3. **Version pinned**: Using version 0.20.1 (stable, tested)
4. **License**: SheetJS Community Edition (Apache 2.0)

## 🔗 References

- **SheetJS CDN**: https://cdn.sheetjs.com/
- **Documentation**: https://docs.sheetjs.com/
- **GitHub**: https://github.com/SheetJS/sheetjs
