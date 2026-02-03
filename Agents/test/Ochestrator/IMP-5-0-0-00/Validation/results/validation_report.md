# Validation Report: IMP-5-0-0-00

## 概要
- 总测试数: 8
- 有效测试: 6
- CORRECT: 6
- INCORRECT: 0
- UNCERTAIN: 0
- TESTCASE_INVALID: 2

## 整体判定
**PASS** - 所有测试通过

## 测试详情
### TC_01
- 盲推预期: PASS
- 实际输出: PASS
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 1 boolean check: log样本显示所有technology libraries都有_ccs后缀(library_ccs_indicator found)，且无Wireload Model字段(wireload_model_name is None)。满足pass_condition: "library_ccs_indicator found AND wireload_model_name is None"

### TC_02
- 盲推预期: PASS
- 实际输出: PASS
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 2 pattern search: 搜索pattern_items ["*wireload*", "*_wlm"]。Log样本中所有库名格式为"tcbn03e_..._ccs 110"，不包含wireload或_wlm字符串。违规数=0，满足 violations ≤ requirements.value

### TC_03
- 盲推预期: PASS
- 实际输出: PASS
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 1 boolean check (同TC_01): library models confirmed via _ccs indicators, no wireload references

### TC_04
- 盲推预期: PASS
- 实际输出: PASS
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 1 boolean check (同TC_01): library-based timing models confirmed

### TC_05
- 盲推预期: UNCERTAIN
- 实际输出: PASS
- 判定: **TESTCASE_INVALID**
- 置信度: HIGH
- 推理: 配置显示waivers.value=4且有waive_items，但缺少pattern_items字段。根据Type 3定义需要"requirements.value>0, pattern_items exists"，此配置不满足Type 3的前置条件。无法确定checker如何处理这种不完整配置。
- 问题: TestCase设计问题：Type 3需要pattern_items来定义要搜索的违规模式，但配置中未提供。这导致无法执行"搜索pattern_items并分类waived/unwaived violations"的逻辑。Checker可能降级到Type 1处理或使用默认行为。
- 建议: 修正TestCase: 为TC_05添加pattern_items配置，例如 pattern_items: ["*_ulvt*"] 来匹配waive_items中的ULVT库，使测试能够验证waiver分类逻辑。
- 无效原因: 配置不完整：Type 3要求pattern_items存在，但配置中缺失该字段，导致测试无法验证预期的waiver逻辑

### TC_06
- 盲推预期: UNCERTAIN
- 实际输出: PASS
- 判定: **TESTCASE_INVALID**
- 置信度: HIGH
- 推理: 同TC_05，waivers.value=2但缺少pattern_items。Type 3配置不完整，无法推理预期行为。
- 问题: TestCase设计问题：与TC_05相同，Type 3配置缺少必需的pattern_items字段。无法验证"部分waiver"场景下的unwaived violations计数逻辑。
- 建议: 修正TestCase: 添加pattern_items (如 ["*_ulvt*"]) 并调整requirements.value，使测试能够验证部分豁免场景：部分违规被waive，部分未被waive，检查unwaived count是否≤阈值。
- 无效原因: 配置不完整：Type 3需要pattern_items定义违规模式，当前配置无法触发预期的waiver分类逻辑

### TC_07
- 盲推预期: PASS
- 实际输出: PASS
- 判定: **CORRECT**
- 置信度: MEDIUM
- 推理: Type 4 boolean check with waiver: log样本显示library models confirmed (_ccs indicators present, no wireload)。根据Type 4逻辑 "library_models_confirmed OR global_waiver_applied"，即使有global waiver配置，因为library models已确认，应直接PASS而不需要应用waiver。
- 建议: 建议增加测试用例：提供一个wireload model存在的log样本来验证global waiver是否能正确应用（即测试 "NOT library_models_confirmed AND global_waiver_applied" 分支）

### TC_08
- 盲推预期: PASS
- 实际输出: PASS
- 判定: **CORRECT**
- 置信度: HIGH
- 推理: Type 2 pattern search: 搜索["*_nldm*", "*wireload*"]。Log样本中所有库都是_ccs格式，不包含nldm或wireload。违规数=0，满足阈值条件。
