# 数据规范与配置说明

## 目录
- 原始采集记录（raw JSON）
- 平台 stats JSON（生成器输入）
- report_config.json 字段
- negtype_map JSON
- 竞品评价 JSON

## 原始采集记录（raw JSON）
浏览器采集每平台保存为数组，每条：
```json
{
  "user": "昵称", "date": "YYYY-MM-DD", "content": "评价正文",
  "sku": "规格", "imgs": ["缩略图URL"], "big_imgs": ["大图URL"],
  "has_video": false
}
```
- `date` 统一 ISO；天猫只有 `MM-DD` 时需按当下时间推定年份并注明。
- `imgs`/`big_imgs` 只存 CDN URL；京东 `.dpg` 实为标准 JPEG 可直接用。

## 平台 stats JSON（生成器输入）
```json
{
  "total": 309,
  "reviews": [
    {
      "user": "昵称", "date": "YYYY-MM-DD", "content": "正文", "sku": "",
      "imgs": [], "big_imgs": [], "has_video": false,
      "dims": ["打印精度与效果", "性价比与赠品"],
      "neg": false
    }
  ]
}
```
- `dims` 必须与 config `cat` 的中文维度名一致。生成器默认 `CAT`（3D 打印示例）映射：打印精度与效果=quality、操作易用性=easy、打印速度=speed、性价比与赠品=value、物流发货=logistics、包装防护=pack、质量做工=build、外观设计=design、客服服务=service、使用体验与功能=experience、耗材与配件=material。新增品类维度时同步修改 `CAT`。
- 无维度且正文 ≥6 字 → overall（整体好评）；无内容 → default。
- `neg=true` 必须已经人工复核（见 classification-rules.md）。

## report_config.json 字段
见 `assets/config.example.json`。

| 字段 | 必填 | 说明 |
|---|---|---|
| product_name | 是 | 报告标题中的商品全称 |
| output_html | 是 | 输出 HTML 绝对路径 |
| report_date | 否 | 默认当天 |
| platforms | 是 | 1~N 个平台：`key`（英文标识）、`name`（表格全称）、`short`（按钮/徽章短名）、`color`、`stats`（stats JSON 路径）、`source`（如 item id，用于页脚） |
| competitor | 否 | `{name, path}`；path 为竞品评价 JSON，省略则竞品模块显示待接入 |
| negtype_map | 否 | 差评归因映射路径，省略则全部差评默认 defect |
| cat | 否 | 按品类定义维度：`{"中文维度名": ["英文key", "卡片显示名", "颜色"]}`；覆盖后 `dims` 用这里的中文名 |
| text_points | 否 | 夸赞点：`[["std|gain", "点名", ["关键词..."]], ...]`，我方与竞品共用此口径 |
| material | 否 | 素材词表：`{cats, vivid_scene, vivid_weak, vivid_prod, vivid_metaphor, hl_scene}`；`cats` 为 `{"分类key": ["显示名", "颜色", ["关键词..."], "用途建议"]}` |
| kwchips | 否 | 象限自定义标签关键词：`{"标签key": ["关键词..."]}`，供 quad 的 `kw:标签key` 筛选用 |
| scen / persona | 否 | 覆盖默认场景/人群表：`[[名称, [关键词...], 定位, 营销建议], ...]` |
| quad | 否 | 覆盖象限标签：`{core, opportunity, baseline, hidden}`，每项为 `[[显示文案, 筛选目标], ...]`；筛选目标为维度英文键或 `kw:xxx`（xxx 在生成器 KWCHIPS 中定义） |

## negtype_map JSON
```json
{
  "tmall|2025-09-27": ["scene"],
  "jd|2024-04-25": ["expect"],
  "jd|2024-05-29": ["defect", "service"]
}
```
键为 `平台key|评价ISO日期`，值为归因类型数组（defect/service/expect/scene）。同一平台同日有多条差评时需在生成器中改为按内容判读后指定。

## 竞品评价 JSON
数组，每条至少含 `content`：
```json
[{"nick": "昵称", "date": "YYYY-MM-DD", "content": "竞品评价正文"}]
```
可从我方同类报告 HTML 的 `const DATA` 或浏览器采集中提取；双方使用同一 TEXT_POINTS 口径统计。
