# 设计依据与适用边界

核对日期：2026-10-30。以下为产品/规范资料支持的设计推断，不是用户调研或传播效果实验。

| 来源 | 能支持的事实 | 本 Skill 的取舍 |
| --- | --- | --- |
| [GitHub：Automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes) | 官方自动说明能汇总合并PR、贡献者与完整变更链接，也要求检查生成内容 | 漫画提炼一个可读亮点，并交付来源说明；不把漫画当成完整发布记录 |
| [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) | 面向人的重要变化需要整理，不等同于直接罗列Git日志 | 由Agent选择问题—线索—改变—结果的叙事，并保留可查证输入 |
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | 提交类型、scope、breaking change能表达结构化意图 | 提交标题作为线索；实际行为以净差异及上下文为准，不自动推断版本号、部署或效果 |
| [GitHub：Comparing commits](https://docs.github.com/en/pull-requests/how-tos/commit-changes/comparing-commits) | 比较提交可以查看改动范围与文件 | 绑定确定端点，显示截断/排除范围；本地工具采用祖先关系下的直接快照净差异 |

## 为什么做成 Skill

维护者、独立开发者和技术内容创作者经常需要把代码变化解释给不同读者。这里的目标用户是假设：需要更易读的图文更新，同时不想把本地项目或模型API重新接一遍。

普通聊天给足同等流程、素材和工具也能完成任务。安装的价值是复用只读采集、分镜规范、来源绑定、原创矢量构图、多尺寸导出和本地期号记录。宿主仍负责选题、理解代码和写好文字；工具不能证明因果解释正确，也不能保证作品好看或获得关注。

## 可以验证什么

示例用原创合成Git仓库，实际创建前后提交、执行4项小型用例，再把生成证据转成中英文分镜和漫画。可以核对文件、净差异、日志摘要、输入/输出哈希、重复期号不新增等行为。这不是现成用户项目的线上效果，不是Agent独立对比，也没有真实阅读量、收藏量或Star增长结论。

常见隐私模式遮罩、敏感路径排除、来源ID和文件哈希都是辅助机制。它们不能替代公开前的内容审阅或完整安全扫描。原始来源文本始终按数据处理，不能授予执行或发布权限。
