################################################################################
# Script Name: IMP-16-0-0-02.py
#
# Purpose:
#   Confirm PHY has the IPTAG for Hard PHY delivery and Slices have the IPTAG for FIRM PHY delivery. (Can skip slice level IPTAG for Hard PHY delivery)
#
# Logic:
#   - Parse input file: cdn_hs_phy_top.csv (IP_CHECKER tool CSV output)
#   - Validate CSV header structure to confirm file format
#   - Extract PHY-level IPTAG entry (*phy line) with vendor, product, version, instance_tag
#   - Extract Block-level IPTAG entry (*block line) with vendor, product, version, instance_tag
#   - Classify delivery type based on IPTAG presence:
#     * Hard PHY delivery: PHY IPTAG exists AND Block IPTAG does NOT exist
#     * FIRM PHY delivery: Block IPTAG exists AND PHY IPTAG does NOT exist
#     * ERROR: Both PHY IPTAG and Block IPTAG do NOT exist
#   - Generate INFO01 for found IPTAGs with delivery type classification
#   - Generate ERROR01 for missing IPTAG violations or invalid configurations
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2025-12-26 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-18
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Dict, Tuple, Optional, Any


# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # Go up to Check_modules/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, create_check_result

# MANDATORY: Import template mixins (checker_templates v1.1.0)
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_16_0_0_02(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-16-0-0-02: Confirm PHY has the IPTAG for Hard PHY delivery and Slices have the IPTAG for FIRM PHY delivery. (Can skip slice level IPTAG for Hard PHY delivery)
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers>0 → Boolean Check with Waiver Logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # DESCRIPTION & REASON CONSTANTS - COPY FROM README Output Descriptions!
    # =========================================================================
    # Type 1/4: Boolean checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE1_4 = "IPTAG verification completed with valid delivery type configuration"
    MISSING_DESC_TYPE1_4 = "IPTAG verification failed - missing required IPTAG or invalid delivery type configuration"
    FOUND_REASON_TYPE1_4 = "IPTAG found and delivery type verified"
    MISSING_REASON_TYPE1_4 = "Required IPTAG not found or invalid delivery type configuration"
    
    # Type 2/3: Pattern checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE2_3 = "IPTAG entries matched expected delivery type requirements"
    MISSING_DESC_TYPE2_3 = "IPTAG entries do not satisfy delivery type requirements"
    FOUND_REASON_TYPE2_3 = "IPTAG requirement satisfied for delivery type"
    MISSING_REASON_TYPE2_3 = "IPTAG requirement not satisfied for delivery type"
    
    # All Types (waiver description) - COPY EXACT VALUES FROM README!
    WAIVED_DESC = "IPTAG violations waived per configuration"
    
    # Waiver parameters (Type 3/4 ONLY) - COPY EXACT VALUES FROM README!
    WAIVED_BASE_REASON = "IPTAG violation waived"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="16.0_IPTAG_CHECK",
            item_id="IMP-16-0-0-02",
            item_desc="Confirm PHY has the IPTAG for Hard PHY delivery and Slices have the IPTAG for FIRM PHY delivery. (Can skip slice level IPTAG for Hard PHY delivery)"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._phy_iptag: Optional[Dict[str, Any]] = None
        self._block_iptag: Optional[Dict[str, Any]] = None
        self._delivery_type: Optional[str] = None
    
    # =========================================================================
    # Main Check Execution
    # =========================================================================
    
    def execute_check(self) -> CheckResult:
        """
        Execute check with automatic type detection and delegation.
        
        Returns:
            CheckResult based on detected checker type
        """
        try:
            if self.root is None:
                raise RuntimeError("Checker not initialized. Call init_checker() first.")
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1()
            elif checker_type == 2:
                return self._execute_type2()
            elif checker_type == 3:
                return self._execute_type3()
            else:  # checker_type == 4
                return self._execute_type4()
        except ConfigurationError as e:
            return e.check_result
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        解析输入文件，从 Instance 列查找 phy/block 行，从 Product 列提取对应的 IPTAG。
        
        返回:
            Dict 包含:
            - 'items': List[Dict] - 所有 IPTAG 条目
            - 'phy_iptag': Dict - PHY IPTAG 条目（如果找到）
            - 'block_iptag': Dict - Block IPTAG 条目（如果找到）
            - 'delivery_type': str - 分类的交付类型
            - 'metadata': Dict - 文件元数据
            - 'errors': List - 解析错误
        """
        import csv
        
        # 1. 验证输入文件
        valid_files, missing_files = self.validate_input_files()
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # 2. 解析 CSV 文件
        items = []
        phy_iptag = None
        block_iptag = None
        errors = []
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f)
                    header = None
                    
                    for line_num, row in enumerate(reader, 1):
                        # 跳过空行
                        if not row or all(not cell.strip() for cell in row):
                            continue
                        
                        # 查找表头
                        if header is None and any('Instance' in cell for cell in row):
                            header = [cell.strip() for cell in row]
                            continue
                        
                        if header is None:
                            continue
                        
                        # 确保有足够的列（至少7列: GDS, Vendor, Product, Version, Metric, Instance, Instance_tag）
                        if len(row) < 7:
                            continue
                        
                        # 提取字段
                        instance = row[5].strip().lower()  # Instance列，转小写用于匹配
                        product = row[2].strip()  # Product列，这里是IPTAG
                        
                        # 构建条目
                        entry = {
                            'name': row[5].strip(),
                            'gds': row[0].strip(),
                            'vendor': row[1].strip(),
                            'product': product,
                            'version': row[3].strip(),
                            'instance': row[5].strip(),
                            'instance_tag': row[6].strip(),
                            'line_number': line_num,
                            'file_path': str(file_path)
                        }
                        items.append(entry)
                        
                        # 查找 PHY IPTAG (Instance 包含 'phy')
                        if phy_iptag is None and 'phy' in instance:
                            phy_iptag = {
                                'name': f"PHY IPTAG: {row[5].strip()}",
                                'gds': row[0].strip(),
                                'vendor': row[1].strip(),
                                'product': product,
                                'version': row[3].strip(),
                                'instance': row[5].strip(),
                                'instance_tag': row[6].strip(),
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                        
                        # 查找 Block IPTAG (Instance 包含 'block')
                        if block_iptag is None and 'block' in instance:
                            block_iptag = {
                                'name': f"Block IPTAG: {row[5].strip()}",
                                'gds': row[0].strip(),
                                'vendor': row[1].strip(),
                                'product': product,
                                'version': row[3].strip(),
                                'instance': row[5].strip(),
                                'instance_tag': row[6].strip(),
                                'line_number': line_num,
                                'file_path': str(file_path)
                            }
                    
                    if header is None:
                        errors.append(f"CSV header not found in {file_path}")
            
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. 分类交付类型
        delivery_type = self._classify_delivery_type(phy_iptag, block_iptag)
        
        # 4. 保存数据
        self._parsed_items = items
        self._phy_iptag = phy_iptag
        self._block_iptag = block_iptag
        self._delivery_type = delivery_type
        
        return {
            'items': items,
            'phy_iptag': phy_iptag,
            'block_iptag': block_iptag,
            'delivery_type': delivery_type,
            'metadata': {
                'total_items': len(items),
                'phy_iptag_found': phy_iptag is not None,
                'block_iptag_found': block_iptag is not None
            },
            'errors': errors
        }
    
    def _classify_delivery_type(self, phy_iptag: Optional[Dict], block_iptag: Optional[Dict]) -> str:
        """
        Classify delivery type based on IPTAG presence.
        
        Args:
            phy_iptag: PHY-level IPTAG entry (or None)
            block_iptag: Block-level IPTAG entry (or None)
        
        Returns:
            Delivery type: 'Hard PHY', 'FIRM PHY', or 'ERROR'
        """
        if phy_iptag and not block_iptag:
            return 'Hard PHY'
        elif block_iptag and not phy_iptag:
            return 'FIRM PHY'
        else:
            return 'ERROR'
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Custom boolean validation (file exists? config valid?).
        Does NOT use pattern_items for searching.
        
        Use OutputBuilderMixin.build_complete_output() for automatic formatting.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        phy_iptag = data.get('phy_iptag')
        block_iptag = data.get('block_iptag')
        delivery_type = data.get('delivery_type')
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            error_msg = '; '.join(errors)
            missing_items = {
                'parsing_error': {
                    'name': 'parsing_error',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'details': error_msg
                }
            }
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        
        # Check if valid delivery type configuration exists
        found_items = {}
        missing_items = {}
        
        if delivery_type == 'Hard PHY':
            # Hard PHY delivery: PHY IPTAG exists, Block IPTAG does NOT exist
            phy_product = phy_iptag.get('product', 'N/A')
            phy_instance = phy_iptag.get('instance', 'N/A')
            item_name = f"Hard PHY delivery - IPTAG: {phy_product} (Instance: {phy_instance})"
            found_items[item_name] = {
                'name': item_name,
                'line_number': phy_iptag.get('line_number', 0),
                'file_path': phy_iptag.get('file_path', 'N/A'),
                'vendor': phy_iptag.get('vendor', 'N/A'),
                'product': phy_product,
                'version': phy_iptag.get('version', 'N/A')
            }
        elif delivery_type == 'FIRM PHY':
            # FIRM PHY delivery: Block IPTAG exists, PHY IPTAG does NOT exist
            block_product = block_iptag.get('product', 'N/A')
            block_instance = block_iptag.get('instance', 'N/A')
            item_name = f"FIRM PHY delivery - IPTAG: {block_product} (Instance: {block_instance})"
            found_items[item_name] = {
                'name': item_name,
                'line_number': block_iptag.get('line_number', 0),
                'file_path': block_iptag.get('file_path', 'N/A'),
                'vendor': block_iptag.get('vendor', 'N/A'),
                'product': block_product,
                'version': block_iptag.get('version', 'N/A')
            }
        else:
            # ERROR: Both PHY IPTAG and Block IPTAG are missing
            if not phy_iptag:
                missing_items['PHY-level IPTAG'] = {
                    'name': 'ERROR: PHY-level IPTAG not found',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            if not block_iptag:
                missing_items['Block-level IPTAG'] = {
                    'name': 'ERROR: Block-level IPTAG not found',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files.
        found_items = patterns found; missing_items = patterns not found.
        PASS/FAIL depends on check purpose (violation check vs requirement check).
        
        Template auto-handles waiver=0 conversions.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        phy_iptag = data.get('phy_iptag')
        block_iptag = data.get('block_iptag')
        delivery_type = data.get('delivery_type')
        errors = data.get('errors', [])
        
        # Check for parsing errors
        if errors:
            error_msg = '; '.join(errors)
            missing_items = {
                'parsing_error': {
                    'name': 'parsing_error',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'details': error_msg
                }
            }
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3
            )
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check if delivery type matches expected patterns
        found_items = {}
        missing_items = {}
        
        for pattern in pattern_items:
            pattern_lower = pattern.lower()
            matched = False
            
            # Check if pattern matches delivery type
            if 'hard' in pattern_lower and delivery_type == 'Hard PHY':
                if phy_iptag:
                    found_items[phy_iptag['name']] = {
                        'name': phy_iptag['name'],
                        'line_number': phy_iptag.get('line_number', 0),
                        'file_path': phy_iptag.get('file_path', 'N/A'),
                        'vendor': phy_iptag.get('vendor', 'N/A'),
                        'product': phy_iptag.get('product', 'N/A'),
                        'version': phy_iptag.get('version', 'N/A')
                    }
                    matched = True
            elif 'firm' in pattern_lower and delivery_type == 'FIRM PHY':
                if block_iptag:
                    found_items[block_iptag['name']] = {
                        'name': block_iptag['name'],
                        'line_number': block_iptag.get('line_number', 0),
                        'file_path': block_iptag.get('file_path', 'N/A'),
                        'vendor': block_iptag.get('vendor', 'N/A'),
                        'product': block_iptag.get('product', 'N/A'),
                        'version': block_iptag.get('version', 'N/A')
                    }
                    matched = True
            
            if not matched:
                missing_items[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Same pattern search logic as Type 2, plus waiver classification.
        
        Uses WaiverHandlerMixin for waiver processing:
        - parse_waive_items(waive_items_raw): Parse waiver configuration
        - match_waiver_entry(item, waive_dict): Match item against waivers
        
        Uses OutputBuilderMixin for result construction:
        - build_complete_output(...): Assemble final CheckResult with auto-formatting
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        phy_iptag = parsed_data.get('phy_iptag')
        block_iptag = parsed_data.get('block_iptag')
        delivery_type = parsed_data.get('delivery_type')
        errors = parsed_data.get('errors', [])
        
        # Parse waiver configuration using template helper - CORRECT! Use waivers.get() directly
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check for parsing errors
        if errors:
            error_msg = '; '.join(errors)
            missing_items = {
                'parsing_error': {
                    'name': 'parsing_error',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'details': error_msg
                }
            }
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE2_3,
                missing_desc=self.MISSING_DESC_TYPE2_3,
                found_reason=self.FOUND_REASON_TYPE2_3,
                missing_reason=self.MISSING_REASON_TYPE2_3
            )
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Find violations (same logic as Type 2)
        found_items = {}
        violations = {}
        
        for pattern in pattern_items:
            pattern_lower = pattern.lower()
            matched = False
            
            # Check if pattern matches delivery type
            if 'hard' in pattern_lower and delivery_type == 'Hard PHY':
                if phy_iptag:
                    found_items[phy_iptag['name']] = {
                        'name': phy_iptag['name'],
                        'line_number': phy_iptag.get('line_number', 0),
                        'file_path': phy_iptag.get('file_path', 'N/A'),
                        'vendor': phy_iptag.get('vendor', 'N/A'),
                        'product': phy_iptag.get('product', 'N/A'),
                        'version': phy_iptag.get('version', 'N/A')
                    }
                    matched = True
            elif 'firm' in pattern_lower and delivery_type == 'FIRM PHY':
                if block_iptag:
                    found_items[block_iptag['name']] = {
                        'name': block_iptag['name'],
                        'line_number': block_iptag.get('line_number', 0),
                        'file_path': block_iptag.get('file_path', 'N/A'),
                        'vendor': block_iptag.get('vendor', 'N/A'),
                        'product': block_iptag.get('product', 'N/A'),
                        'version': block_iptag.get('version', 'N/A')
                    }
                    matched = True
            
            if not matched:
                violations[pattern] = {
                    'name': pattern,
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        unwaived_items = {}
        
        for name, violation in violations.items():
            if self.match_waiver_entry(name, waive_dict):
                waived_items[name] = violation
            else:
                unwaived_items[name] = violation
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper for automatic output formatting
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        
        Use OutputBuilderMixin.build_complete_output() with has_waiver_value=True.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        phy_iptag = data.get('phy_iptag')
        block_iptag = data.get('block_iptag')
        delivery_type = data.get('delivery_type')
        errors = data.get('errors', [])
        
        # Parse waiver configuration - CORRECT! Use waivers.get() directly
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check for parsing errors
        if errors:
            error_msg = '; '.join(errors)
            missing_items = {
                'parsing_error': {
                    'name': 'parsing_error',
                    'line_number': 0,
                    'file_path': 'N/A',
                    'details': error_msg
                }
            }
            return self.build_complete_output(
                found_items={},
                missing_items=missing_items,
                found_desc=self.FOUND_DESC_TYPE1_4,
                missing_desc=self.MISSING_DESC_TYPE1_4,
                found_reason=self.FOUND_REASON_TYPE1_4,
                missing_reason=self.MISSING_REASON_TYPE1_4
            )
        
        # Check if valid delivery type configuration exists
        found_items = {}
        violations = {}
        
        if delivery_type == 'Hard PHY':
            # Hard PHY delivery: PHY IPTAG exists, Block IPTAG does NOT exist
            phy_product = phy_iptag.get('product', 'N/A')
            phy_instance = phy_iptag.get('instance', 'N/A')
            item_name = f"Hard PHY delivery - IPTAG: {phy_product} (Instance: {phy_instance})"
            found_items[item_name] = {
                'name': item_name,
                'line_number': phy_iptag.get('line_number', 0),
                'file_path': phy_iptag.get('file_path', 'N/A'),
                'vendor': phy_iptag.get('vendor', 'N/A'),
                'product': phy_product,
                'version': phy_iptag.get('version', 'N/A')
            }
        elif delivery_type == 'FIRM PHY':
            # FIRM PHY delivery: Block IPTAG exists, PHY IPTAG does NOT exist
            block_product = block_iptag.get('product', 'N/A')
            block_instance = block_iptag.get('instance', 'N/A')
            item_name = f"FIRM PHY delivery - IPTAG: {block_product} (Instance: {block_instance})"
            found_items[item_name] = {
                'name': item_name,
                'line_number': block_iptag.get('line_number', 0),
                'file_path': block_iptag.get('file_path', 'N/A'),
                'vendor': block_iptag.get('vendor', 'N/A'),
                'product': block_product,
                'version': block_iptag.get('version', 'N/A')
            }
        else:
            # ERROR: Both PHY IPTAG and Block IPTAG are missing
            if not phy_iptag:
                violations['PHY-level IPTAG'] = {
                    'name': 'ERROR: PHY-level IPTAG not found',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
            if not block_iptag:
                violations['Block-level IPTAG'] = {
                    'name': 'ERROR: Block-level IPTAG not found',
                    'line_number': 0,
                    'file_path': 'N/A'
                }
        
        # Separate waived/unwaived using template helper
        waived_items = {}
        unwaived_items = {}
        
        for name, violation in violations.items():
            if self.match_waiver_entry(name, waive_dict):
                waived_items[name] = violation
            else:
                unwaived_items[name] = violation
        
        # Find unused waivers
        used_names = set(waived_items.keys())
        unused_waivers = [name for name in waive_dict.keys() if name not in used_names]
        
        # Use template helper (auto-handles waiver=0)
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_16_0_0_02()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())