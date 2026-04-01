# Kangyur RAG Search — 技术文档

> 基于 Google Gemini File Search 的藏传佛教甘珠尔经典语义检索系统

## 1. 项目概述

本项目利用 Google Gemini File Search（RAG）API，将罗马化藏文（Romanized Tibetan）甘珠尔（Kangyur）佛经文本作为知识库，支持用户以**英文提问**，系统语义检索并返回**匹配的罗马化藏文原文段落**及英文翻译与来源引用。

### 核心流程

```
用户英文查询
    ↓
Google Gemini File Search (语义 embedding 匹配)
    ↓
返回罗马化藏文原文 + 英文翻译 + 来源溯引
```

### 当前状态

- **POC 验证通过** — 律部（Vinaya）16 个文件已成功上传并测试
- 英文查询 → 藏文匹配 → 溯源引用，全流程跑通
- 方案 B（直接上传原文，无需预处理）已验证可行

---

## 2. 环境配置

### 运行环境

| 项目 | 值 |
|------|-----|
| 操作系统 | macOS (Darwin 24.6.0) |
| Python 版本 | **Python 3.10.7**（必须使用 3.10+） |
| Python 路径 | `/Library/Frameworks/Python.framework/Versions/3.10/bin/python3.10` |
| google-genai 版本 | **1.60.0** |
| 项目根目录 | `/Users/haowei/Downloads/Code/ALL_Search` |

### 重要：Python 版本要求

系统默认的 Anaconda Python 3.9 **不兼容** google-genai 1.48+（缺少 `file_search_stores` API）。必须使用 `python3.10` 命令运行所有脚本。

```bash
# 正确 ✅
python3.10 test_poc.py setup

# 错误 ❌ (Anaconda Python 3.9, google-genai 版本太旧)
python test_poc.py setup
```

### 依赖安装

```bash
# 安装到 Python 3.10 环境
pip3.10 install google-genai>=1.60.0
# 或
/Library/Frameworks/Python.framework/Versions/3.10/bin/pip3 install google-genai
```

---

## 3. API 与服务配置

### Google Gemini API

| 项目 | 值 |
|------|-----|
| API Key | `YOUR_GEMINI_API_KEY` |
| 查询模型 | `gemini-3-pro-preview`（在 `config.py` 中配置） |
| API 文档 | https://ai.google.dev/gemini-api/docs/file-search |

API Key 通过环境变量传入：

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

### File Search Store（已创建）

| 项目 | 值 |
|------|-----|
| Store 名称 | `fileSearchStores/kangyurvinayapoc-yqdrpsujqcve` |
| 显示名 | `kangyur-vinaya-poc` |
| 已上传文件数 | 16 个（律部 Vinaya 全卷） |
| 数据持久性 | 手动删除前永久保留（不受 Files API 48 小时限制） |

Store 名称自动保存在项目根目录的 `.store_name.json` 文件中。

### Google File Search 定价参考

| 项目 | 费用 |
|------|------|
| 索引（Indexing） | $0.15 / 1M tokens |
| 存储（Storage） | 免费 |
| 查询 embedding | 免费 |
| 检索 tokens | 按常规 context tokens 计费 |
| 免费层存储上限 | 1 GB |

---

## 4. 数据说明

### 数据源

甘珠尔（Kangyur）罗马化藏文文本，位于：

```
/Users/haowei/Downloads/Code/ALL_Search/KANGYUR updated to 12 30 25 WS 2/
```

| 统计 | 值 |
|------|-----|
| 总文件数 | 1008 个 .txt 文件 |
| 总大小 | 124 MB |
| 文本格式 | 罗马化藏文（ACIP/Wylie 转写） |

### 甘珠尔分类结构（13 部）

| 编号 | 藏文名 | 英文名 | 梵文名 | Metadata key |
|------|--------|--------|--------|-------------|
| 1 | 'DUL BA | Vowed Morality | Vinaya | `Vinaya` |
| 2 | 'BUM | Perfection of Wisdom in 100,000 Lines | Śatasāhasrikā Prajñā Pāramitā | `Prajnaparamita_100k` |
| 3 | NYI KHRI | Perfection of Wisdom in 25,000 Lines | Pañcaviṃśatisāhasrikā | `Prajnaparamita_25k` |
| 4 | BRGYAD STONG | Perfection of Wisdom in 8,000 Lines | Aṣṭasāhasrikā | `Prajnaparamita_8k` |
| 5 | KHRI BRGYAD STONG | Perfection of Wisdom in 18,000 Lines | Aṣṭadaśasāhasrikā | *(未映射)* |
| 6 | KHRI PA | Perfection of Wisdom in 10,000 Lines | Daśasāhasrikā | *(未映射)* |
| 7 | SHER PHYIN SNA TSOGS | Other Teachings on Perfection of Wisdom | — | *(未映射)* |
| 8 | DKON BRTZEGS | Pile of Jewels | Ratnakūṭa | `Ratnakuta` |
| 9 | PHAL CHEN | The Majority | Avataṃsaka | `Avatamsaka` |
| 10 | MDO MANG | Collection of Sutras | Sūtra | `Sutra_Collection` |
| 11 | MYANG 'DAS | Nirvana | Nirvāṇa | `Nirvana` |
| 12 | RGYUD | Secret Teachings | Tantra | `Tantra` |
| 13 | DKAR CHAG | Native Catalog | — | *(未映射)* |

### 文件命名规则

```
KL00001E1_'DUL BA GZHI 1_Foundation of Vowed Morality, Part 1 (Vinaya Vastu 1).txt
│         │              │
│         │              └── 英文标题 (梵文名)
│         └── 藏文标题
└── 编号 (KL = Kangyur Lhasa edition)
```

### 已知编码问题

文件名含梵文 diacritics（如 `ṣ`, `ṃ`, `ṇ`），`google-genai` SDK 的 `files.upload()` 无法直接处理含 Unicode 的文件路径。解决方案：先复制文件到临时 ASCII 安全路径，再上传（已在 `upload.py` 中实现）。

---

## 5. 项目文件结构

```
ALL_Search/
├── config.py              # 全局配置（API key, 模型名, 数据路径）
├── upload.py              # 上传工具（创建 store / 上传文件 / 列出 store）
├── search.py              # 搜索引擎（单次查询 / 交互模式 / 分类过滤）
├── test_poc.py            # POC 测试脚本（一键 setup + 批量测试）
├── requirements.txt       # Python 依赖
├── .store_name.json       # 自动保存的 store 名称（由 test_poc.py 生成）
├── docs/
│   └── TECHNICAL_DOC.md   # 本文档
└── KANGYUR updated to 12 30 25 WS 2/   # 甘珠尔数据文件
    ├── 1. 'DUL BA_Vowed Morality (Vinaya)/
    │   ├── VOL 1 (KA)/
    │   ├── VOL 2 (KHA)/
    │   └── ...
    ├── 2. 'BUM_.../
    ├── ...
    └── 13. DKAR CHAG_.../
```

### 各文件详细说明

#### `config.py`
- `GEMINI_API_KEY` — 从环境变量 `GEMINI_API_KEY` 读取
- `MODEL_NAME` — 当前设置为 `gemini-3-pro-preview`
- `KANGYUR_BASE` — 甘珠尔数据根目录
- `POC_FOLDER` — POC 测试用的律部文件夹

#### `upload.py`
- `create_store(client, display_name)` — 创建新的 File Search Store
- `upload_folder(client, store_name, folder_path)` — 批量上传 .txt 文件，自动提取 category/volume metadata
- `get_category_from_path(filepath)` — 从文件路径推断甘珠尔分类
- `list_stores(client)` / `list_documents(client, store_name)` — 查看已有 store 和文档

CLI 用法：
```bash
python3.10 upload.py create --display-name "kangyur-full"
python3.10 upload.py upload-poc --store-name fileSearchStores/xxx
python3.10 upload.py upload-all --store-name fileSearchStores/xxx
python3.10 upload.py list-stores
python3.10 upload.py list-docs --store-name fileSearchStores/xxx
```

#### `search.py`
- `search(client, store_name, query, model, category_filter)` — 核心搜索函数
- `format_response(response)` — 格式化输出（主文本 + grounding citations）
- `interactive_search(client, store_name)` — 交互式搜索循环
- System prompt 指导 Gemini：引用原文 → 英文翻译 → 来源标注 → 相关性解释

CLI 用法：
```bash
# 单次查询
python3.10 search.py --store-name fileSearchStores/xxx -q "What are the four root downfalls?"

# 带分类过滤
python3.10 search.py --store-name fileSearchStores/xxx -q "rules about robes" -c Vinaya

# 交互模式
python3.10 search.py --store-name fileSearchStores/xxx
```

交互模式中支持分类前缀过滤：
```
Query> cat:Vinaya What are the rules about eating?
```

#### `test_poc.py`
- `setup` — 一键创建 store + 上传律部文件
- `test` — 运行 7 个预设测试查询
- `interactive` — 进入交互模式

---

## 6. 快速开始

```bash
cd /Users/haowei/Downloads/Code/ALL_Search

# 设置 API Key
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# 使用已有的 POC store 直接搜索
python3.10 search.py --store-name fileSearchStores/kangyurvinayapoc-yqdrpsujqcve -q "What are the four defeats?"

# 或进入交互模式
python3.10 search.py --store-name fileSearchStores/kangyurvinayapoc-yqdrpsujqcve
```

如需从头搭建：
```bash
# 1. 创建 store 并上传 POC 文件（律部 16 个文件）
python3.10 test_poc.py setup

# 2. 批量测试
python3.10 test_poc.py test

# 3. 扩展到全部甘珠尔（1008 个文件）
python3.10 upload.py create --display-name "kangyur-full"
python3.10 upload.py upload-all --store-name fileSearchStores/新store名称
```

---

## 7. POC 验证结果

### 已测试查询及结果

| 查询 | 结果 | 命中来源 |
|------|------|----------|
| "What are the rules about monks eating food?" | 成功检索到布萨（gso sbyong）相关段落 | Vinaya Vastu 1, Vinaya Vastu 4 |
| "What are the four root downfalls (parajika)?" | 准确返回四根本堕内容 | Vinaya Vastu 4, Vinaya Uttara Grantha B2 |

### 关键发现

1. **语义检索有效** — Google File Search 能理解罗马化藏文和英文之间的语义关系
2. **Grounding citations 可用** — 返回结果包含文件名和原文片段，可溯源
3. **Metadata 过滤可用** — 支持按类别（category）和卷号（volume）过滤
4. **编码问题已解决** — 通过临时路径复制绕过 SDK 的 ASCII 编码限制

---

## 8. 后续开发路线

### 阶段二：扩展到全部甘珠尔

- 上传全部 1008 个文件到新 store
- 补全 `get_category_from_path()` 中未映射的分类（5/6/7/13）
- 验证大规模数据下的检索质量

### 阶段三（可选）：方案 A — 双语增强索引

如果直接检索效果不够好，可升级到方案 A：
- 用 LLM 为每个文本块生成英文摘要/关键词
- 将「原文 + 英文注释」一起上传
- 显著提升跨语言语义匹配质量

### 其他可能的扩展

- 加入宗喀巴（Je Tsongkhapa）等藏传大师的著作
- 加入丹珠尔（Tengyur）论典
- 构建 Web UI（Streamlit / Gradio）
- 支持藏文脚本（Tibetan Unicode）输入
- 结合 Structured Output 返回标准化 JSON 结果

---

## 9. Google File Search API 关键参考

### 支持的模型

- `gemini-3-pro-preview`
- `gemini-3-flash-preview`
- `gemini-2.5-pro`
- `gemini-2.5-flash-lite`

### 存储限制

| 层级 | 存储上限 |
|------|----------|
| Free | 1 GB |
| Tier 1 | 10 GB |
| Tier 2 | 100 GB |
| Tier 3 | 1 TB |

建议单个 store 不超过 20 GB。

### 支持的文件类型

TXT, PDF, DOCX, JSON, Markdown, HTML, 以及 100+ 种文本格式。

### API 限制

- 不支持 Live API
- 不能与其他工具（Google Search, URL Context 等）同时使用
- 单文件最大 100 MB
- Files API 上传的文件 48 小时后过期，但导入到 File Search Store 后**永久保留**

### 官方文档

- File Search: https://ai.google.dev/gemini-api/docs/file-search
- Python SDK: https://github.com/googleapis/python-genai
- API Key 管理: https://aistudio.google.com/apikey
