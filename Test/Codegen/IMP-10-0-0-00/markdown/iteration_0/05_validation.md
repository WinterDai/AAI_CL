# 🔬 Validation Results

**Item:** IMP-10-0-0-00  
**Iteration:** 0  
**Timestamp:** 2026-01-28 14:06:36

---

## ✅ Summary: 12/12 Gates Passed

## 📋 Gate Results

| Gate | Status | Description |
|------|--------|-------------|
| `gate1_signature` | ✅ PASS | Required function signatures present |
| `gate1_schema` | ✅ PASS | Output schema compliance |
| `gate1_type_safety` | ✅ PASS | Value field is string type |
| `gate2_none_safety` | ✅ PASS | Handles parsed_fields=None |
| `gate2_alternatives` | ✅ PASS | Empty alternatives `|a||` works |
| `gate2_bad_regex` | ✅ PASS | Catches invalid regex gracefully |
| `gate2_literal_alt` | ✅ PASS | Literal alternatives before regex |
| `gate2_precedence` | ✅ PASS | Wildcard uses fnmatch |
| `gate2_default_strategy` | ✅ PASS | Contains vs exact matching |
| `gate2_invalid_mode` | ✅ PASS | Invalid regex_mode defaults to search |
| `gate1_evidence` | ✅ PASS | Evidence passthrough works |
| `consistency` | ✅ PASS | YAML and code are consistent |
