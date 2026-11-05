# 评价报告 · ReviewInsight

把电商商品评价变成一份**可交互的三层业务目标分析 HTML 报告**的 AI Agent Skill。

**不限制品类**：3D 打印、家电、美妆、食品、服饰等均可，全部分析词表都可按品类配置。

适用平台：天猫/淘宝、京东等（浏览器采集）；也支持直接喂入已有评价数据（JSON / 同类报告 HTML）。

## 报告包含什么

| 业务目标 | 模块 | 内容 |
|---|---|---|
| ① 差评止损 | 差评归因分层 | 硬缺陷 / 服务型 / 预期不符 / 场景错配，多标签归因、数量与整改建议，点击卡片筛选对应差评 |
| ② 好评增效 | 提取语言素材 | 只保留**有画面感、精确**的好评原文，高亮画面场景、比喻与精确数据，可直接用于营销图片/视频创作 |
| ② 好评增效 | 拆分好评动因 | 标配型 / 增益型 / 决策验证型，夸赞点频率统计；接入竞品评价后自动校准差异化（竞品高频的增益点降级为标配） |
| ③ 洞察增收 | 使用场景 / 用户身份 / 品类感知基线图 | 多标签文本推断 + 营销建议，四象限指导卖点表达，每个分类可点击筛选评价 |

通用能力：单/多平台合计与切换、评价明细（平台/昵称/SKU/时间/标签/正文）、带图评价同卡展示与图片灯箱、全部数字随平台联动。

## 质量口径（内置硬性规则）

- **差评**必须正文确实表达不好，"担心破损""后悔没早买""故障率低"等措辞不得误判；差评清单逐条人工复核。
- **语言素材**不要关键词、笼统夸赞和模板化好评；候选入库后人工终审，宁少勿滥。
- 带图评价的文字与它自己的图片始终在同一张卡片。

详细规则见 [references/classification-rules.md](references/classification-rules.md)。

## 安装

把整个目录放进你的 Agent Skill 目录（如 `workspace/.user_skills/review-insight`）。之后对 Agent 说"用评价报告 skill 分析这个商品的评价"即可触发。

## 使用流程

1. **提供输入**：商品链接与平台（或已有评价数据）；可选目标条数、竞品评价列表。
2. **采集与分类**：Agent 用浏览器采集评价并保存原始 JSON，按口径分类并人工复核差评、归因与素材。
3. **配置**：复制 `assets/config.example.json` 为 `report_config.json` 填写。字段与数据格式见 [references/data-schema.md](references/data-schema.md)。
4. **生成报告**：

```bash
python3 scripts/build_report.py report_config.json
```

5. **验证与交付**：浏览器检查交互与数字一致性后交付单文件 HTML；可选覆盖上传飞书云空间保留链接与版本。

单平台、无竞品、无归因映射均可运行，对应模块自动降级展示。

## 配置示例（最小）

```json
{
  "product_name": "品牌 型号 商品全称",
  "output_html": "/absolute/path/评价分析报告.html",
  "platforms": [
    {
      "key": "tmall",
      "name": "天猫（XX旗舰店）",
      "short": "天猫",
      "color": "#ff5000",
      "stats": "/absolute/path/tmall_reviews_stats.json",
      "source": "item 000000000000"
    }
  ]
}
```

按品类在 config 中定义：`cat`（卖点维度）、`text_points`（夸赞点与竞品口径）、`material`（素材分类与画面词表）、`scen` / `persona` / `quad` / `kwchips`（场景、人群、象限）。生成器默认值仅为 3D 打印示例，全部可覆盖，无需改代码。

## 目录结构

```
review-insight/
├── SKILL.md                        # 触发描述与工作流程
├── scripts/
│   └── build_report.py             # 配置驱动的报告生成器
├── references/
│   ├── classification-rules.md     # 差评/归因/素材/动因口径
│   └── data-schema.md              # 数据与配置字段规范
└── assets/
    └── config.example.json         # 配置模板
```

## 依赖

- 生成器仅使用 Python 3 标准库，无第三方依赖。
- 采集与验证依赖 Agent 的浏览器能力；登录/验证码由用户接管完成，不提供账号密码。
