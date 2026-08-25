# tencentcloud-api-skill

[![Sync ClawHub upstream](https://github.com/Marco9442/tencentcloud-api-skill/actions/workflows/sync-upstream.yml/badge.svg)](https://github.com/Marco9442/tencentcloud-api-skill/actions/workflows/sync-upstream.yml)

这是 ClawHub 官方技能 [`tencent-adm/tencentcloud-api-skill`](https://clawhub.ai/tencent-adm/skills/tencentcloud-api-skill) 的**自动同步公开镜像**。仓库根目录保持标准 Agent Skill 结构，可直接作为 GitHub Skill 源使用。

## 上游信息

- ClawHub 上游：[`tencent-adm/tencentcloud-api-skill`](https://clawhub.ai/tencent-adm/skills/tencentcloud-api-skill)
- 当前同步版本：`1.0.3`
- 上游许可证：`MIT-0`
- 上游元数据：[`https://clawhub.ai/api/v1/skills/tencentcloud-api-skill`](https://clawhub.ai/api/v1/skills/tencentcloud-api-skill)
- 最新版下载：[`https://clawhub.ai/api/v1/download?slug=tencentcloud-api-skill&tag=latest`](https://clawhub.ai/api/v1/download?slug=tencentcloud-api-skill&tag=latest)
- 同步清单：[`.clawhub/upstream.json`](.clawhub/upstream.json)

> 本仓库不是独立开发分支。`SKILL.md`、`skill-card.md`、`references/`、`_meta.json` 等技能文件来自 ClawHub 上游；镜像仅增加 README、许可证副本、来源清单和自动同步基础设施。

## 作为 Agent Skill 使用

将本仓库作为 GitHub Skill 源安装，或克隆到 Agent 的 skills 目录。入口文件位于仓库根目录：

```text
SKILL.md
```

示例：

```bash
git clone https://github.com/Marco9442/tencentcloud-api-skill.git
```

具体安装方式取决于所使用的 Agent 运行时；任何支持标准 `SKILL.md` 仓库布局的运行时都可以直接读取本仓库。

## 自动同步机制

GitHub Actions 工作流 [`.github/workflows/sync-upstream.yml`](.github/workflows/sync-upstream.yml) 会：

1. 每 6 小时检查一次 ClawHub `latest` 版本，也支持手动触发。
2. 从 ClawHub API 核验所有者、slug、版本和许可证。
3. 安全解压官方发布包，并同步新增、修改和删除的上游文件。
4. 更新当前版本、许可证和 `.clawhub/upstream.json` 文件哈希清单。
5. 仅当 Git 工作区实际发生变化时创建并推送提交；无变化时正常结束且不产生空提交。

同步提交由 `github-actions[bot]` 创建，提交信息格式为：

```text
chore(sync): update ClawHub upstream to <version>
```

## 来源与许可证

原始来源和上游版本信息保存在 [`.clawhub/upstream.json`](.clawhub/upstream.json)。上游 API 声明当前版本采用 `MIT-0`；许可证文本见 [`LICENSE`](LICENSE)。所有上游内容的权利归原作者及权利人所有。
