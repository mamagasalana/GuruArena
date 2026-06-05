from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from template.template_20260424_2026 import (
    InstrumentTag,
    TradingInstrument,
)


class EvidenceItem(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        description="Transcript 中真实存在的连续原文子串，逐字复制，不得改写"
    )
    summary: str = Field(
        ...,
        min_length=1,
        description="用中文简要解释该原文片段在该维度下表达了什么含义（1-2句），"
                     "说明主持人的观点、判断或语境，供下游信号分类使用"
    )


class SignalEvidenceBase(BaseModel):
    instrument: List[str] = Field(
        ...,
        description="必须直接复制 Helper 对应项的 instrument 列表"
    )
    instrument_normalized: str = Field(
        ...,
        description="必须直接复制 Helper 对应项的 instrument_normalized"
    )
    direction_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="表达价格方向预期（上涨/下跌/反弹/回调/机会/风险等）的证据项"
    )
    action_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="表达交易动作（买卖/开仓/平仓/减仓/停损等）的证据项"
    )
    price_level_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="表达价格位置或估值（高位/低位/高峰/底部/颈线/跌过头等）的证据项"
    )
    technical_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="表达技术分析或形态（突破/跌破/头肩顶/月线转强等）的证据项"
    )
    conditional_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="表达条件或假设（如果/假如/一旦等）的证据项"
    )
    rhetoric_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="表达特殊修辞或语气（反问、反向思考、讽刺、反话等）的证据项"
    )
    negation_uncertainty_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="表达否定（不/不是/并非）或不确定性（可能/也许/不确定）的证据项"
    )
    other_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="无法归入以上 7 个维度的其他相关证据项（仅在前述维度均不适用时使用，勿滥用）"
    )
    invalid: bool = Field(
        default=False,
        description="该标的在 Transcript 中的提及不构成可用的交易证据。"
                     "满足以下任一条件时应设为 True：仅提及/枚举/一笔带过；"
                     "作为历史举例或类比（如 GE 分拆作为过去事件举例）；"
                     "该标的在文中充当信息源/发布方（如机构发布报告、媒体来源）而非被讨论的交易对象；主持人引用外部观点来支持自己的判断不在此列，本项仅针对标的本身是信源的情况"
                     "描述过往现象而非当前观点；"
                     "属于明显错配或非交易语境。"
                     "设为 True 时各 evidence 维度可留空，下游将跳过该标的的信号分类"
    )
    invalid_reason: str = Field(
        ...,
        description="当 invalid=True 时，简短说明为何该提及不构成交易证据（1 句即可）；invalid=False 时填 null"
    )

class SignalEvidence(BaseModel):
    signals: List[SignalEvidenceBase] = Field(
        default_factory=list,
        description="每个 helper item 对应一个 SignalEvidenceBase 对象"
    )


SCHEMA_EVIDENCE_EXTRACT = r"""
SCHEMA_VERSION=2026-06-01T16:30:00
你是中文财经分析师，负责从财经节目逐字稿中提取关于特定标的的多维度证据。

输入有两个块：
- Transcript：完整逐字稿，主证据
- Helper：候选标的与辅助 OCR

你的任务：
- 对 `Helper.instruments` 中每个 helper item，找出 Transcript 中所有与该标的相关的评论。
- 将评论按以下维度分类，每个维度输出对应的原文证据片段（必须是连续原文子串，逐字复制）。
- 仅陈述已发生的市场事实，若上下文不含主持人的判断、预期、分析或操作倾向，则不应提取为证据。注意：事实性片段本身若被主持人用于支撑其分析或交易结论，仍应提取；本规则针对的是整段评论缺乏主持人观点的情况，而非单一片段的字面语义。

维度定义：
1. `direction_evidence`：表达价格方向预期（上涨/下跌/反弹/回调/机会/风险等）。
2. `action_evidence`：表达交易动作（买卖/开仓/平仓/减仓/停损等）。
3. `price_level_evidence`：表达价格位置或估值（高位/低位/高峰/底部/颈线/跌过头等）。
4. `technical_evidence`：表达技术分析或形态（突破/跌破/头肩顶/月线转强等）。
5. `conditional_evidence`：表达条件或假设（如果/假如/一旦等）。
6. `rhetoric_evidence`：表达特殊修辞或语气（反问、反向思考、讽刺、反话等）。
7. `negation_uncertainty_evidence`：表达否定（不/不是/并非）或不确定性（可能/也许/不确定）。
8. `other_evidence`：无法归入以上 7 个维度的其他相关证据。仅在前述维度均不适用时使用，勿滥用。

维度归类规则：若同一原文片段可归入多个维度，选择最具体、最贴近该片段核心含义的维度，不得将同一条原文片段重复放入多个维度。

每条证据由两个字段组成：
- `text`：Transcript 中真实存在的连续原文子串，逐字复制，不得改写。
- `summary`：用中文简要解释该原文片段在该维度下表达了什么含义（1-2句），说明主持人的观点、判断或语境，方便下游信号分类使用。

输出约束：
1. 【重要】先判断每条 helper item 的提及是否构成有效交易证据。若该标的在 Transcript 中的提及属于以下情况，应将 `invalid` 设为 True，且 `invalid_reason` 给出简短原因，各 evidence 维度留空：
   - 仅提及/枚举/一笔带过，未展开讨论
   - 作为历史举例、类比或背景材料
   - 该标的在文中充当信息源/发布方（如机构发布报告、媒体来源），而非被讨论的交易对象（注意：主持人引用外部观点来支撑自己的判断不在此列，本项仅针对标的本身是信源的情况）
   - 描述过往现象，并非表达当前观点或预期
   - 明显错配（如把公司名当成产品名提及）或非交易语境
   invalid=True 与任何非空 evidence 维度互斥，绝不可同时出现。
2. 必须覆盖 `Helper.instruments` 中的全部 helper item。
3. 每个 helper item 输出一个对象，包含上述 8 个证据列表（未找到证据的维度保持空数组）。
4. `instrument` 和 `instrument_normalized` 必须直接复制 Helper 对应项，不得改写。
5. 每一条证据的 `text` 字段必须是 Transcript 中真实存在的连续原文子串，逐字复制，不得改写、拼接或省略；`summary` 字段用中文解释该证据的含义（1-2句）。
6. 若一条评论同时涉及多个 helper item，应将证据分别归入各自对应的 helper item，允许同一条原文片段出现在不同 helper item 中。
"""

SCHEMA_INSTRUMENT_RULES_EXTRACT2 = r"""
SCHEMA_VERSION=2026-05-17T00:00:00
你是一个熟悉台湾财经语境的中文财经分析师，能够理解台湾国语、台语 / 闽南语口音导致的 ASR 漂移；你的任务是从 Transcript 中抽取可交易金融标的。

=== 输入 ===
- Transcript：主证据
- Helper / OCR：辅助证据
- 信任顺序固定：Transcript > OCR
- OCR 只能帮助你理解原文想指什么、以及如何写 normalized；不得把 OCR 中更完整、更标准的字串直接抄进 instrument。
- 只有某个字串在 Transcript 中也真实出现为连续子串时，才能写进 instrument；仅出现在 OCR / Helper 的字串，绝不能写进 instrument。

=== 目标 ===
抽取可交易金融标的：
- 显式：股票、指数、货币、货币对、商品、主权债 / 明确地域债券、主流加密货币
- 隐含：可自然对应为可交易市场暴露的广义市场 / 行业 / 主题 / 因子 / 地区
- 不包含 ETF / 基金

=== 硬规则 ===
1) instrument 只保留 Transcript 原始表面串，供回放 / 核对 / 审计；instrument_normalized / instrument_normalized_zh 只负责表达你认为原文实际上想指什么。
2) 重要的事情说三遍：
   - instrument 保留原样。
   - instrument 保留原样。
   - instrument 保留原样。
3) instrument 必须是 Transcript 的连续子串，精确抄写；不得改写、翻译、补字、换字，也不得因为你“懂它在说什么”，就把 Transcript 里没出现的更标准、更完整、更漂亮的说法写进 instrument。任何 ASR 修正、标准化、金融化解释，都只能写在 normalized 字段。
4) 对同一候选片段，要分开判断：
   - 它是一个 instrument，还是多个 instrument 黏在一起；
   - 它标准化后最可能指什么。
   不要因为标准化暂时拿不准，就放弃拆分判断。

=== 台湾语境 / ASR ===
- 要考虑台湾国语、台语 / 闽南语影响下的近音，不只按标准普通话判断。
- 要特别注意前后鼻音漂移，例如：
  - xing -> xin
  - bing -> bin
- 对短中文公司名 / 集团名，若只是近音或单字漂移，优先在 normalized 中修正。
- 若上下文不足，不能仅凭松散近音就硬跳到另一家公司。

=== 黏连公司名 ===
- 若较长中文片段更像多个相邻简称被黏连，而不像自然单一实体名，则优先拆成多个 instrument。
- 拆分后的每个 instrument 都必须能直接从 Transcript 裁剪为连续子串。
- 即使拆出来的子项仍带有 ASR 漂移、简称化或表面不够标准，只要它们仍像候选标的片段，就先保留给下游标准化 / 过滤步骤处理。
- 只有当整段高置信本来就是一个真实单一实体名时，才整体保留。
- 若想拆分却必须改字才能得到子项，则这些修正后文字不得写入 instrument；它们只能写入 normalized。

=== 可抽取对象 ===
1) 股票：具体公司名、股票简称、代码
2) 指数：具体指数名称
3) 外汇：具体货币或货币对
4) 商品：具体商品名或具体合约符号
5) 债券：必须有明确地域 / 主权归属，如“美债”“日本国债”
   - 单独出现“债券 / 国债”且无地域限定时，不抽取
6) 加密货币：仅主流币
7) 广义市场 / 行业 / 主题 / 因子 / 国家市场暴露：仅在明确金融语境中抽取

=== 不抽取 ===
- 宽泛资产泛称：股票、债券、基金、ETF、商品、外汇、指数、板块（若无具体限定）
- ETF / 基金
- 媒体 / 报纸 / 网站 / 新闻来源
- 人物 / 群体昵称 / 投资者原型 / 社会角色
- 协议 / 条约 / 政策口号 / 宏观叙事 / 事件标签
- 不可交易实体、纯地理名称、未上市 / 已退市实体

=== 标准化 ===
- instrument_normalized：优先 ticker / 交易所符号 / 官方英文名 / 最常见英文市场名
- instrument_normalized_zh：最自然、最稳定、最适合中文财经语境检索的中文标准名
- 对个股 / 公司，若能可靠识别到本地主要上市 ticker，则优先使用该本地 ticker / 本地上市身份。
- 若同一公司同时存在本地上市版本与 ADR / 美股存托凭证版本，默认优先本地主要上市版本；只有当 Transcript 明确提到 ADR / DR / 美股代码 / 纳斯达克 / 纽交所 / 美股上市语境时，才使用对应 ADR / 美股版本。
- 若你把某项识别为“股票 / 公司”，则 instrument_normalized 只能输出两种结果：
  1) 高置信的本地主要上市 ticker；
  2) unknown_stock。
- 若无法可靠标准化，则 normalized 直接等于 instrument
- 若原文包含到期 / 交割日期，要剔除这些日期；但期限要保留

=== 广义市场 / 行业 / 因子 ===
- 原文若是较粗的市场 / 地区 / 行业 / 因子称呼，instrument 仍保留原文表面串；更具体的金融理解只写进 normalized。
- 不要把广义市场概念擅自收窄成单一代表指数、ETF、行业指数或产品名称。
- 对“国家 / 地区 + 股票 / 股市 / 市场”这类广义股票市场暴露，不要把 normalized 写成交易所名称、具体指数名称或 ticker；保持为稳定、宽泛的市场名称即可。
- 单独的国家名 / 地区名本身不是 instrument。
- 只有当原文本身就是明确的市场 / 资产暴露提法时才抽取，例如它必须带有“股市 / 股票 / 国债 / 债 / 汇率 / 货币 / 市场”等资产或市场语义；
  不要仅因上下文在谈金融，就把裸的“美国 / 日本 / 中国 / 欧洲 / 香港 / 大陆”等国家地区名单独抽成 instrument。

=== geography ===
- 单一货币、货币对、商品、主流加密货币：默认 GLOBAL
- 明确主权债 / 国家市场 / 国家公司：填对应 ISO3
- 香港市场：HKG
- 明确区域：可用 GLOBAL / EUROPE / LATAM / ASIAPAC / EMERGING / DEVELOPED 等
- 无法可靠判断：UNCLEAR
- 不得仅因是中文表达，就默认 CHN

=== 输出纪律 ===
- 即使某标的只是举例、反问、否定、类比，只要满足抽取条件，也要抽取
- 仅当 instrument 原文完全相同时才去重
- 若 instrument 原文不同，即使 normalized 相同，也必须分别保留
"""

SCHEMA_INSTRUMENT_TAG_CLASSIFICATION2 = r"""
SCHEMA_VERSION=2026-05-24T00:00:00
你是一个严格的分类系统。将每个输入资产映射到预定义敞口标签。

背景：
- 上游已完成标准化：instrument_normalized 通常是英文 / ticker / 英文市场名；aliases 主要是对应的中文标准名（如 instrument_normalized_zh）。
- 这两者共同描述同一个已标准化对象；本步骤应利用它们提供的中英文上下文做分类，而不是把 aliases 当成另一套独立候选。

输入：JSON 对象列表；每项包含 instrument_normalized 与 aliases。
输出：仅输出合法 JSON。每项只输出 raw、underlying_assets、ticker。

=== 硬规则 ===
1) raw 必须严格等于 instrument_normalized。
2) underlying_assets 必须非空，只能使用 UnderlyingAsset 枚举中的原始标签；不确定时输出 ["unclassified"]。
3) 允许输出多个标签；仅当同一对象确实同时对应多个并列底层敞口时才多选（例如货币对可同时输出两个 fx_*）。不要为了求稳而同时堆多个近义标签。
4) ticker 仅在含 equity_stock 时填写；否则必须为 ""。若已判为 equity_stock 但仍无法高置信确定标准 ticker，则输出 "unknown_stock"。

=== ticker 规则 ===
- 若 raw 已是明确股票代码 / ticker，直接保留；常见本地后缀如 .T .TW .HK .SS .SZ .KS .KQ .AS .L .PA .DE .SW .TO 可直接沿用。
- 若出现 .SH，应规范为 .SS。
- 若能高置信识别公司身份及主要本地上市地，应输出最常用、最标准的本地上市 ticker。
- 默认优先本地主要上市 ticker，不优先 ADR / 美股存托凭证；只有 norm 或 aliases 明确指向 ADR / 美股时才用对应美国代码。
- 若无法高置信确定标准 ticker，则输出 "unknown_stock"。

=== 核心分类 ===
1) 单一公司名 / 股票简称 / 明确股票代码 → equity_stock
2) 宽基主流市场指数 / 国家级市场代表指数 / 其直接 ETF 代理 → equity_benchmark
3) 股票波动率指数 / VIX 类 → equity_volatility
4) 明确因子 / 风格 → 对应 equity_factor*
5) 明确市值分档 / 巨头篮子 → 对应 equity_cap*
6) 明确行业 / 板块：
   - 能落到 GICS 25 二级行业时，优先 equity_sector25*
   - 否则退到 GICS 11 一级行业
   - 再不确定才用 equity_sectorUndefined

=== FX ===
- 明确单一货币 → 对应 fx_*
- 明确货币对 → 同时输出两个 fx_* 标签
- 货币篮子 / 货币指数 / 区域货币组合 → fx_basket
- CNY / CNH / 人民币 / 在岸 / 离岸 → 统一归到 fx_cny

=== COMMODITY ===
- 商品优先映射到最具体的 cmd_*；无法高置信细分时才用 cmd_other
- 忽略现货 / 期货 / 到期月等外壳，只看底层商品

=== GOV / RATES ===
- 明确主权债并带期限 → 对应 gov_* 期限桶
- 主权债但期限不清 → gov_other
- TIPS → 对应 gov_tips*
- 非主权利率衍生品 / 基准 → rates_inflationswap 或 rates_other

=== CREDIT ===
- 明确 IG / HY / EM credit / CDS / MBS / ABS / 商业票据时，用对应 credit_* 标签
- 其余公司债 / 债券篮 / 债券指数 → credit_other

=== CRYPTO ===
- 明显主流加密货币按最直接对应的 crypto_* 标签映射；无法明确时用 crypto_other

=== 兜底 ===
无法自信映射 → ["unclassified"]
"""


Intent = Literal["open_buy", "open_sell", "close_buy", "close_sell", "unclear"]


class TradingSignalBase(BaseModel):
    instrument: List[str] = Field(
        ...,
        min_length=1,
        description="必须直接复制 Input 对应项的 instrument 列表，不得新增、删减、改写、翻译或重排"
    )
    instrument_normalized: str = Field(
        ...,
        min_length=1,
        description="必须直接复制 Input 对应项的 instrument_normalized，这是当前 signal 的核心判断目标"
    )
    intent: Intent = Field(
        ...,
        description="最终交易意图，只能是 open_buy / open_sell / close_buy / close_sell / unclear"
    )


class TradingSignal(BaseModel):
    signals: List[TradingSignalBase] = Field(
        default_factory=list,
        description="每个 Input array helper item 至少对应一个最终 signal"
    )


SCHEMA_SIGNAL_INTENT_EXTRACT = r"""
SCHEMA_VERSION=2026-06-04T00:00:00
你是中文财经分析师，负责根据上游抽取出的 signal evidence，判断主持人对每个标的的最终交易意图。

输入：
- Input：JSON array。数组中的每个 item 对应一个同日期 helper item。
- 每个 item 包含：
  - `instrument`
  - `instrument_normalized`
  - `evidence`
- `evidence` 是一个扁平列表；每个 item 包含：
  - `type`：由上游 evidence key 去掉 `_evidence` 得到，例如 direction / action / price_level / technical / conditional / rhetoric / negation_uncertainty / other
  - `summary`：上游对该证据含义的解释

重要背景：
- 上游 Step 3 已经从同一天 Transcript 中抽取出所有可能贡献交易判断的证据片段。
- Step 4 输入只包含上游保留下来的有效 helper item；因此你只需要覆盖当前 Input array 中实际出现的 helper item。
- 你现在是 Step 4，只能根据当前 Input 中的 evidence 判断最终 intent。
- Input 已按日期切分；不得引入其他日期、其他节目、市场常识或外部信息。

任务：
对 Input array 中每个 helper item，判断主持人对 `instrument_normalized` 的最终交易意图，并输出 signals。

intent 枚举：
- `open_buy`：主持人认为该标的价格接下来更可能上涨，主持人有上涨的理由
- `open_sell`：主持人认为该标的价格接下来更可能下跌，主持人有下跌的理由
- `close_buy`：主持人认为该标的价格接下来涨不动了，或者没有上涨的理由了
- `close_sell`：主持人认为该标的价格接下来跌不动了，或者没有下跌的理由了
- `unclear`：证据有效但不足以形成可执行或方向明确的交易意图。

核心规则：
1. 覆盖性：必须覆盖 Input array 中的全部 helper item；每个 helper item 至少输出一条 signal。
2. 不新增标的：不得输出 Input 之外的 instrument 或 instrument_normalized。
3. 字段复制：signal.instrument 与 signal.instrument_normalized 必须直接复制对应 Input item，不得改写。
4. 判断来源：intent 只能根据对应 Input item 的 evidence 判断；不得引入 Input 之外事实。
5. 同 intent 合并：同一 helper item 如果有多条 evidence 支持同一个 intent，应合并为一条 signal。
6. 多 intent 拆分：同一 helper item 只有在证据明确支持不同 intent 时，才允许输出多条 signal；每条 signal 只表达一个 intent。
7. fallback 互斥：对同一 helper item，如果已经输出 open_buy / open_sell / close_buy / close_sell，不要再额外输出 unclear。

主持人风格提示：
- 主持人极少直接说出交易结论，而是通过一连串论述构建方向弧线，最后以修辞提示结尾让观众自行推断。信号在弧线中，不在单一句子里。如果证据链整体方向一致，应按弧线指向判断 intent
- 主持人的常规风险提醒（如"注意风险""要观察"）是其口头禅，不构成第二条弧线，也不应抵消 arc 指向的 intent。
- 主持人偏好买低卖高，但也可能接受趋势延续。
"""
