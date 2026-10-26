# Resource Radar · 资源雷达

**好工具很多，难的是找到它。**

FMHY、Awesome Lists、油猴脚本社区、免费开发资源……有价值的东西散落在各种目录里，普通搜索不一定找得到。

**Resource Radar 把精选资源入口汇总进本地索引，再通过 MCP 交给你的 AI Agent 搜索。** 不用反复翻收藏夹，也不用挨个网站碰运气。

[English](README.en.md) · [快速开始](#快速开始) · [接入 MCP](#接入-mcp) · [后续计划](#接下来做什么)

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-stdio-333333)
![SQLite](https://img.shields.io/badge/Local_Index-SQLite-003B57?logo=sqlite&logoColor=white)

## 它能帮你找到什么？

| 你想做什么 | Resource Radar 会去哪找 |
| --- | --- |
| 找免费、冷门但实用的软件与网站 | **FMHY** |
| 找某个方向的精选项目清单 | **Awesome Lists** |
| 找能自己部署的知识库、影音服务或自动化工具 | **Awesome Selfhosted** |
| 找免费 API、云服务和开发工具 | **Free for Dev** |
| 找浏览器增强脚本、油猴脚本 | **Awesome Userscripts**；尝试查询 **Greasy Fork** 实时 API |

你可以这样问 Agent：

> - “有什么能本地部署的 AI 知识库？”
> - “帮我找几个增强 YouTube 使用体验的油猴脚本。”
> - “有没有免费可用的开发 API？”

它就可以先调用 Resource Radar 找候选工具，再顺着原始来源做下一步研究。

## 一次搜索，多份精选目录

`你的问题 → 多源资源索引 → 关键词检索与 URL 去重 → 来源追溯 → MCP / Agent`

当前版本使用 **SQLite + FTS5**，具备本地全文搜索、子串回退匹配、来源过滤、同链接去重和同步记录。核心目录下载后保存在本机，可以重复检索。

**首轮本地实测（2026-10-26）：5 个目录、27,964 条去重资源。** 这是一次同步结果，不是实时更新的资源总量。

例如查询 **Ollama**，能看到它同时出现在 FMHY 和 Awesome Selfhosted；查询 **YouTube** 用户脚本，也能从 Awesome Userscripts 索引中发现相关项目。

## 快速开始

需要 Python 3.11+ 和 Git。以下是 Windows PowerShell 示例：

```powershell
git clone https://github.com/lite-milkfrog/resource-radar.git
cd resource-radar

py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .

$env:RESOURCE_RADAR_DB = (Join-Path (Get-Location) 'data\index.sqlite3')
.\.venv\Scripts\resource-radar.exe sync
.\.venv\Scripts\resource-radar.exe search "Ollama"
.\.venv\Scripts\resource-radar.exe search "YouTube" --source awesome_userscripts
```

运行状态查看：

```powershell
.\.venv\Scripts\resource-radar.exe status
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

没有设置 `RESOURCE_RADAR_DB` 时，默认使用本机用户目录中的 `ResourceRadar/index.sqlite3`；首次搜索之前需要执行一次 `sync`。

## 接入 MCP

把它接进支持 MCP 的 Agent，资源检索就不再局限于通用网页搜索。

```json
{
  "mcpServers": {
    "resource-radar": {
      "command": "D:\\AgentData\\10_Workspaces\\resource-radar\\.venv\\Scripts\\python.exe",
      "args": ["-m", "resource_radar.server"],
      "env": {
        "RESOURCE_RADAR_DB": "D:\\AgentData\\10_Workspaces\\resource-radar\\data\\index.sqlite3"
      }
    }
  }
}
```

这是**通用 MCP 客户端配置示例**，请把绝对路径替换为实际安装目录，并把 `resource-radar` 条目合并到客户端现有的服务配置中。WAC 不同版本的配置入口可能有所不同；本项目的 WAC 自动注册尚在计划中。

### 现在提供的 7 个 MCP 工具

| MCP 工具 | 作用 |
| --- | --- |
| `search_resources` | 搜本地资源索引，按来源过滤 |
| `search_userscripts` | 搜 Greasy Fork，失败时回退到本地精选脚本索引 |
| `inspect_resource` | 查看资源详情与原始出处 |
| `inspect_script` | 读取 Greasy Fork 脚本元数据并检查静态风险线索 |
| `compare_resources` | 并排对比已索引资源的已知信息 |
| `sync_sources` | 更新指定资源目录 |
| `source_status` | 查看资源数量、更新时间和同步错误 |

Greasy Fork 的实时 API 在部分网络会返回 403；此时 MCP 会说明问题，并尝试从已同步的 Awesome Userscripts 目录给出结果。

## 接下来做什么？

- **发现更多资源**：逐步加入 ScriptCat、OpenUserJS、HelloGitHub 等来源。
- **搜索更聪明**：改善中文分词、同类项目聚合和排序。
- **从发现走向判断**：接入 GitHub 活跃度、许可证和链接状态等核验信息。
- **接进日常工作流**：完成 WAC 实机注册和端到端调用验收。

目标很简单：**你只管说想解决什么问题，Agent 负责帮你找到已经有人做好的工具。**

## 关于资源

Resource Radar 保留原始出处与同步记录，方便你核对工具；找到的脚本不会被自动安装或执行。不同资源目录有各自的许可与使用规则，索引数据保留在本地，**不会被打包上传到本仓库**。

---

**如果你也受够了到处翻资源目录，欢迎提 Issue 推荐值得接入的站点。**
