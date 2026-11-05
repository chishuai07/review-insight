# -*- coding: utf-8 -*-
"""电商评价三层业务目标分析报告生成器（差评止损 / 好评增效 / 洞察增收）。

用法: python3 build_report.py <config.json>
config 字段与数据格式见 references/data-schema.md。
"""
import json, re, sys, os, datetime

CFG = json.load(open(sys.argv[1], encoding='utf-8'))
OUT = CFG['output_html']
PRODUCT = CFG.get('product_name', '商品')
PLATFORMS = CFG['platforms']          # [{key, name, short, color, stats, source?}]
COMP_CFG = CFG.get('competitor')      # {name, path} 可选；path 为 [{content},...] JSON
COMP_NAME = COMP_CFG['name'] if COMP_CFG else '竞品'
NEGTYPE_PATH = CFG.get('negtype_map')  # 可选：{"平台key|YYYY-MM-DD": ["defect","service"]}
TODAY = CFG.get('report_date') or datetime.date.today().isoformat()

for pl in PLATFORMS:
    pl['reviews'] = json.load(open(pl['stats'], encoding='utf-8'))['reviews']
PLATMETA = {pl['key']: {'name': pl.get('short', pl['name']), 'color': pl.get('color', '#5f6368')} for pl in PLATFORMS}
platmeta_js = json.dumps(PLATMETA, ensure_ascii=False)
platform_css = '\n'.join(
    f'  .platform-bar button.active[data-p="{pl["key"]}"]{{background:{pl.get("color","#5f6368")};color:#fff;border-color:{pl.get("color","#5f6368")}}}\n'
    f'  .p-{pl["key"]}{{background:{pl.get("color","#5f6368")}}}' for pl in PLATFORMS)

CAT = {
    '打印精度与效果': ('quality', '打印质量与精度', '#ff5000'),
    '操作易用性': ('easy', '操作简单·新手友好', '#ff7a00'),
    '打印速度': ('speed', '打印速度快', '#f5a623'),
    '性价比与赠品': ('value', '性价比与赠品', '#f7b500'),
    '物流发货': ('logistics', '物流发货快', '#00b8d9'),
    '包装防护': ('pack', '包装防护好', '#26a69a'),
    '质量做工': ('build', '做工与质量', '#8e7cc3'),
    '外观设计': ('design', '外观设计', '#9b59b6'),
    '客服服务': ('service', '客服与售后', '#e91e63'),
    '使用体验与功能': ('experience', '使用体验·功能', '#1a73e8'),
    '耗材与配件': ('material', '耗材与配件', '#34a853'),
}
# 品类无关：以下所有词表均可在 config 中按品类覆盖；默认值为 3D 打印示例
CAT = {k: tuple(v) for k, v in CFG.get('cat', CAT).items()}

def cn_date(iso):
    m = re.match(r'(\d+)-(\d+)-(\d+)', iso or '')
    return f'{m.group(1)}年{int(m.group(2))}月{int(m.group(3))}日' if m else (iso or '')

def convert(reviews, platform):
    out = []
    for r in reviews:
        cats = []
        for d in r['dims']:
            c = CAT.get(d, (None,))[0]
            if c:
                cats.append(c)
        if not cats and len(r['content']) >= 6:
            cats = ['overall']
        elif not cats:
            cats = ['default']
        imgs = r['imgs'][:6]
        bigs = (r.get('big_imgs') or r['imgs'])[:6]
        out.append({
            'p': platform,
            'nick': r['user'],
            'date': cn_date(r['date']),
            'iso': r['date'],
            'sku': (r['sku'] or '')[:36],
            'content': r['content'],
            'pics': imgs,
            'bigs': bigs,
            'video': r.get('has_video', False),
            'cats': cats,
            'neg': bool(r['neg']),
        })
    return out

DATA = []
for pl in PLATFORMS:
    DATA += convert(pl['reviews'], pl['key'])
DATA.sort(key=lambda r: r['iso'], reverse=True)
N = len(DATA)
PLAT_N = {pl['key']: len(pl['reviews']) for pl in PLATFORMS}

# ---------- 差评归因分层（逐条人工判读，一条差评可归入多个类型） ----------
# 类型: defect=硬缺陷型 service=服务型 expect=预期不符型 scene=场景错配型
# 映射文件格式: {"tmall|2025-09-27": ["scene"], "jd|2024-04-25": ["expect"]}
NEGTYPE = {}
if NEGTYPE_PATH and os.path.exists(NEGTYPE_PATH):
    NEGTYPE = {tuple(k.split('|', 1)): v for k, v in json.load(open(NEGTYPE_PATH, encoding='utf-8')).items()}
for r in DATA:
    if r['neg']:
        r['negtype'] = NEGTYPE.get((r['p'], r['iso']), ['defect'])

# ---------- 好评语言素材提取（有画面感、精确表达的好评 → 营销图/视频素材） ----------
MAT_CATS = {
    'detail': ('细节控·精度赞美', '#e91e63', ['纹理','纹路','头发丝','符文','褶皱','无牙仔','翅膀','螺旋','层纹','微缩','纤毫'], '用于细节特写图/微距视频文案'),
    'easy':   ('新手友好·上手故事', '#ff7a00', ['新手','小白','开箱即用','上手','傻瓜式','免调平','自动调平','教程','闭眼入','入门','第一次就'], '用于新手向短视频脚本、教程封面'),
    'speed':  ('速度效率', '#f5a623', ['速度','飞快','效率','提速','两个半小时','一天两锅','十锅','150mm/h','小时'], '用于效率对比图、打印计时画面'),
    'stable': ('稳定省心·零翻车', '#26a69a', ['不翻车','没有翻车','没翻车','零翻车','稳定','成功率','省心','可靠','稳稳当当','恒温','加热','智能'], '用于“零翻车/成功率”卖点海报'),
    'value':  ('性价比·真香', '#9b59b6', ['性价比','真香','亲民','划算','赠品','送了','便宜','神机','标杆','碾压','诚意'], '用于促销图、价格锚点文案'),
    'scene':  ('使用场景·创作画面', '#1a73e8', ['手办','模型','小恐龙','游戏','微缩','工作室','家用','家里','小朋友','上色','年会','牙模','珠宝','高达'], '用于场景图/短视频分镜参考'),
}
# 强画面标记：具体物象/可视场景，命中即入选；弱标记（微缩、肉眼、锅数）需组合或搭配生产场景才入选
VIVID_SCENE = ['无牙仔','翅膀','冰淇淋','螺旋','头发丝','发丝','符文','褶皱','小恐龙','高达','牙模','珠宝','首饰','蜡模','浮雕','兵人','眼睛高光','恐龙','小朋友','上色','年会','圆梦','桌面','屋外','摸起来','那一刻','成品出来','迫不及待','心心念念','紫光','手办柜','展示柜']
VIVID_WEAK = ['微缩','肉眼','摸着']
VIVID_PROD = ['翻车','支撑','稳定','料盘','加热']
VIVID_METAPHOR = ['璀璨明珠','实力标杆','神机','艺术品','碾压','真香','不香了','闭眼入','天花板','神器','承包','太值了','刚刚硬']
NUM_RE = re.compile(r'(?:\d+(?:\.\d+)?\s*[个多]?\s*锅|[一二两三四五六七八九十]+锅)')
HL_SCENE = ['无牙仔','翅膀纹理','翅膀','冰淇淋','螺旋纹路','螺旋','头发丝','发丝','符文刻印','符文','服装的褶皱','褶皱','小恐龙','微缩模型','高达','牙模','珠宝','首饰','蜡模','浮雕','人偶','兵人','眼睛高光','恐龙','小朋友','年会','上色','桌面','屋外','游戏手办','工作室']
MATCFG = CFG.get('material', {})
MAT_CATS = {k: tuple(v) for k, v in MATCFG.get('cats', MAT_CATS).items()}
VIVID_SCENE = MATCFG.get('vivid_scene', VIVID_SCENE)
VIVID_WEAK = MATCFG.get('vivid_weak', VIVID_WEAK)
VIVID_PROD = MATCFG.get('vivid_prod', VIVID_PROD)
VIVID_METAPHOR = MATCFG.get('vivid_metaphor', VIVID_METAPHOR)
HL_SCENE = MATCFG.get('hl_scene', HL_SCENE)
for r in DATA:
    if r['neg']:
        continue
    text = r['content']
    if len(text) < 45 or '以下是一篇' in text or '朋友圈' in text or '【' in text:
        continue
    nums = NUM_RE.findall(text)
    n_strong = sum(1 for p in VIVID_SCENE if p in text)
    n_weak = sum(1 for p in VIVID_WEAK if p in text) + len(nums)
    vivid = (n_strong >= 1 or n_weak >= 2
             or (nums and any(p in text for p in VIVID_PROD)))
    if not vivid:
        continue
    cats = [k for k, v in MAT_CATS.items() if any(p in text for p in v[2])]
    if not cats:
        continue
    phrases = [{'t': p, 'k': 'scene'} for p in HL_SCENE if p in text]
    phrases += [{'t': p, 'k': 'metaphor'} for p in VIVID_METAPHOR if p in text]
    phrases += [{'t': m, 'k': 'vocab'} for m in nums]
    if not phrases:
        continue
    r['material'] = cats
    r['phrases'] = phrases

# ---------- 拆分好评动因：标配型 / 增益型 / 决策验证型（一条好评可含多个动因） ----------
MOTIVE = {
    'std': ('标配型好评', '#5f6368',
            '全行业都能做到、用户默认该有的点。夸的人再多也不是我们的优势，只是没拖后腿。',
            '营销价值：保持达标即可，不占主图/首屏资源，避免把差异化预算浪费在行业标配。'),
    'gain': ('增益型好评', '#188038',
             '超出预期、用户主动提及的惊喜点' + (f'，已经竞品（{COMP_NAME}）评价对比校准。' if COMP_CFG else '（未接入竞品评价，差异化判断待校准）。'),
             '营销价值：我们的差异化卖点。优先用于主图、短视频与详情页核心表达，建立“只有我们有”的心智。'),
    'verify': ('决策验证型好评', '#0b57d0',
               '下单前最顾虑、收货后专门验证并夸赞的点。',
               '营销价值：转化杀器。用户专门提一句=所有新用户的共同顾虑，把这些原话（如“没有一次打印失败”“新手第一次就成功”）原封不动放到详情页、主图、直播间。'),
}

def has_any(t, words):
    return any(w in t for w in words)

# 夸赞点统一文本口径（我方与竞品使用同一套关键词，保证对比公平）
TEXT_POINTS = [
    ('std', '打印质量·精度达标', ['精度','清晰','细节','细腻','打印效果','效果好','精细','层纹']),
    ('std', '自动调平·操作简单', ['调平','操作简单','上手','新手','小白','傻瓜','教程','易用']),
    ('std', '包装防护到位', ['包装','严实']),
    ('std', '物流发货快', ['物流','发货','快递','次日','隔天']),
    ('std', '外观做工·设计', ['外观','颜值','做工','科技感','设计']),
    ('gain', '高速打印·倾斜离型', ['速度','提速','效率','离型','小时','很快','飞快']),
    ('gain', '微距细节超预期', ['纹理','纹路','头发丝','发丝','符文','褶皱','眼睛高光']),
    ('gain', '料盘加热·低温稳定', ['加热','恒温','料盘']),
    ('gain', '智能功能·监控检测', ['AI','监控','延时','断料','智能检测','智能诊断']),
    ('gain', '远程售后·手把手', ['远程','手把手','耐心','视频指导','一对一','有问必答','随叫随到','指导']),
    ('gain', '赠品/性价比惊喜', ['赠品','赠送','送了','大礼包','真香']),
]
TEXT_POINTS = [tuple(x) for x in CFG.get('text_points', TEXT_POINTS)]

def motive_points(r):
    """返回该好评命中的夸赞点：类型 -> [点名,...]"""
    t = r['content']
    pts = {'std': [], 'gain': [], 'verify': []}
    for k, name, words in TEXT_POINTS:
        if has_any(t, words):
            pts[k].append(name)
    # 决策验证型：下单前的顾虑，收货后专门验证并夸赞
    if has_any(t, ['第一次','首次','新手','小白','开箱']) and has_any(t, ['成功','一次就','直接打','上岸','没失败','零翻车']):
        pts['verify'].append('新手首打成功')
    if has_any(t, ['没有一次','没翻车','不翻车','没有翻车','零翻车','全部成功','都成功','成功率','十锅','几锅','两锅']):
        pts['verify'].append('多锅稳定·零翻车验证')
    if has_any(t, ['对比','犹豫','纠结','研究','看了很久','最终','没让我失望','没有失望','不后悔','没买错']):
        pts['verify'].append('对比选购后认可')
    if has_any(t, ['担心','害怕','忐忑','顾虑']) and has_any(t, ['结果','但是','但','没','成功','放心','惊喜','意外']):
        pts['verify'].append('担心→验证后放心')
    if has_any(t, ['售后','客服']) and has_any(t, ['解决','搞定','处理好','换新','补发']):
        pts['verify'].append('售后问题被解决')
    if has_any(t, ['实测','测试','试打','试用','用了一段时间','用了几天','才来评价','使用了一段时间','用了挺久','用了一个月']):
        pts['verify'].append('实测/长期使用后认可')
    return pts

MOTIVE_POINT_COUNT = {'std': {}, 'gain': {}, 'verify': {}}
for r in DATA:
    if r['neg']:
        continue
    pts = motive_points(r)
    r['motive'] = [k for k, v in pts.items() if v]
    for k, names in pts.items():
        for nm in names:
            MOTIVE_POINT_COUNT[k][nm] = MOTIVE_POINT_COUNT[k].get(nm, 0) + 1
print('动因计数:', {k: sum(1 for r in DATA if not r['neg'] and k in r.get('motive', [])) for k in MOTIVE})

motivecat_js = json.dumps({k: {'name': v[0], 'color': v[1], 'desc': v[2], 'advice': v[3]} for k, v in MOTIVE.items()}, ensure_ascii=False)
mp_cols = ''
for k in ['std', 'gain', 'verify']:
    nm, color = MOTIVE[k][0], MOTIVE[k][1]
    rows = ''.join(f'<div class="mp-row"><span>{p}</span><b>{c}</b></div>'
                   for p, c in sorted(MOTIVE_POINT_COUNT[k].items(), key=lambda x: -x[1]))
    mp_cols += f'<div class="mp-col" style="--ac:{color}"><div class="mp-title">{nm} · 夸赞点频率<span>（合计 {sum(1 for r in DATA if not r["neg"])} 条好评）</span></div>{rows}</div>'

# ---------- 竞品对比（可选；未配置时显示待接入提示） ----------
N_POS = sum(1 for r in DATA if not r['neg'])
if COMP_CFG:
    COMP = json.load(open(COMP_CFG['path'], encoding='utf-8'))
    COMP_POS = [c for c in COMP if c.get('content', '').strip()]
    N_COMP = len(COMP_POS)
    comp_count = {}
    for c in COMP_POS:
        for k, name, words in TEXT_POINTS:
            if has_any(c['content'], words):
                comp_count[name] = comp_count.get(name, 0) + 1

    downgraded, strong_diff = [], []
    comp_rows = ''
    for k, name, words in TEXT_POINTS:
        my_n = MOTIVE_POINT_COUNT[k].get(name, 0)
        cp_n = comp_count.get(name, 0)
        my_rate = my_n / N_POS if N_POS else 0
        cp_rate = cp_n / N_COMP if N_COMP else 0
        if k == 'std':
            verdict, vc = '行业标配，不占核心营销资源', '#5f6368'
        elif cp_rate >= my_rate * 0.7 or cp_rate >= 0.15:
            verdict, vc = '竞品同样高频 → 建议降为标配', '#d93025'
            downgraded.append(name)
        elif cp_n == 0:
            verdict, vc = '竞品未提及 → 强差异化', '#188038'
            strong_diff.append(name)
        else:
            verdict, vc = '我方明显更高 → 差异化保留', '#0b57d0'
            strong_diff.append(name)
        comp_rows += (f'<tr><td>{name}</td><td>{my_n}（{my_rate*100:.0f}%）</td><td>{cp_n}（{cp_rate*100:.0f}%）</td>'
                      f'<td><span class="verdict" style="color:{vc};border-color:{vc}">{verdict}</span></td></tr>')
    comp_html = f'''
      <div class="comp-head">竞品对比：我方 {PRODUCT}（{N_POS} 条好评） vs {COMP_NAME}（{N_COMP} 条评价，同一夸赞点口径）</div>
      <table class="insight-table comp-table">
        <tr><th>夸赞点</th><th style="width:130px">我方提及</th><th style="width:130px">竞品提及</th><th>对比结论</th></tr>
        {comp_rows}
      </table>
      <div class="attr-foot">校准结果：<b>建议降为标配</b>：{'、'.join(downgraded) if downgraded else '无'}；<b>差异化保留/强化</b>：{'、'.join(strong_diff) if strong_diff else '无'}。竞品提及率为 0 不代表竞品没有该功能，仅表示其买家未主动提及。</div>
'''
    print('降级:', downgraded, '| 差异化:', strong_diff)
else:
    comp_html = '''
      <div class="attr-foot"><b>竞品对比（待接入）</b>：提供竞品评价列表后，将输出「我方 vs 竞品」各夸赞点提及率对照；竞品同样高频的增益点会降级为标配型，确保差异化判断可靠。</div>
'''

# ---------- 差异化洞察：使用场景 / 用户画像（基于全部评价文本推断，多标签） ----------
SCEN = [
    ('手办/模型制作', ['手办','模型','人偶','高达','GK','兵人','微缩','恐龙','无牙仔','摆件'], '核心主流',
     '营销主阵地，把场景做透：首屏用发丝/符文/褶皱微距实拍，短视频做“图纸→成品”全过程，投放手办/GK/微缩圈层。'),
    ('新手入门/家用爱好', ['新手','小白','入门','第一次','家里','家用','孩子','小朋友','桌面'], '核心主流',
     '首单转化场景：强调开箱即用、自动调平与“第一锅就成功”，配新手陪跑教程，降低入门焦虑。'),
    ('工作室/批量生产', ['工作室','批量','接单','一天两锅','十锅','生意','客户'], '高价值商用',
     '效率与稳定性叙事：一天两锅、十锅不翻车、恒温与耗材成本，做批量案例、回本周期测算与商用团购。'),
    ('牙科/珠宝/专业领域', ['牙模','珠宝','首饰','蜡模','医疗','齿科'], '小众高价值',
     '细分人群长尾流量：高精度蜡模/牙模案例、专业渠道与长尾词投放，客单价与耗材复购高，粘性强。'),
    ('工业/功能件打样', ['零件','功能件','工业','工装','原型','结构件','测试件'], '观察培育',
     '以16K精度与材料兼容切入原型打样，补充尺寸精度实测内容。'),
    ('教学/创客', ['学生','创客','学校','课程','教学'], '观察培育',
     '教育套装与安全/气味防护指引，校园创客案例。'),
]
PERSONA = [
    ('模型/手办玩家', ['手办','高达','GK','兵人','人偶','玩家','微缩','收藏','游戏'], '圈层语境',
     '好评占比最高的人群：用玩家语境说话（16K还原、层纹、支撑、离型），做作品晒图赛与社群运营，泛投可收缩为圈层精准投放。'),
    ('新手/小白入门者', ['新手','小白','零起步','第一次','入门'], '增量人群',
     '好评逻辑是“怕失败→第一次就成功”：用真实新手证言+教程陪跑，解决“不会用”的核心顾虑。'),
    ('升级换机用户', ['拓竹','FDM','fdm','上一台','前一台','土星2','纵维','普罗森','竞品','某竹','Bambu'], '对比敏感',
     '好评逻辑是“对比之后的惊喜”：实测对比内容杀伤力最强——FDM换光固化、同树脂快一半、精度碾压，直接做对比图/对比视频。'),
    ('家庭/亲子/送礼人群', ['孩子','小朋友','家里','家用','年会','礼物','送礼','奖品'], '场景人群',
     '好评逻辑是“全家都能玩、送得体面”：亲子打印小恐龙、年会礼品场景，强调安全、气味防护与包装体面。'),
    ('工作室/商家', ['工作室','接单','批量','生意'], '商用人群',
     '好评逻辑是“稳定=赚钱”：突出成功率、效率与耗材成本，用批量生产案例说话。'),
    ('学生/创客', ['学生','创客','学校','课程'], '价格敏感',
     '好评逻辑是“预算内最强”：突出性价比、耗材兼容与教育优惠。'),
]
# 可在 config 中按品类覆盖: scen / persona / quad（结构同上方默认值）
SCEN = [tuple(x) for x in CFG.get('scen', SCEN)]
PERSONA = [tuple(x) for x in CFG.get('persona', PERSONA)]
QUAD = CFG.get('quad', {
    'core': [('16K打印精度', 'quality'), ('性价比与赠品', 'value'), ('倾斜离型·高速打印', 'speed'), ('售后·远程指导', 'service')],
    'opportunity': [('料盘加热恒温（低温十锅不翻车）', 'kw:heat'), ('兼容第三方/高粘耗材', 'kw:material'), ('智能诊断·主动提醒', 'kw:diag')],
    'baseline': [('自动调平·新手友好', 'easy'), ('运行稳定·成功率', 'kw:stable'), ('操作界面直观', 'kw:ui')],
    'hidden': [('气味与通风防护', 'kw:smell'), ('清洗/二次固化后处理', 'kw:post'), ('新手图文说明书', 'kw:manual'), ('AI监控·延时摄影', 'kw:ai'), ('包装防护与物流', 'kw:packlog')],
})

def tag_count(words):
    return sum(1 for r in DATA if any(w in r['content'] for w in words))
for r in DATA:
    r['scen'] = [i for i, (n, ws, _a, _b) in enumerate(SCEN) if any(w in r['content'] for w in ws)]
    r['persona'] = [i for i, (n, ws, _a, _b) in enumerate(PERSONA) if any(w in r['content'] for w in ws)]
# 象限自定义标签的关键词（用于点击筛选）
KWCHIPS = {
    'heat': ['加热','恒温','低温'],
    'material': ['兼容','范特斯','高粘','第三方','耗材'],
    'diag': ['智能诊断','诊断','提醒'],
    'stable': ['稳定','成功率','不翻车','没翻车','零翻车'],
    'ui': ['界面','触控屏','触摸屏'],
    'smell': ['气味','味道','通风','防毒面具'],
    'post': ['清洗','二次固化','后处理','铲件','固化机'],
    'manual': ['说明书','教程','教学','图文'],
    'ai': ['AI','摄像头','监控','延时'],
    'packlog': ['包装','物流','快递'],
}
KWCHIPS = CFG.get('kwchips', KWCHIPS)
kwchips_js = json.dumps(KWCHIPS, ensure_ascii=False)
scen_rows = ''
for i, (name, words, role, sug) in enumerate(SCEN):
    c = tag_count(words)
    scen_rows += f'<tr class="row-click" data-f="scen:{i}" title="点击筛选该场景评价"><td><b>{name}</b> <span class="row-go">›</span></td><td>{c}</td><td>{c/N*100:.1f}%</td><td><span class="role-tag">{role}</span></td><td class="sug-cell">{sug}</td></tr>\n'
persona_rows = ''
for i, (name, words, role, sug) in enumerate(PERSONA):
    c = tag_count(words)
    persona_rows += f'<tr class="row-click" data-f="persona:{i}" title="点击筛选该人群评价"><td><b>{name}</b> <span class="row-go">›</span></td><td>{c}</td><td>{c/N*100:.1f}%</td><td><span class="role-tag">{role}</span></td><td class="sug-cell">{sug}</td></tr>\n'
def catcnt(k):
    return sum(1 for r in DATA if k in r['cats'])

def quad_chips(items):
    out = ''
    for label, f in items:
        cnt = f'（{catcnt(f)}条）' if not f.startswith('kw:') else ''
        out += f'<span class="chip chip-click" data-f="{f}">{label}{cnt}</span>'
    return out

def top2(rows):
    ranked = sorted(rows, key=lambda x: -tag_count(x[1]))[:2]
    return '、'.join(f'{x[0]} {tag_count(x[1])} 条' for x in ranked)

insight_html = f'''
  <div class="sub-tabs">
    <button class="sub-tab active" data-ins="scen">使用场景</button>
    <button class="sub-tab" data-ins="role">用户身份</button>
    <button class="sub-tab" data-ins="quad">品类感知基线图</button>
    <span class="sub-tab-note">点击行 / 标签可筛选对应评价</span>
  </div>

  <div class="attr-panel ins-panel" id="ins-scen">
    <div class="attr-note">基于全部 {N} 条评价文本推断用途；一条评价可含多个场景，占比按总评价数计。</div>
    <table class="insight-table">
      <tr><th style="width:160px">场景</th><th style="width:70px">评价数</th><th style="width:60px">占比</th><th style="width:110px">定位</th><th>营销建议</th></tr>
      {scen_rows}
    </table>
    <div class="attr-foot">核心主流场景做透（{top2(SCEN)}）；小众高价值场景做长尾，是细分人群与长尾流量机会。</div>
  </div>

  <div class="attr-panel ins-panel" id="ins-role" style="display:none">
    <div class="attr-note">从评价内容反推身份；一条评价可含多个人群信号。</div>
    <table class="insight-table">
      <tr><th style="width:160px">身份</th><th style="width:70px">评价数</th><th style="width:60px">占比</th><th style="width:110px">类型</th><th>营销建议</th></tr>
      {persona_rows}
    </table>
    <div class="attr-foot">{top2(PERSONA)}信号最强：营销可从“泛人群”收缩到“精准人群”，用他们的语境和痛点说话，效率远高于泛投。</div>
  </div>

  <div class="attr-panel ins-panel" id="ins-quad" style="display:none">
    <div class="attr-note">横轴=用户提及频次（据 {N} 条评价统计）；纵轴=优势判读（据评价内容）；象限归属为分析判断。</div>
    <div class="quad">
      <div></div><div class="qh">用户高频提及</div><div class="qh">用户低频提及</div>
      <div class="qh">我方优势明显</div>
      <div class="qcell" style="background:#f0f9f1"><div class="qtitle" style="color:#188038">核心主打卖点 <span>放大、全渠道渗透</span></div>
        {quad_chips(QUAD['core'])}</div>
      <div class="qcell" style="background:#fff8ec"><div class="qtitle" style="color:#b06000">潜在差异化机会 <span>测试性投放，验证用户兴趣</span></div>
        {quad_chips(QUAD['opportunity'])}</div>
      <div class="qh">行业普遍做到</div>
      <div class="qcell" style="background:#f5f6f7"><div class="qtitle" style="color:#5f6368">品类基线 <span>不用重点说，但不能没有</span></div>
        {quad_chips(QUAD['baseline'])}</div>
      <div class="qcell" style="background:#eef4fd"><div class="qtitle" style="color:#0b57d0">隐性需求 <span>没人讲但用户在意，可做心智占位</span></div>
        {quad_chips(QUAD['hidden'])}</div>
    </div>
  </div>
'''
print('场景计数:', [(s[0], tag_count(s[1])) for s in SCEN])
print('画像计数:', [(p[0], tag_count(p[1])) for p in PERSONA])

data_js = json.dumps(DATA, ensure_ascii=False)

# 分类卡片骨架（数字由JS按平台动态计算）
cards_html = ''
for dim_name, (key, cname, color) in CAT.items():
    cards_html += f'<div class="cat-card" data-cat="{key}" style="--c:{color}"><div class="cc-num" style="color:{color}" id="c-{key}">-</div><div class="cc-name">{cname}</div></div>\n'
cards_html += '<div class="cat-card" data-cat="overall" style="--c:#5f6368"><div class="cc-num" style="color:#5f6368" id="c-overall">-</div><div class="cc-name">整体好评·泛认可</div></div>'
cards_html += '<div class="cat-card" data-cat="default" style="--c:#9aa0a6"><div class="cc-num" style="color:#9aa0a6" id="c-default">-</div><div class="cc-name">默认好评/无内容</div></div>'

# 工具栏按钮
tb = '<button class="active" data-f="all">全部</button>\n<button data-f="pos" style="--c:#34a853">好评</button>\n<button data-f="neg" style="--c:#d93025">差评</button>\n'
for dim_name, (key, cname, color) in CAT.items():
    tb += f'<button data-f="{key}" style="--c:{color}">{cname}</button>\n'
tb += '<button data-f="overall" style="--c:#5f6368">整体好评</button>\n'

# 合计概览数据
def stats_of(rs):
    neg = sum(1 for r in rs if r['neg'])
    img_r = sum(1 for r in rs if r['pics'])
    imgs = sum(len(r['pics']) for r in rs)
    return len(rs), len(rs)-neg, neg, img_r, imgs

t_all = stats_of(DATA)

def daterange(rs):
    isos = [r['iso'] for r in rs if r['iso']]
    return f'{min(isos)} ~ {max(isos)}' if isos else '-'

plat_rows = ''
diff_parts = []
for pl in PLATFORMS:
    rs = [r for r in DATA if r['p'] == pl['key']]
    t = stats_of(rs)
    plat_rows += (f'<tr><td>{pl["name"]}</td><td>{t[0]}</td><td>{t[1]}</td><td>{t[2]}</td>'
                  f'<td>{t[2]/t[0]*100:.1f}%</td><td>{t[3]}</td><td>{t[4]}</td><td>{daterange(rs)}</td></tr>\n')
    diff_parts.append(f'{pl.get("short", pl["name"])}差评率 {t[2]/t[0]*100:.1f}%、带图率 {t[3]/t[0]*100:.0f}%')
plat_sub = ' + '.join(f'{pl.get("short", pl["name"])} {PLAT_N[pl["key"]]} 条（按实际可加载数量统计）' for pl in PLATFORMS)
top_dims = sorted(CAT.values(), key=lambda v: -catcnt(v[0]))[:3]
top_text = f'认可度最高的卖点为<b>{top_dims[0][1]}</b>，其次是<b>{top_dims[1][1]}</b>、<b>{top_dims[2][1]}</b>。'
diff_text = '；'.join(diff_parts)
platform_buttons = f'<button class="active" data-p="all">合计 {N}</button>\n'
for pl in PLATFORMS:
    platform_buttons += f'    <button data-p="{pl["key"]}">{pl.get("short", pl["name"])} {PLAT_N[pl["key"]]}</button>\n'
footer_sources = '；'.join(
    f'{pl.get("short", pl["name"])} {pl.get("source", "")}（{PLAT_N[pl["key"]]}条）' for pl in PLATFORMS)
insight_nums = f'{len(SCEN)}+{len(PERSONA)}+4'
insight_sub = f'{len(SCEN)} 类使用场景 · {len(PERSONA)} 类用户身份 · 4 象限基线'

catmap_js = json.dumps({v[0]: {'name': v[1], 'color': v[2]} for v in CAT.values()}, ensure_ascii=False)
matcat_js = json.dumps({k: {'name': v[0], 'color': v[1], 'use': v[3]} for k, v in MAT_CATS.items()}, ensure_ascii=False)

html_doc = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="referrer" content="no-referrer">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>评价卖点归类 — {PRODUCT}</title>
<style>
  :root{{--bg:#f5f6f8;--card:#fff;--text:#22252a;--muted:#8a9099;--accent:#ff5000;--line:#eceef1;--tag:#f2f3f5}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.65}}
  .wrap{{max-width:1000px;margin:0 auto;padding:24px 16px 60px}}
  header.hero{{background:linear-gradient(135deg,#ff5000,#ff8a3c);color:#fff;border-radius:14px;padding:26px;margin-bottom:18px}}
  .hero h1{{font-size:20px;font-weight:700;line-height:1.4;margin-bottom:8px}}
  .hero p{{font-size:13px;opacity:.9}}
  h2.sec{{font-size:17px;margin:22px 0 12px}}
  .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}}
  .cat-card{{background:var(--card);border-radius:12px;padding:14px 16px;border-top:3px solid var(--c);cursor:pointer;transition:.15s}}
  .cat-card:hover{{transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,.08)}}
  .goal-cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:6px 0 20px}}
  @media (max-width:760px){{.goal-cards{{grid-template-columns:1fr}}}}
  .goal-card{{border-radius:14px;padding:18px 20px 22px;color:#fff;cursor:pointer;position:relative;transition:.18s}}
  .goal-card:hover{{transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,.12)}}
  .goal-card.active{{box-shadow:0 10px 24px rgba(0,0,0,.20);transform:translateY(-3px)}}
  .goal-card.active::before{{content:'';position:absolute;left:22px;right:22px;bottom:9px;height:3px;border-radius:2px;background:rgba(255,255,255,.85)}}
  .goal-card.active::after{{content:'当前展示';position:absolute;top:12px;right:14px;font-size:11px;background:rgba(255,255,255,.22);border-radius:6px;padding:2px 8px}}
  .gc-red{{background:linear-gradient(135deg,#e8564a,#d93025)}}
  .gc-green{{background:linear-gradient(135deg,#34a853,#188038)}}
  .gc-blue{{background:linear-gradient(135deg,#4a86e8,#0b57d0)}}
  .goal-card .gc-num{{font-size:36px;font-weight:800;line-height:1.1}}
  .goal-card .gc-name{{font-size:16px;font-weight:800;margin-top:4px}}
  .goal-card .gc-sub{{font-size:12px;opacity:.88;margin-top:4px}}
  .cat-card.big-pos{{background:linear-gradient(135deg,#34a853,#6fcf97)}}
  .cat-card.big-neg{{background:linear-gradient(135deg,#d93025,#f28b82)}}
  .cc-num{{font-size:24px;font-weight:800}}
  .cc-name{{font-size:13px;font-weight:600;margin-top:2px}}
  .platform-bar{{display:flex;gap:10px;margin:18px 0 4px;align-items:center}}
  .platform-bar button{{border:1px solid var(--line);background:var(--card);border-radius:10px;padding:10px 22px;font-size:14px;font-weight:600;color:#4a4f57;cursor:pointer;transition:.15s}}
  .platform-bar button.active[data-p="all"]{{background:#22252a;color:#fff;border-color:#22252a}}
  .platform-bar button.active[data-p="tmall"]{{background:#ff5000;color:#fff;border-color:#ff5000}}
  .platform-bar button.active[data-p="jd"]{{background:#e1251b;color:#fff;border-color:#e1251b}}
  .platform-bar .pb-sub{{font-size:12px;color:var(--muted)}}
  .toolbar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;position:sticky;top:0;z-index:10;background:var(--bg);padding:10px 0}}
  .toolbar button{{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:6px 14px;font-size:13px;color:#4a4f57;cursor:pointer}}
  .toolbar button.active{{background:var(--c,var(--accent));border-color:var(--c,var(--accent));color:#fff}}
  .count{{font-size:12px;color:var(--muted)}}
  .review{{background:var(--card);border-radius:14px;padding:18px 20px;margin-bottom:14px}}
  .r-head{{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}}
  .r-platform{{font-size:11px;font-weight:700;border-radius:6px;padding:2px 8px;color:#fff}}
  .p-tmall{{background:#ff5000}}
  .p-jd{{background:#e1251b}}
  .r-nick{{font-weight:600;font-size:14px}}
  .r-sku{{font-size:12px;color:var(--accent);background:#fff2ea;border-radius:6px;padding:2px 8px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  .r-date{{font-size:12px;color:var(--muted)}}
  .r-tags{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}}
  .r-tag{{font-size:11px;border-radius:6px;padding:2px 8px;color:#fff;background:var(--c)}}
  .r-content{{font-size:14.5px;margin-bottom:10px}}
  .r-empty{{font-size:13px;color:var(--muted)}}
  .r-pics{{display:flex;flex-wrap:wrap;gap:8px}}
  .r-pics a{{display:block;width:110px;height:110px;border-radius:8px;overflow:hidden;background:var(--tag);flex:0 0 auto}}
  .r-pics img{{width:100%;height:100%;object-fit:cover;display:block;cursor:zoom-in;transition:.2s}}
  .r-pics img:hover{{transform:scale(1.04)}}
  .neg-card{{border:1px solid #fdd8d6}}
  .neg-badge{{font-size:11px;color:#d93025;border:1px solid #f3b3b0;border-radius:6px;padding:1px 8px}}
  .attr-panel{{background:var(--card);border-radius:14px;padding:20px 22px;margin:6px 0 16px}}
  .attr-panel h2{{font-size:16px;margin-bottom:4px}}
  .attr-panel .attr-note{{font-size:12px;color:var(--muted);margin-bottom:14px}}
  .attr-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:12px}}
  .attr-card{{border:1px solid var(--line);border-left:4px solid var(--ac);border-radius:10px;padding:14px 16px;cursor:pointer;transition:.15s}}
  .attr-card:hover{{box-shadow:0 4px 12px rgba(0,0,0,.08)}}
  .attr-card.active{{background:#fff8f6;border-color:var(--ac);box-shadow:0 4px 12px rgba(0,0,0,.08)}}
  .attr-card .ac-head{{display:flex;align-items:baseline;gap:8px;margin-bottom:4px}}
  .attr-card .ac-num{{font-size:26px;font-weight:800;color:var(--ac)}}
  .attr-card .ac-name{{font-size:14px;font-weight:700}}
  .attr-card .ac-def{{font-size:12px;color:var(--muted);margin-bottom:8px}}
  .attr-card .ac-sug{{font-size:12.5px;color:#3a3f46;background:#f7f8fa;border-radius:8px;padding:8px 10px}}
  .attr-foot{{font-size:12px;color:var(--muted);margin-top:12px}}
  mark.hl-vocab{{background:#fff1e0;color:#c2570a;padding:0 2px;border-radius:3px}}
  mark.hl-metaphor{{background:#fde7f3;color:#c2185b;padding:0 2px;border-radius:3px}}
  mark.hl-scene{{background:#e3f0ff;color:#0b57d0;padding:0 2px;border-radius:3px}}
  .hl-legend{{display:inline-flex;gap:10px;margin-left:8px}}
  .hl-legend i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:3px}}
  .mat-badge{{font-size:11px;color:#0b57d0;border:1px solid #a8c7fa;border-radius:6px;padding:1px 8px}}
  .insight-table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}}
  .insight-table th{{text-align:left;color:var(--muted);font-weight:600;padding:8px 10px;border-bottom:2px solid var(--line);white-space:nowrap}}
  .insight-table td{{padding:10px;border-bottom:1px solid var(--line);vertical-align:top}}
  .sug-cell{{color:#3a3f46;font-size:12.5px}}
  .role-tag{{display:inline-block;font-size:11px;background:#eef2ff;color:#3b5bdb;border-radius:6px;padding:2px 8px;white-space:nowrap}}
  .quad{{display:grid;grid-template-columns:110px 1fr 1fr;gap:10px;margin-top:12px}}
  .qh{{display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;color:#3a3f46;text-align:center}}
  .qcell{{border:1px solid var(--line);border-radius:10px;padding:14px}}
  .qtitle{{font-weight:800;font-size:14px;margin-bottom:10px}}
  .qtitle span{{font-weight:400;font-size:11.5px;color:var(--muted);margin-left:6px}}
  .chip{{display:inline-block;background:#fff;border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:12px;margin:0 6px 6px 0;color:#3a3f46}}
  .chip-click{{cursor:pointer}}
  .chip-click:hover{{border-color:var(--accent);color:var(--accent);box-shadow:0 2px 6px rgba(0,0,0,.08)}}
  .row-click{{cursor:pointer}}
  .row-click:hover td{{background:#f7f8fa}}
  .row-go{{color:var(--accent);font-weight:800}}
  .vid-badge{{font-size:11px;color:#1a73e8;border:1px solid #bcd4f7;border-radius:6px;padding:1px 8px}}
  .insight{{background:var(--card);border-radius:14px;padding:18px 22px;margin-bottom:18px;font-size:14px}}
  .insight h2{{font-size:16px;margin-bottom:10px}}
  .insight p{{margin-bottom:8px;color:#3a3f46}}
  .insight table{{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}}
  .insight th,.insight td{{border:1px solid var(--line);padding:6px 10px;text-align:center}}
  .insight th{{background:#f7f8fa;font-weight:600}}
  .insight td:first-child,.insight th:first-child{{text-align:left}}
  footer{{margin-top:26px;text-align:center;font-size:12px;color:var(--muted)}}
  .goal-sec{{margin:26px 0 18px;border-radius:16px;padding:20px 22px;background:var(--card);border:1px solid var(--line)}}
  .goal-red{{border-top:4px solid #d93025}}
  .goal-green{{border-top:4px solid #188038}}
  .goal-blue{{border-top:4px solid #0b57d0}}
  .goal-head{{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px}}
  .goal-badge{{font-size:12px;font-weight:800;color:#fff;border-radius:8px;padding:4px 12px;white-space:nowrap}}
  .goal-red .goal-badge{{background:#d93025}}
  .goal-green .goal-badge{{background:#188038}}
  .goal-blue .goal-badge{{background:#0b57d0}}
  .goal-head h2{{font-size:19px;margin:0}}
  .goal-sub{{font-size:12.5px;color:var(--muted);margin:0 0 12px}}
  .goal-btn{{margin-left:auto;border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 16px;font-size:12.5px;cursor:pointer;color:#3a3f46}}
  .goal-btn:hover{{border-color:var(--accent);color:var(--accent)}}
  .goal-sec .attr-panel{{padding:12px 0 0;margin:0;background:transparent}}
  .b-grid{{display:grid;grid-template-columns:minmax(0,2.1fr) minmax(250px,1fr);gap:16px;align-items:start}}
  @media (max-width:900px){{.b-grid{{grid-template-columns:1fr}}}}
  .ph-card{{border:1.5px dashed #c8cdd4;border-radius:10px;padding:18px;background:#fafbfc}}
  .ph-title{{font-size:14px;font-weight:700;color:#5f6368;margin-bottom:8px}}
  .ph-tag{{display:inline-block;font-size:11px;background:#eceff1;color:#78909c;border-radius:6px;padding:2px 8px;margin-left:6px}}
  .ph-desc{{font-size:12.5px;color:var(--muted);line-height:1.8}}
  #matGrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
  @media (max-width:1100px){{#matGrid{{grid-template-columns:repeat(2,1fr)}}}}
  .mat-card{{padding:12px 14px}}
  .mat-card .ac-num{{font-size:24px}}
  .mat-card .ac-desc{{font-size:11.5px;margin-top:6px}}
  .sub-tabs{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:4px 0 14px}}
  .sub-tab{{border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 18px;font-size:13px;cursor:pointer;color:#3a3f46}}
  .sub-tab:hover{{border-color:var(--accent);color:var(--accent)}}
  .sub-tab.active{{background:#0b57d0;border-color:#0b57d0;color:#fff;font-weight:700}}
  .sub-tab-g.active{{background:#188038;border-color:#188038}}
  .sub-tab-note{{margin-left:auto;font-size:12px;color:var(--muted)}}
  .ins-panel{{padding-top:4px}}
  .insight-table td:nth-child(2),.insight-table th:nth-child(2){{text-align:right;font-variant-numeric:tabular-nums}}
  .insight-table td:nth-child(3),.insight-table th:nth-child(3){{text-align:right;color:var(--muted)}}
  .insight-table tr:nth-child(even) td{{background:#fafbfc}}
  .insight-table .sug-cell{{line-height:1.75}}
  .mp-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}}
  @media (max-width:900px){{.mp-grid{{grid-template-columns:1fr}}}}
  .mp-col{{border:1px solid var(--line);border-top:3px solid var(--ac);border-radius:10px;padding:12px 14px;background:#fff}}
  .mp-title{{font-size:13px;font-weight:800;margin-bottom:8px}}
  .mp-title span{{font-weight:400;font-size:11px;color:var(--muted)}}
  .mp-row{{display:flex;justify-content:space-between;gap:10px;font-size:12.5px;padding:5px 0;border-bottom:1px dashed var(--line)}}
  .mp-row:last-child{{border-bottom:none}}
  .mp-row b{{color:var(--ac);font-variant-numeric:tabular-nums}}
  .comp-head{{font-size:14px;font-weight:800;margin:20px 0 10px}}
  .comp-table td{{font-size:12.5px}}
  .verdict{{display:inline-block;font-size:11.5px;border:1px solid;border-radius:6px;padding:2px 8px;white-space:nowrap}}
  .lightbox{{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:99;cursor:zoom-out}}
  .lightbox img{{max-width:92vw;max-height:92vh;border-radius:8px}}
{platform_css}
  @media (max-width:600px){{.r-pics a{{width:31vw;height:31vw}}}}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <h1>{PRODUCT} — 评价卖点归类分析</h1>
    <p>共整理 {N} 条评价：{plat_sub} · 按卖点认可维度分类 · 一条评价可属于多个类别 · {TODAY}</p>
  </header>

  <div class="insight">
    <h2>归类速览</h2>
    <p>合计 <b>{t_all[0]}</b> 条评价：好评 <b>{t_all[1]}</b> 条（{t_all[1]/t_all[0]*100:.1f}%）、差评 <b>{t_all[2]}</b> 条（{t_all[2]/t_all[0]*100:.1f}%）；带图评价 {t_all[3]} 条、实拍图 {t_all[4]} 张。{top_text}</p>
    <table>
      <tr><th>平台</th><th>评价数</th><th>好评</th><th>差评</th><th>差评率</th><th>带图评价</th><th>图片数</th><th>时间跨度</th></tr>
{plat_rows}      <tr><td><b>合计</b></td><td><b>{t_all[0]}</b></td><td><b>{t_all[1]}</b></td><td><b>{t_all[2]}</b></td><td><b>{t_all[2]/t_all[0]*100:.1f}%</b></td><td><b>{t_all[3]}</b></td><td><b>{t_all[4]}</b></td><td>{daterange(DATA)}</td></tr>
    </table>
    <p><b>平台差异</b>：{diff_text}。差评口径=评价内容明确提到不好；好评动因与素材提取规则见各模块说明。</p>
  </div>

  <div class="platform-bar">
    {platform_buttons}    <span class="pb-sub">切换平台后，下方分布与评价列表同步更新</span>
  </div>

  <div class="goal-cards">
    <div class="goal-card gc-red active" data-goal="neg">
      <div class="gc-num" id="c-neg">-</div>
      <div class="gc-name">差评止损</div>
      <div class="gc-sub" id="s-neg"></div>
      <div class="gc-sub">差评归因分层 · 点击查看模块 ▾</div>
    </div>
    <div class="goal-card gc-green" data-goal="pos">
      <div class="gc-num" id="c-pos">-</div>
      <div class="gc-name">好评增效</div>
      <div class="gc-sub" id="s-pos"></div>
      <div class="gc-sub">语言素材 + 好评动因 · 点击查看模块 ▾</div>
    </div>
    <div class="goal-card gc-blue" data-goal="insight">
      <div class="gc-num">{insight_nums}</div>
      <div class="gc-name">洞察增收</div>
      <div class="gc-sub">{insight_sub}</div>
      <div class="gc-sub">场景 / 身份 / 品类基线 · 点击查看模块 ▾</div>
    </div>
  </div>

  <h2 class="sec">卖点认可分布</h2>
  <div class="cards">
{cards_html}
  </div>
  <div id="goalPanels">
  <div class="goal-sec goal-red" id="goal-neg">
    <div class="goal-head"><span class="goal-badge">① 差评止损</span><h2>差评归因分层</h2><button class="goal-btn" data-f="neg">查看全部差评 ›</button></div>
    <p class="goal-sub">先止住流失：硬缺陷与服务问题立刻整改，预期不符前置真实信息，场景错配明确使用边界，减少新差评与舆情。</p>
    <div class="attr-panel" id="attrPanel">
      <div class="attr-note" id="attrNote"></div>
      <div class="attr-grid" id="attrGrid"></div>
      <div class="attr-foot">营销用法：以上四类若在竞品评价中高频出现、而我们能规避，即为详情页可直接对标的核心打击点。</div>
    </div>
  </div>

  <div class="goal-sec goal-green" id="goal-pos" style="display:none">
    <div class="goal-head"><span class="goal-badge">② 好评增效</span><h2>让好评变成素材与转化</h2><button class="goal-btn" data-f="pos">查看全部好评 ›</button></div>
    <p class="goal-sub">把真实好评转成可直接使用的营销语言素材；后续接入好评动因拆分，指导卖点优先级与投放。</p>
    <div class="sub-tabs">
      <button class="sub-tab sub-tab-g active" data-g="mat">提取语言素材</button>
      <button class="sub-tab sub-tab-g" data-g="motive">拆分好评动因</button>
      <span class="sub-tab-note">点击素材分类可筛选对应好评并高亮</span>
    </div>
    <div class="attr-panel ins-panel" id="pos-mat">
      <div class="attr-note" id="matNote"></div>
      <div class="attr-grid" id="matGrid"></div>
      <div class="attr-foot">用法：点击分类查看对应好评，正文已高亮 <mark class="hl-vocab">精确数据</mark> <mark class="hl-metaphor">比喻表达</mark> <mark class="hl-scene">画面场景</mark>，可直接用于营销图片与视频创作。</div>
    </div>
    <div class="attr-panel ins-panel" id="pos-motive" style="display:none">
      <div class="attr-note" id="motiveNote"></div>
      <div class="attr-grid" id="motiveGrid"></div>
      <div class="mp-grid">{mp_cols}</div>
{comp_html}
      <div class="attr-foot"><b>使用建议</b>：增益型=差异化卖点，做主图/短视频核心表达；决策验证型=转化杀器，点击卡片筛出原话，原封不动用于详情页、主图、直播间。</div>
    </div>
  </div>

  <div class="goal-sec goal-blue" id="goal-insight" style="display:none">
    <div class="goal-head"><span class="goal-badge">③ 洞察增收</span><h2>从场景、人群与品类基线找增量</h2></div>
    <p class="goal-sub">核心主流场景做透、小众高价值场景做长尾；用精准人群语境替代泛投；四象限指导卖点表达与心智占位。</p>
{insight_html}
  </div>

  </div>
  <h2 class="sec">评价明细</h2>
  <div class="toolbar">
{tb}
    <span class="count" id="cnt"></span>
  </div>

  <div id="list"></div>

  <footer>数据来源：{footer_sources}；图片为平台CDN直链，需联网查看；差评口径=评价内容明确提到不好。</footer>
</div>

<div class="lightbox" id="lb"><img id="lbimg" src="" alt=""></div>

<script>
const DATA = {data_js};
const CATMAP = {catmap_js};
const MATCAT = {matcat_js};
const MOTCAT = {motivecat_js};
const KWCHIPS = {kwchips_js};
const PLATMETA = {platmeta_js};
CATMAP['overall'] = {{name:'整体好评·泛认可', color:'#5f6368'}};
CATMAP['default'] = {{name:'默认好评/无内容', color:'#9aa0a6'}};
const listEl = document.getElementById('list');
const cntEl = document.getElementById('cnt');
let filter = 'all';
let platform = 'all';

function curData(){{ return platform==='all' ? DATA : DATA.filter(r=>r.p===platform); }}
function updateCards(){{
  const rs = curData();
  const neg = rs.filter(r=>r.neg).length, pos = rs.length-neg;
  document.getElementById('c-pos').textContent = pos;
  document.getElementById('s-pos').textContent = '无负面反馈 · 占比 '+(pos/rs.length*100).toFixed(1)+'%';
  document.getElementById('c-neg').textContent = neg;
  document.getElementById('s-neg').textContent = '明确抱怨 · 占比 '+(neg/rs.length*100).toFixed(1)+'%';
  Object.keys(CATMAP).forEach(k=>{{
    const el = document.getElementById('c-'+k);
    if(el) el.textContent = rs.filter(r=>r.cats.includes(k)).length;
  }});
}}
const ATTR = [
  {{k:'defect', name:'硬缺陷型差评', color:'#d93025', def:'产品本身的质量、功能故障（损坏、异响、失灵、故障、失败率高等）。', sug:'高频出现需立刻解决：定位高发部件与品控环节，提供快速维修/换新与远程指导；低频偶发属品控概率问题，营销价值不大。'}},
  {{k:'service', name:'服务型差评', color:'#e8710a', def:'物流慢、客服态度差、售后不处理（不支持退换、拖延、推诿）。', sug:'常与硬缺陷伴生、需同步整改：明确退换货规则与处理时限、首问负责，杜绝"不支持退换/推诿"类表达。'}},
  {{k:'expect', name:'预期不符型差评', color:'#1a73e8', def:'产品没问题，但和用户想的不一样（宣传放大了预期、功能与想象不符）。', sug:'最有营销价值：详情页前置真实信息，如实说明使用要求与功能边界，避免放大预期、满足真实需求。'}},
  {{k:'scene', name:'场景错配型差评', color:'#8e7cc3', def:'用户买错了、不会用导致体验差（超出适用场景、操作不当、缺少指导）。', sug:'营销里明确"适合什么、不适合什么"：前置使用边界与新手教程，既减少差评，也显得专业。'}}
];
function renderAttr(rs){{
  const panel = document.getElementById('attrPanel');
  const negs = rs.filter(r=>r.neg);
  const counts = {{}};
  negs.forEach(r=>{{ (r.negtype||[]).forEach(t=>{{ counts[t]=(counts[t]||0)+1; }}); }});
  document.getElementById('attrNote').textContent = `当前平台 ${{negs.length}} 条差评，按问题性质多标签归因（一条差评可归入多个类型，点击卡片筛选对应差评明细）`;
  document.getElementById('attrGrid').innerHTML = ATTR.map(a=>{{
    const n = counts[a.k]||0;
    const active = filter==='neg:'+a.k ? ' active' : '';
    return `<div class="attr-card${{active}}" data-at="${{a.k}}" style="--ac:${{a.color}}">
      <div class="ac-head"><span class="ac-num">${{n}}</span><span class="ac-name">${{a.name}}</span><span style="font-size:12px;color:var(--muted)">${{negs.length?(n/negs.length*100).toFixed(0):0}}%</span></div>
      <div class="ac-def">${{a.def}}</div>
      <div class="ac-sug"><b>建议：</b>${{a.sug}}</div>
    </div>`;
  }}).join('');
  document.querySelectorAll('.attr-card').forEach(c=>c.addEventListener('click',()=>{{
    setFilter(filter==='neg:'+c.dataset.at ? 'neg' : 'neg:'+c.dataset.at);
    window.scrollTo({{top: document.querySelector('.toolbar').offsetTop - 6, behavior:'smooth'}});
  }}));
  panel.style.display = 'block';
}}
function renderMat(rs){{
  const mats = rs.filter(r=>r.material);
  const counts = {{}};
  mats.forEach(r=>{{ r.material.forEach(t=>{{ counts[t]=(counts[t]||0)+1; }}); }});
  document.getElementById('matNote').innerHTML = `当前平台 ${{rs.filter(r=>!r.neg).length}} 条好评中提取 <b>${{mats.length}}</b> 条有画面感、精确表达的评价（剔除笼统夸赞；点击分类筛选明细）`;
  document.getElementById('matGrid').innerHTML = Object.entries(MATCAT).map(([k,a])=>{{
    const n = counts[k]||0;
    const active = filter==='mat:'+k ? ' active' : '';
    return `<div class="attr-card mat-card${{active}}" data-mat="${{k}}" style="--ac:${{a.color}}">
      <div class="ac-head"><span class="ac-num">${{n}}</span><span class="ac-name">${{a.name}}</span></div>
      <div class="ac-def">${{a.use}}</div>
    </div>`;
  }}).join('');
  document.querySelectorAll('#matGrid .attr-card').forEach(c=>c.addEventListener('click',()=>{{
    setFilter(filter==='mat:'+c.dataset.mat ? 'pos' : 'mat:'+c.dataset.mat);
    window.scrollTo({{top: document.querySelector('.toolbar').offsetTop - 6, behavior:'smooth'}});
  }}));
}}
function escapeHtml(s){{ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}
function escapeRegExp(s){{ return s.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&'); }}
function highlight(r){{
  let txt = escapeHtml(r.content);
  const ps = (r.phrases||[]).slice().sort((a,b)=>b.t.length-a.t.length);
  if(!ps.length) return txt;
  const map = {{}};
  ps.forEach(p=>{{ map[escapeHtml(p.t)] = p.k; }});
  const re = new RegExp(ps.map(p=>escapeRegExp(escapeHtml(p.t))).join('|'),'g');
  return txt.replace(re, m=>`<mark class="hl-${{map[m]}}">${{m}}</mark>`);
}}
function renderMotive(rs){{
  const poss = rs.filter(r=>!r.neg);
  const counts = {{}};
  poss.forEach(r=>{{ (r.motive||[]).forEach(t=>{{ counts[t]=(counts[t]||0)+1; }}); }});
  document.getElementById('motiveNote').innerHTML = `当前平台 ${{poss.length}} 条好评按夸赞动因归类（一条好评可含多个动因，点击卡片筛选原话；下方夸赞点频率为合计口径）`;
  document.getElementById('motiveGrid').innerHTML = Object.entries(MOTCAT).map(([k,a])=>{{
    const n = counts[k]||0;
    const pct = poss.length ? (n/poss.length*100).toFixed(0)+'%' : '0%';
    const active = filter==='motive:'+k ? ' active' : '';
    return `<div class="attr-card${{active}}" data-motive="${{k}}" style="--ac:${{a.color}}">
      <div class="ac-head"><span class="ac-num">${{n}}</span><span class="ac-name">${{a.name}}</span><span class="ac-pct">${{pct}}</span></div>
      <div class="ac-def">${{a.desc}}</div>
      <div class="ac-advice">${{a.advice}}</div></div>`;
  }}).join('');
  document.querySelectorAll('#motiveGrid .attr-card').forEach(c=>c.addEventListener('click',()=>{{
    setFilter(filter==='motive:'+c.dataset.motive ? 'pos' : 'motive:'+c.dataset.motive);
    window.scrollTo({{top: document.querySelector('.toolbar').offsetTop - 6, behavior:'smooth'}});
  }}));
}}
function render(){{
  const rs = curData();
  let shown = 0, html = '';
  rs.forEach((r,i)=>{{
    if(filter.startsWith('neg:')){{
      const k = filter.slice(4);
      if(!r.neg || !(r.negtype||[]).includes(k)) return;
    }} else if(filter.startsWith('mat:')){{
      const k = filter.slice(4);
      if(!r.material || !r.material.includes(k)) return;
    }} else if(filter.startsWith('motive:')){{
      const k = filter.slice(7);
      if(!r.motive || !r.motive.includes(k)) return;
    }} else if(filter.startsWith('scen:')){{
      const i = +filter.slice(5);
      if(!r.scen || !r.scen.includes(i)) return;
    }} else if(filter.startsWith('persona:')){{
      const i = +filter.slice(8);
      if(!r.persona || !r.persona.includes(i)) return;
    }} else if(filter.startsWith('kw:')){{
      const kws = KWCHIPS[filter.slice(3)] || [];
      if(!kws.some(w=>r.content.includes(w))) return;
    }} else {{
      if(filter==='pos' && r.neg) return;
      if(filter==='neg' && !r.neg) return;
      if(filter!=='all' && filter!=='pos' && filter!=='neg' && !r.cats.includes(filter)) return;
    }}
    shown++;
    const tags = r.cats.filter(c=>c!=='default'&&c!=='overall').map(c=>{{
      const m = CATMAP[c] || {{name:c, color:'#999'}};
      return `<span class="r-tag" style="background:${{m.color}}">${{m.name}}</span>`;
    }}).join('');
    const negb = r.neg ? '<span class="neg-badge">差评</span>' + (r.negtype||[]).map(t=>{{
      const a = ATTR.find(x=>x.k===t) || ATTR[0];
      return `<span class="neg-badge" style="color:${{a.color}};border-color:${{a.color}}">${{a.name.replace('差评','')}}</span>`;
    }}).join('') : '';
    const vidb = r.video ? '<span class="vid-badge">含视频</span>' : '';
    const pname = (PLATMETA[r.p]||{{name:r.p}}).name;
    const pics = r.pics.map((u,j)=>`<a href="${{r.bigs[j]||u}}" target="_blank" rel="noopener"><img loading="lazy" src="${{u}}" alt="评价图"></a>`).join('');
    const isEmpty = r.content.length < 6;
    const content = isEmpty ? `<span class="r-empty">该用户未填写评价内容</span>` : (filter.startsWith('mat:') ? highlight(r) : r.content);
    const matb = r.material ? '<span class="mat-badge">语言素材</span>' : '';
    html += `<div class="review ${{r.neg?'neg-card':''}}">
      <div class="r-head"><span class="r-platform p-${{r.p}}">${{pname}}</span><span class="r-nick">${{r.nick}}</span><span class="r-sku" title="${{r.sku}}">${{r.sku||''}}</span><span class="r-date">${{r.date}}</span>${{negb}}${{vidb}}${{matb}}</div>
      ${{tags?`<div class="r-tags">${{tags}}</div>`:''}}
      <div class="r-content">${{content}}</div>
      ${{pics?`<div class="r-pics">${{pics}}</div>`:''}}
    </div>`;
  }});
  listEl.innerHTML = shown ? html : '<div class="review"><span class="r-empty">该分类下暂无评价</span></div>';
  cntEl.textContent = `显示 ${{shown}}/${{rs.length}} 条`;
  updateCards();
  renderAttr(rs);
  renderMat(rs);
  renderMotive(rs);
}}
function setFilter(f){{
  filter = f;
  document.querySelectorAll('.toolbar button').forEach(b=>b.classList.toggle('active', b.dataset.f===f || (f.startsWith('neg:') && b.dataset.f==='neg') || ((f.startsWith('mat:')||f.startsWith('motive:')) && b.dataset.f==='pos')));
  render();
}}
document.querySelectorAll('.toolbar button').forEach(b=>b.addEventListener('click',()=>setFilter(b.dataset.f)));
document.querySelectorAll('.cat-card').forEach(c=>c.addEventListener('click',()=>{{
  setFilter(c.dataset.cat);
  window.scrollTo({{top: document.querySelector('.toolbar').offsetTop - 6, behavior:'smooth'}});
}}));
function showGoal(g){{
  ['neg','pos','insight'].forEach(k=>{{
    document.getElementById('goal-'+k).style.display = (k===g) ? 'block' : 'none';
  }});
  document.querySelectorAll('.goal-card').forEach(c=>c.classList.toggle('active', c.dataset.goal===g));
}}
document.querySelectorAll('.goal-card').forEach(c=>c.addEventListener('click',()=>{{
  showGoal(c.dataset.goal);
  window.scrollTo({{top: document.getElementById('goalPanels').offsetTop - 10, behavior:'smooth'}});
}}));
document.querySelectorAll('.sub-tab').forEach(t=>t.addEventListener('click',()=>{{
  ['scen','role','quad'].forEach(k=>{{
    document.getElementById('ins-'+k).style.display = (k===t.dataset.ins) ? 'block' : 'none';
  }});
  document.querySelectorAll('.sub-tab').forEach(x=>x.classList.toggle('active', x===t));
}}));
document.querySelectorAll('.sub-tab-g').forEach(t=>t.addEventListener('click',()=>{{
  ['mat','motive'].forEach(k=>{{
    document.getElementById('pos-'+k).style.display = (k===t.dataset.g) ? 'block' : 'none';
  }});
  document.querySelectorAll('.sub-tab-g').forEach(x=>x.classList.toggle('active', x===t));
}}));
document.querySelectorAll('.row-click, .chip-click, .goal-btn').forEach(c=>c.addEventListener('click',()=>{{
  setFilter(c.dataset.f);
  window.scrollTo({{top: document.querySelector('.toolbar').offsetTop - 6, behavior:'smooth'}});
}}));
document.querySelectorAll('.platform-bar button').forEach(b=>b.addEventListener('click',()=>{{
  platform = b.dataset.p;
  document.querySelectorAll('.platform-bar button').forEach(x=>x.classList.toggle('active', x===b));
  render();
}}));
const lb=document.getElementById('lb'),lbimg=document.getElementById('lbimg');
document.addEventListener('click',e=>{{
  if(e.target.tagName==='IMG' && e.target.closest('.r-pics')){{e.preventDefault();lbimg.src=e.target.parentElement.href;lb.style.display='flex'}}
}});
lb.addEventListener('click',()=>{{lb.style.display='none';lbimg.src=''}});
render();
</script>
</body>
</html>'''

open(OUT, 'w', encoding='utf-8').write(html_doc)
print('双平台报告已生成:', OUT, len(html_doc), '字符; 评价数', N)
