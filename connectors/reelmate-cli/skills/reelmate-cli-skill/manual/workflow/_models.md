# 模型目录

模型展示名、可见性、模式和合法参数都以当次命令返回为准。不要在文档或记忆里维护对照表。本次目录没有的条目不展示、不提交；目录多出来的条目按实际返回展示。`id` / `ai_model_mark` 任何时候都不能给用户看，查询 JSON 也不会返回它们。

## 查询

```bash
reelmate model list --type image --sp-type MODEL_SP_TYPE --json
reelmate model list --type video --sp-type MODEL_SP_TYPE --json
reelmate model search KEYWORD --sp-type MODEL_SP_TYPE --json
reelmate model params image|video MODEL_NAME --json
```

`MODEL_SP_TYPE` 从 [_bootstrap.md](_bootstrap.md) 推出。账号可见性以在线目录为准；`--offline-models` 只用于排查命令格式。字段含义见 [model.md](../../commands/model.md)。

问用户和提交都只用 `name` / `display_name`。括号只允许 `（推荐）`。用户说的名字先在本次 `list` / `search` 结果里匹配，匹配不到就展示实时目录让用户选。生成命令写 `--set ai_model_mark=<展示名>`，由 CLI 解析。

提交必须带已确认场景：画布生成和积分预估同时写 `--set mode=`；分镜或参考生视频走对应命令。目录里可能有两条记录同名（例如 Vidu Q2、Happy Horse 1.0）；按上面筛完后仍全部列给用户。禁止因为 CLI 报「不唯一」就把该项从候选删除或改推其它模型。`model params` 遇到同名时补同一 `mode` 再查。

确认时列全、分步见 [_hard-gate.md](_hard-gate.md)，呈现见 [_hitl-present.md](_hitl-present.md)。本页只规定模型及其画幅、分辨率、时长枚举从哪读。先确认模型，再按该模型规则列出画幅、分辨率、时长；拆分镜模板按 [拆分镜模板选择](gui-script-video-storyboard.md#模板合并与选择) 合并两类目录；官方按模型分组，团队一步流按项目真实类型和界面语言查询完整目录，与视频模型无关。用户改选模型后，丢掉旧选择并重列。例外：画布生剧本按 [generate-script.md](generate-script.md)，目录含 TG Chat 5.5 时直接采用该文本模型，不列全、不走 HITL。本例外只覆盖文本模型，不含图片或视频。

## 筛选

- 只列 `visible=true` 的记录。
- 画布生图 / 生视频：`supported_modes` 含目标模式，且 `params.generation.<mode>` 非空。账号未开白时 CLI 会从 `supported_modes` 摘掉对应模式，不要用静态名单补回来。
- 资产生图（GUI 环节 3 与资产提示词回填生图）：只看 `params.studio_asset_image` 非空且 `visible=true`。按 `mode_order.studio_asset_image` 升序列展示名。角色、场景、道具共用这一套。本场景 0 条时停止，不改走画布 `text2image` 清单，也不要用 `mode_order.text2image` / 画布 `supported_modes` 当本场景成员或排序依据。
- 剧本拆分镜（GUI 环节 4）：只看 `params.script_to_scene_refer` 非空。按 `mode_order.script_to_scene_refer` 升序列展示名。本场景 0 条时停止，不改走分镜规划 13 模表，也不要用 `params.storyboard_reference_video` 非空或 `mode_order.universal_reference` 当成员/排序依据。
- 分镜规划 / Excel 回填生视频：只看 `params.storyboard_reference_video` 非空。不要用画布 `supported_modes` 是否含 `universal_reference` 来筛——未开白时该模式会被摘掉，分镜规则仍可能在。
- 画布剧本：`reelmate model search 'TG Chat' --json`，只取 `type` / `types` 含 `file` 且 `visible=true` 的记录。没有匹配项时停止，不换用其它模型。含 TG Chat 5.5 时的确认规则见 [generate-script.md](generate-script.md)，不要按本页「确认时列全」去弹文本模型选择器。

目标模式由输入素材决定，不由文档里的模型名单决定：无图图片 `text2image`，单张参考图 `image2image`，多张 `multi_reference`；无图视频 `text2video`，一张图 `image2video`（首帧语义为 `first_frame`），首尾帧 `first_last_frame`，多素材 `universal_reference`。模型不支持该模式时 CLI 会报错，不自动换模式或换模型。

筛完后按 `mode_order[目标模式]` 升序列模型展示名；缺该键的条目排在有键条目之后。资产生图的目标模式键是 `studio_asset_image`；分镜规划 / 回填参考生视频的目标模式键是 `universal_reference`；剧本拆分镜的目标模式键是 `script_to_scene_refer`。禁止按 mark 字母序、展示名字母序或自拟顺序重排。

分辨率只按 `resolution_options` 原序列 `label`。不要把提交值念给用户，也不要按码口算中文（`720p_sale` 不是 720P优惠版）。`--set resolution=` 交展示名，由 CLI 解析。

## 推荐

推荐值是剧厂口径，必须先落在当次目录里才展示：

- 图片：目录展示名含 `TGI 2` 时推荐该项。资产生图禁止把列表第一项当默认（常见第一项是 TGI 2.5 Flare）。
- 画布视频 / 分镜规划 / 回填参考生视频：目标模式候选的展示名含 `Seedance 2.0 VIP` 时推荐该项。
- 剧本拆分镜：候选展示名含 `Seedance 2.0 VIP` 时推荐该项；禁止把列表第一项当默认（常见第一项是 Seedance 2.5）。
- 分辨率、画幅、时长取所选模型目标模式的 `params.generation.<mode>` 或 `params.storyboard_reference_video`。图片/画布视频用前者，分镜规划 / 回填 / 剧本拆分镜选中后的画幅分辨率时长用后者。资产生图选中后的画幅 / 分辨率仍读 `params.generation.text2image` 的 `ratios` 与 `resolution_options` 原序列 `label`；本轮不问画质。分辨率列 `resolution_options[].label`，有 `default_resolution` 时把对应 label 标推荐。推荐值不在枚举中时改用该规则默认值。无论是否有推荐，都把该规则的真实枚举全部列给用户。

目录没有上述展示名时，只把本次候选列给用户，不伪造标识。不因为有推荐就省略其它候选。
