# ItemSpec: TODO: Add check item ID (e.g., IMP-10-0-0-00)

## 1. Check Objective

**Description**: TODO: Copy description from item_data.yaml (e.g., "Confirm the netlist/spef version is correct")

**语义理解**：
TODO: 用1-2句中文解释description的业务含义 (e.g., 验证STA（静态时序分析）流程中使用的netlist和SPEF文件的版本信息是否正确)

**检查对象**：
- **TODO: Add object 1 name** (e.g., Netlist)：TODO: 用一句话解释该对象在EDA领域的含义 (e.g., 门级网表文件，包含设计的逻辑结构)
- **TODO: Add object 2 name** (e.g., SPEF)：TODO: 用一句话解释该对象在EDA领域的含义 (e.g., Standard Parasitic Exchange Format，包含寄生参数信息)

**TODO: Add correctness keyword from description** (e.g., "correct")在EDA领域的含义：
- **TODO: Add dimension 1** (e.g., 完整性)：TODO: 简述该维度的判定标准 (e.g., 版本标识信息必须存在（工具名称、版本号、生成时间）)
- **TODO: Add dimension 2** (e.g., 可追溯性)：TODO: 简述该维度的判定标准 (e.g., 能够识别文件的生成来源和时间点)
- **TODO: Add dimension 3** (e.g., 一致性)：TODO: 简述该维度的判定标准 (e.g., netlist和SPEF都应包含相应的版本信息)

---

## 2. Parsing Logic

**需要提取的信息**：

### 2.1 TODO: Add object 1 name (e.g., Netlist)文件信息
- **目的**：TODO: 从Section 1的正确性维度推导提取目的 (e.g., 验证netlist文件的版本信息完整性)
- **关键信息**：
  - TODO: Add key info 1 (e.g., 文件路径)（用于TODO: Add usage 1 (e.g., 定位和输出)）
  - TODO: Add key info 2 (e.g., 文件加载状态)（用于TODO: Add usage 2 (e.g., 确认文件可访问)）
  - TODO: Add key info 3 (e.g., 生成工具名称)（用于TODO: Add usage 3 (e.g., 工具信息验证)）
  - TODO: Add key info 4 (e.g., 工具版本号)（用于TODO: Add usage 4 (e.g., 版本验证)）
  - TODO: Add key info 5 (e.g., 文件生成时间戳)（用于TODO: Add usage 5 (e.g., 时间追溯)）

### 2.2 TODO: Add object 2 name (e.g., SPEF)文件信息
- **目的**：TODO: 从Section 1的正确性维度推导提取目的 (e.g., 验证SPEF文件的版本信息完整性)
- **关键信息**：
  - TODO: Add key info 1 (e.g., 文件路径)（用于TODO: Add usage 1 (e.g., 定位和输出)）
  - TODO: Add key info 2 (e.g., 文件加载状态)（用于TODO: Add usage 2 (e.g., 确认文件可访问)）
  - TODO: Add key info 3 (e.g., SPEF标准版本)（用于TODO: Add usage 3 (e.g., 格式标准验证)）
  - TODO: Add key info 4 (e.g., 生成程序名称和版本)（用于TODO: Add usage 4 (e.g., 程序信息验证)）
  - TODO: Add key info 5 (e.g., 设计名称和层次信息)（用于TODO: Add usage 5 (e.g., 设计匹配验证)）
  - TODO: Add key info 6 (e.g., 文件生成时间戳)（用于TODO: Add usage 6 (e.g., 时间追溯)）

**实现要求**：
从实际文件或日志中学习并识别TODO: Add information type from Section 1 (e.g., 版本信息)的格式，不依赖预设规则。

---

## 3. Check Logic

根据description "TODO: Copy description text here"，需要验证以下项目的TODO: Add verification focus from Section 1 (e.g., 完整性)：

**验证项目**：
1. TODO: Add verification item 1 (e.g., Netlist文件加载状态)
2. TODO: Add verification item 2 (e.g., Netlist版本信息（工具名称、版本号、生成时间戳）)
3. TODO: Add verification item 3 (e.g., SPEF文件加载状态)
4. TODO: Add verification item 4 (e.g., SPEF版本信息（SPEF标准版本、生成程序信息、生成时间戳）)

---

### 3.1 requirements.pattern_items = N/A（存在性检查）

**处理逻辑**：
1. 接受Section 2 parsing logic的输出（parsed_data）
2. 对上述TODO: Add N (e.g., 4)个验证项目进行**存在性检查**：
   - **TODO: Verification item 1 name** (e.g., Netlist文件加载状态)：parsed_data中是否包含TODO: Expected fields (e.g., netlist文件路径和加载成功标识)？
     - TODO: Found condition (e.g., 包含) → found_items
     - TODO: Missing condition (e.g., 不包含) → missing_items
   
   - **TODO: Verification item 2 name** (e.g., Netlist版本信息)：parsed_data中是否同时包含TODO: Expected fields (e.g., 工具名称、版本号、时间戳)？
     - TODO: Found condition (e.g., 三者都有) → found_items
     - TODO: Missing condition (e.g., 任一缺失) → missing_items
   
   - **TODO: Verification item 3 name** (e.g., SPEF文件加载状态)：parsed_data中是否包含TODO: Expected fields (e.g., SPEF文件路径和加载成功标识)？
     - TODO: Found condition (e.g., 包含) → found_items
     - TODO: Missing condition (e.g., 不包含) → missing_items
   
   - **TODO: Verification item 4 name** (e.g., SPEF版本信息)：parsed_data中是否同时包含TODO: Expected fields (e.g., SPEF标准版本、程序信息、时间戳)？
     - TODO: Found condition (e.g., 三者都有) → found_items
     - TODO: Missing condition (e.g., 任一缺失) → missing_items

3. 返回：`(found_items, missing_items, extra_items)`
   - extra_items为空（不预期有额外项目）

**判定规则**：
- 所有TODO: N (e.g., 4)个项目都在found_items中 → 整体PASS
- 任一项目在missing_items中 → 整体FAIL

---

### 3.2 requirements.pattern_items > 0（存在性检查 + Pattern匹配）

**与3.1的差异**：需要对TODO: Add which items need pattern matching (e.g., 版本信息)进行pattern匹配验证

**额外处理**：
1. 接受requirements.pattern_items作为匹配规则
2. 对**TODO: Add which items need pattern matching** (e.g., 版本信息项目（Netlist版本信息、SPEF版本信息）)增加pattern匹配：
   
   - **TODO: Item 1 name** (e.g., Netlist版本信息)：
     - 存在且匹配pattern_items → found_items
     - 存在但不匹配pattern_items → extra_items
     - 不存在 → missing_items（同3.1）
   
   - **TODO: Item 2 name** (e.g., SPEF版本信息)：
     - 存在且匹配pattern_items → found_items
     - 存在但不匹配pattern_items → extra_items
     - 不存在 → missing_items（同3.1）

3. **TODO: Add which items don't need pattern** (e.g., 文件加载状态)的判断逻辑与3.1相同（不需要pattern匹配）

4. 返回：`(found_items, missing_items, extra_items)`

**判定规则**：
- 所有项目都在found_items中且pattern都匹配 → 整体PASS
- 存在missing_items或extra_items → 整体FAIL

---

## 4. Waiver Logic

基于description "TODO: Copy description text here"，对TODO: Add N (e.g., 4)个验证项目的豁免场景分析：

**可能需要豁免的项目**：

1. **TODO: Verification item 1 name** (e.g., SPEF文件加载状态)
   - 豁免场景：TODO: Add waiver scenario (e.g., 综合阶段不需要SPEF文件，跳过SPEF检查属于正常)
   - 典型waive原因："TODO: Add typical waiver reason" (e.g., "Current stage is synthesis, SPEF check is not applicable")

2. **TODO: Verification item 2 name** (e.g., SPEF版本信息)
   - 豁免场景：TODO: Add waiver scenario (e.g., 某些设计阶段SPEF不可用或使用简化的SPEF)
   - 典型waive原因："TODO: Add typical waiver reason" (e.g., "SPEF not required in early design stage")

3. **TODO: Verification item 3 name** (e.g., Netlist版本时间戳)
   - 豁免场景：TODO: Add waiver scenario (e.g., 使用历史版本的golden netlist进行回归测试)
   - 典型waive原因："TODO: Add typical waiver reason" (e.g., "Using historical golden netlist for regression")

4. **TODO: Verification item 4 name** (e.g., SPEF版本时间戳)
   - 豁免场景：TODO: Add waiver scenario (e.g., 使用历史版本的golden SPEF，或版本格式特殊但已确认可用)
   - 典型waive原因："TODO: Add typical waiver reason" (e.g., "Using golden SPEF from previous release")

Waiver Control接受check logic的输出（found_items, missing_items, extra_items）和waivers配置，对上述项目的violation进行豁免处理。

---

### 4.1 waivers.value = 0（强制PASS模式）

**处理逻辑**：
1. 接受check logic的输出结果
2. **强制整体结果为PASS**
3. 对所有TODO: Add N (e.g., 4)个验证项目的violation进行豁免：
   - **TODO: Verification item 1** (e.g., SPEF文件加载状态缺失) → 转为INFO，标记`[WAIVED_AS_INFO]`
   - **TODO: Verification item 2** (e.g., SPEF版本信息缺失) → 转为INFO，标记`[WAIVED_AS_INFO]`
   - **TODO: Verification item 3** (e.g., Netlist/SPEF版本时间戳不匹配) → 转为INFO，标记`[WAIVED_AS_INFO]`
   - **TODO: Verification item 4** (e.g., 其他任何missing/extra项目) → 转为INFO，标记`[WAIVED_AS_INFO]`
4. waivers.waive_items作为豁免原因说明 → 输出INFO，标记`[WAIVED_INFO]`

**效果**：
- 所有violation降级为INFO，保留详情
- 即使TODO: Add most critical item (e.g., SPEF)完全不可用，也判定为PASS
- 适用于明确不需要检查的场景（如TODO: Add typical force pass scenario (e.g., 综合阶段强制跳过SPEF检查)）

---

### 4.2 waivers.value > 0（选择性豁免模式）

**处理逻辑**：
1. 接受check logic的输出结果
2. 对TODO: Add N (e.g., 4)个验证项目的violation进行选择性匹配：
   
   - **TODO: Verification item 1** (e.g., SPEF文件加载状态缺失)：
     - waive_items包含"TODO: keyword 1" (e.g., SPEF)"或"TODO: keyword 2" (e.g., synthesis)" → 豁免，标记`[WAIVER]`
     - 不匹配 → 保持ERROR
   
   - **TODO: Verification item 2** (e.g., SPEF版本信息缺失)：
     - waive_items包含"TODO: keyword 1" (e.g., SPEF)"或"TODO: keyword 2" (e.g., version)" → 豁免，标记`[WAIVER]`
     - 不匹配 → 保持ERROR
   
   - **TODO: Verification item 3** (e.g., Netlist版本时间戳不匹配)：
     - waive_items包含"TODO: keyword 1" (e.g., netlist)"或"TODO: keyword 2" (e.g., golden)"或"TODO: keyword 3" (e.g., historical)" → 豁免，标记`[WAIVER]`
     - 不匹配 → 保持ERROR
   
   - **TODO: Verification item 4** (e.g., SPEF版本时间戳不匹配)：
     - waive_items包含"TODO: keyword 1" (e.g., SPEF)"或"TODO: keyword 2" (e.g., golden)"或"TODO: keyword 3" (e.g., historical)" → 豁免，标记`[WAIVER]`
     - 不匹配 → 保持ERROR

3. 未使用的waive_items → 输出WARN，标记`[WAIVER]`
4. 重新判定：
   - 所有violation都被豁免 → PASS
   - 仍有未豁免的violation → FAIL

**匹配规则**：
- 单词级别关键词匹配：waive_items与具体violation项目的描述匹配
- 例如：TODO: Add matching example (e.g., SPEF加载失败 + waive_items="Current stage is synthesis" → 匹配成功（包含"synthesis"关键词）)

---

## 5. Output Messages

输出分为两个层次：Console输出（简洁）和Report输出（详细）

### 5.1 Console输出（Log格式）

**结构**：
```
[PASS/FAIL]:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
TODO: ITEM_ID-[级别][序号]: [标签]: [分类标题]:
  Severity: [级别] Occurrence: [数量]
  - [详细项目1]
  - [详细项目2]
  ...
```

**PASS场景示例**：
```
PASS:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
TODO: ITEM_ID-INFO01: TODO: Found items title (e.g., Netlist version information found):
  Severity: Info Occurrence: TODO: COUNT
  - TODO: Found item 1 detail (e.g., Netlist file: /path/to/design.v.gz
    Tool: Genus version 21.1
    Generated: 2025-01-05)
  - TODO: Found item 2 detail (e.g., SPEF file: /path/to/design.spef.gz
    SPEF version: IEEE 1481-1999
    Program: Innovus 21.1
    Generated: 2025-01-05)
```

**FAIL场景示例**：
```
FAIL:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
TODO: ITEM_ID-ERROR01: TODO: Error title (e.g., Version information missing):
  Severity: Error Occurrence: TODO: ERROR_COUNT
  - TODO: Missing item 1 (e.g., SPEF file path not found in STA log)
  - TODO: Missing item 2 (e.g., SPEF version information not found)
TODO: ITEM_ID-INFO01: TODO: Partial info title (e.g., Partial information found):
  Severity: Info Occurrence: TODO: INFO_COUNT
  - TODO: Found item detail (e.g., Netlist file: /path/to/design.v.gz
    Tool: Genus version 21.1
    Generated: 2025-01-05)
```

**Waiver场景示例（waivers.value=0）**：
```
PASS:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
TODO: ITEM_ID-INFO01: [WAIVED_INFO]: Waiver reason:
  Severity: Info Occurrence: 1
  - TODO: Waiver reason from waive_items (e.g., Current stage is synthesis, SPEF check is not applicable.)
TODO: ITEM_ID-INFO02: [WAIVED_AS_INFO]: TODO: Waived content title (e.g., SPEF information waived):
  Severity: Info Occurrence: TODO: WAIVED_COUNT
  - TODO: Waived item 1 (e.g., SPEF file path not found in STA log)
  - TODO: Waived item 2 (e.g., SPEF version information not found)
```

**Waiver场景示例（waivers.value>0，部分豁免）**：
```
FAIL:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
TODO: ITEM_ID-ERROR01: TODO: Unwaived error title (e.g., Version mismatch not waived):
  Severity: Error Occurrence: TODO: ERROR_COUNT
  - TODO: Unwaived error (e.g., Netlist version timestamp does not match pattern: expected 2025, found 2024)
TODO: ITEM_ID-INFO01: [WAIVER]: TODO: Waived items title (e.g., SPEF issues waived):
  Severity: Info Occurrence: TODO: WAIVED_COUNT
  - TODO: Waived item 1 (e.g., SPEF file not loaded: Synthesis stage, SPEF not required)
  - TODO: Waived item 2 (e.g., SPEF version information missing: Synthesis stage)
```

---

### 5.2 Report输出（详细格式）

**结构**：
```
[PASS/FAIL]:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
[级别] Occurrence: [总数]
[序号]: [级别]: [项目描述]: [详细信息][标签]
```

**PASS场景示例**：
```
PASS:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
Info Occurrence: TODO: COUNT
1: Info: TODO: Item 1 short desc (e.g., Netlist version: Genus 21.1, Generated 2025-01-05): TODO: Item 1 full desc (e.g., Version information complete)
2: Info: TODO: Item 2 short desc (e.g., SPEF version: IEEE 1481-1999, Innovus 21.1, Generated 2025-01-05): TODO: Item 2 full desc (e.g., Version information complete)
```

**FAIL场景示例**：
```
FAIL:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
Error Occurrence: TODO: ERROR_COUNT
1: Error: TODO: Error 1 short desc (e.g., SPEF file path not found in STA log): TODO: Error 1 detail (e.g., Design has no SPEF file or unexpected error)
2: Error: TODO: Error 2 short desc (e.g., SPEF version information not found): TODO: Error 2 detail (e.g., Version information incomplete)
Info Occurrence: TODO: INFO_COUNT
3: Info: TODO: Info short desc (e.g., Netlist version: Genus 21.1, Generated 2025-01-05): TODO: Info detail (e.g., Version information complete)
```

**Waiver场景示例（waivers.value=0）**：
```
PASS:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
Info Occurrence: TODO: COUNT
1: Info: TODO: Waive reason (e.g., Current stage is synthesis, SPEF check is not applicable.): Waiver reason[WAIVED_INFO]
2: Info: TODO: Waived item 1 (e.g., SPEF file path not found in STA log): TODO: Waived item 1 detail (e.g., Design has no SPEF file)[WAIVED_AS_INFO]
3: Info: TODO: Waived item 2 (e.g., SPEF version information not found): TODO: Waived item 2 detail (e.g., Version information incomplete)[WAIVED_AS_INFO]
```

**Waiver场景示例（waivers.value>0，部分豁免）**：
```
FAIL:TODO: ITEM_ID:TODO: DESCRIPTION_TEXT
Error Occurrence: TODO: ERROR_COUNT
1: Error: TODO: Unwaived error (e.g., Netlist version timestamp does not match pattern): TODO: Error detail (e.g., Version mismatch)
Info Occurrence: TODO: INFO_COUNT
2: Info: TODO: Waived item 1 (e.g., SPEF file not loaded): TODO: Waived item 1 detail (e.g., Synthesis stage, SPEF not required)[WAIVER]
3: Info: TODO: Waived item 2 (e.g., SPEF version information missing): TODO: Waived item 2 detail (e.g., Synthesis stage)[WAIVER]
```

---

### 5.3 输出内容映射

| Check Logic结果 | Waiver处理 | Log级别 | Report级别 | 标签 |
|----------------|-----------|---------|-----------|------|
| found_items | 无waiver | INFO | Info | 无 |
| missing_items | 无waiver | ERROR | Error | 无 |
| extra_items | 无waiver | ERROR | Error | 无 |
| missing_items | waiver=0 | INFO | Info | [WAIVED_AS_INFO] |
| extra_items | waiver=0 | INFO | Info | [WAIVED_AS_INFO] |
| waive_items配置 | waiver=0 | INFO | Info | [WAIVED_INFO] |
| missing_items | waiver>0匹配 | INFO | Info | [WAIVER] |
| extra_items | waiver>0匹配 | INFO | Info | [WAIVER] |
| missing_items | waiver>0不匹配 | ERROR | Error | 无 |
| extra_items | waiver>0不匹配 | ERROR | Error | 无 |

---

## 6. Implementation Guide

### 6.1 实现流程总览

```
Input: item.yaml配置
  ↓
[Parsing Logic - Section 2]
从TODO: Add data source (e.g., STA日志或文件)中提取TODO: Add N info types (e.g., 4)类信息：
- TODO: Info type 1 (e.g., Netlist文件加载状态)
- TODO: Info type 2 (e.g., Netlist版本信息（工具名、版本、时间）)
- TODO: Info type 3 (e.g., SPEF文件加载状态)
- TODO: Info type 4 (e.g., SPEF版本信息（标准、程序、时间）)
  ↓
[Check Logic - Section 3]
判断TODO: Add N (e.g., 4)个验证项目：
- 存在性检查（N/A模式）或pattern匹配（>0模式）
- 返回：(found_items, missing_items, extra_items)
  ↓
[Waiver Logic - Section 4]
豁免处理（如果配置了waiver）：
- value=0：强制PASS，所有violation→INFO+标签
- value>0：匹配waive_items，匹配的→INFO+[WAIVER]
  ↓
[Output Formatting - Section 5]
生成两种输出：
- Console (Log)：分级别、有统计、结构化
- Report：逐项列出、带标签、易解析
  ↓
Output: PASS/FAIL + 详细报告
```

### 6.2 关键实现要点

#### Parsing实现（Section 2）
- **数据源推断**：根据description推断应读取TODO: Add data source inference (e.g., STA日志文件（sta_post_syn.log）)
- **信息提取**：
  - TODO: Add info extraction method 1 (e.g., 文件加载状态：查找日志中的"Reading netlist"、"Loading SPEF"等关键字)
  - TODO: Add info extraction method 2 (e.g., 版本信息：从文件头部或日志解析提取工具名称、版本号、时间戳)
- **自主学习**：不预设固定格式，从实际内容学习TODO: Add learning target (e.g., 版本信息)的结构
- **容错处理**：文件不存在、格式异常时返回missing_items，不抛出异常

#### Check Logic实现（Section 3）
- **验证项目**：明确检查TODO: Add N (e.g., 4)个项目（Section 3开头列出的）
- **分类逻辑**：
  - N/A模式：parsed_data包含 → found_items，不包含 → missing_items
  - Pattern模式：存在且匹配 → found_items，存在不匹配 → extra_items，不存在 → missing_items
- **返回结构**：`(found_items, missing_items, extra_items)`，确保项目名称与Section 3定义一致

#### Waiver Control实现（Section 4）
- **匹配规则**：单词级别关键词匹配（如TODO: Add example keywords (e.g., "SPEF"、"synthesis"、"golden")）
- **标签应用**：
  - value=0：所有violation加`[WAIVED_AS_INFO]`，waive_items加`[WAIVED_INFO]`
  - value>0：匹配成功的加`[WAIVER]`
- **判定更新**：豁免后重新判定PASS/FAIL

#### Output Formatting实现（Section 5）
- **Log格式**：按Section 5.1的结构，使用`TODO: ITEM_ID-[级别][序号]`编号
- **Report格式**：按Section 5.2的结构，`[序号]: [级别]: [描述]: [详情][标签]`
- **内容映射**：遵循Section 5.3的映射表，确保found_items→Info、missing_items→Error等

### 6.3 特殊场景处理

#### 场景1：TODO: Add scenario 1 title (e.g., SPEF在综合阶段不可用)
- Parsing结果：TODO: Add parsing result (e.g., SPEF文件加载状态 → missing_items)
- Waiver处理：如果waive_items包含TODO: Add keywords (e.g., "synthesis"或"SPEF") → 豁免为INFO
- 输出示例：见Section 5 Waiver场景

#### 场景2：TODO: Add scenario 2 title (e.g., 使用历史版本netlist进行测试)
- Check结果：TODO: Add check result (e.g., Netlist时间戳不匹配pattern → extra_items)
- Waiver处理：如果waive_items包含TODO: Add keywords (e.g., "golden"或"historical") → 豁免为INFO
- 输出示例：见Section 5.2 Waiver场景（value>0部分豁免）

#### 场景3：TODO: Add scenario 3 title (e.g., 文件完全缺失)
- Parsing结果：TODO: Add parsing result (e.g., 所有4个项目 → missing_items)
- 无Waiver：输出全ERROR，整体FAIL
- 有Waiver（value=0）：输出全INFO+标签，整体PASS

### 6.4 代码组织建议

```python
class TODO: Add class name (e.g., IMP_10_0_0_00_Checker)(BaseChecker):
    def _parse_input_files(self) -> Dict:
        """实现Section 2的信息提取"""
        # 1. 推断TODO: Add data source (e.g., STA日志路径)
        # 2. 提取TODO: Add N (e.g., 4)类信息：TODO: Add info types (e.g., netlist加载、netlist版本、SPEF加载、SPEF版本)
        # 3. 返回结构化数据
        return {'found_items': {...}, 'missing_items': {...}}
    
    def _boolean_check_logic(self, parsed_data) -> tuple:
        """实现Section 3.1的存在性检查"""
        # 对TODO: Add N (e.g., 4)个验证项目判断found/missing
        return (found_items, missing_items, extra_items)
    
    def _pattern_check_logic(self, parsed_data) -> tuple:
        """实现Section 3.2的pattern匹配"""
        # 对TODO: Add which items (e.g., 版本信息项目)增加pattern匹配，不匹配→extra_items
        return (found_items, missing_items, extra_items)
```

注意：具体实现应基于框架的BaseChecker、Mixin等类，遵循CHECKER_IMPLEMENTATION_RULES中的三层架构。
