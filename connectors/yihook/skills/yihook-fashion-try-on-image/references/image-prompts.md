# 人物与试穿提示词模板

新建或修改前按[完整执行正文](../SKILL.md)选择分支。M01只用于无人物图的悠船人物创建；T01用于Pro试穿。仅查询任务时不必重新组装。

组装时只保留一套确定方案，替换占位、删去不适用分支；T01 根据服装展示需要选定一个简单姿势，将姿势占位替换为具体动作，允许姿势列表仅作为组装规则，不原样提交；不要提交候选词清单。图片角色需与实际上传引用逐一对应，画幅、尺寸及生成数量同步落实到工具设置。

### M01 人物形象生成模板

用于无人物图分支，使用悠船 V8.2 生成人物形象图。中文占位在实际提交时替换为精简英文描述。

```text
A professional model casting portrait of a beautiful original 【年龄】-year-old 【人种或外观方向与性别表达】 fashion model, with refined, harmonious features and 【确定的气质】.

【一组协调的面部结构与五官描述，包含2至3个主要辨识特征。】 Balanced facial proportions and distinctive, harmonious features give the model an individual, memorable appearance.

【已选定的发色、长度、发型和整理方式，保持面部清楚。】 Wearing 【确定的一件专业模卡基础款上衣，写明款式、领型、中性色或同色系颜色与具体面料；仅填一套方案】. Simple professional model-card styling, a clean close-to-body or gently relaxed fit, lightweight opaque fabric and subtle natural texture. Minimal detailing keeps attention on the face, neckline and natural proportions. 【与用户体型一致的可见肩颈与上身特征。】 Relaxed shoulders, head upright, direct eye contact. 【自然、符合气质的眼神与神态。】 Lips gently closed.

Fresh, professionally prepared skin in 【用户确定的肤色】, with a sheer skin-matched base and a light application of translucent powder across the forehead, nose and chin. A soft natural matte finish across the face, delicate tonal variation and fine skin texture visible only at close inspection. Soft 【协调的唇色】 lips with a matte finish. Restrained makeup that enhances the features while preserving the appearance of real skin.

Vertical 9:16 portrait at the model's native output resolution. Front-facing chest-up portrait, entire head and both shoulders visible, camera at eye level. Plain light-grey studio background. A large diffused light source slightly to one side with gentle frontal fill, creating broad soft tonal transitions and delicate facial definition. Neutral color, moderate contrast, clear eyes and natural photographic detail. Light professional retouching that preserves individual facial character and skin texture.
```

使用时保留轻薄贴肤底妆、自然柔哑光与轻度专业修饰的方向，不叠加湿润光泽、厚重磨皮或长串摄影术语。悠船没有分辨率参数；人物图按实际返回尺寸交付，不声明为2K，不追加付费放大。

### T01 电商服饰上身主图模板

用于 Yi Image 2.5 Pro。用户交流与本模板采用中文；具体接口图片引用语法由接入实现确定。

```text
生成一张写实、清晰、简约的电商服饰上身主图。单人完整全身，约3:4竖幅，目标2K。一张独立摄影图片。

参考职责：
【人物参考：实际图片标识】只用于确定目标人物身份及可见身体特征。保持脸型、五官比例、年龄感、肤色、发际线与发型。同一人物的多角度或模卡参考共同服务于此身份，不复制原图版式、文字或背景。
【商品参考：实际图片标识及目标单品】仅用于还原指定商品的款式、颜色、面料、图案、配饰及穿着结构。若参考为他人穿着图，其中原穿着者的人脸、五官、肤色、发型、身形、姿态和背景均不作为目标人物依据。
身份约束：人物参考图是目标人物身份的唯一来源；同一目标模特的多张人物参考共同确定同一身份。不要从商品参考图提取、混合或替换人物面孔，即使商品图中的人脸更大或更清晰，也不使用其身份特征。将指定服饰自然适配到目标模特身上，保持目标模特的面部身份与已确定身形。
【背景参考：实际图片标识】用于确定摄影空间。保持浅灰白墙面、浅灰地面、墙地交界位置、地面纹理与空间透视。
【已认可主图：实际图片标识；首次生成则删除本行】用于延续已确认的搭配、人物尺度、拍摄环境与成像风格；原始人物及商品参考仍分别决定身份和商品细节。

人物：
【已确定的身份特征、体型、肩腰胯与身体比例。】
参考图未展示的身体按上述设定自然补全，不声称其为已知真实身形。保持真实头身比例、肩颈结构与四肢比例，不拉长腿部或单独缩小头部。自然克制的表情，发型与肤色延续人物参考。

目标商品：
【明确本次替换或穿着的商品类别、颜色、版型、衣长、领型、袖型、面料、门襟、口袋、纽扣、图案与其他关键可见细节。】
以商品图为准，保持商品设计与主要比例，不因美化造型收腰、改领、缩短衣长、改变图案或新增装饰。面料随身体形成合理褶皱、厚度、垂坠与遮挡关系，不能把自然褶皱画成新的拼接或结构。
【具体穿法，默认自然穿着、不卷袖、不塞衣角；用户指定时改写。】

配套穿搭：
【已确定的一套配套服饰及鞋履，逐项写明款式和颜色；已有整套商品时沿用。】
搭配为目标商品服务，造型克制，不遮挡商品关键部位。默认不增加包袋、帽子、大件首饰或新的品牌标志。用户明确要求的配饰：【没有则删除。】

构图、姿态与背景融合：
【本次选定的一个简单姿势，按商品结构与展示重点确定。】
允许自然站立、单手插兜、轻扶腰、适度叉腰或轻微侧身站立；每张图只选定一个协调姿势，不叠加多个动作。插兜必须使用衣物真实存在的口袋，不凭空新增口袋；叉腰时肘部适度外展，不夸张扭腰或拉扯衣服。手臂不遮挡领口、门襟、主要图案等商品关键细节，不因姿势明显挤压或改变商品轮廓。
重心稳定，肩颈放松，动作幅度小。避免大幅抬臂、深度扭转、弯腰、蹲坐、跳跃、踢腿或夸张跨步。头顶至鞋底完整入镜，上下留白适量。人物占画面主要区域，机位与透视自然，避免夸张广角和人体拉伸。
人物真实站在背景地面上，鞋底接触地面，脚下有柔和、方向一致的接触阴影。人物受光与背景协调，边缘自然，不漂浮，不出现抠图白边。保持背景空间，不随意增加家具、道具或墙面装饰。

成像质感：
呈现简约、干净的商业服装摄影质感，人物突出，背景安静，留白克制，整幅画面清晰通透。色彩中性自然、白平衡准确，不加明显偏色滤镜、复古颗粒、戏剧性明暗或过度虚化。造型自然松弛，同时让商品版型与面料细节易于辨认。
柔和均匀的大面积光线，适度对比，保留自然立体层次。肤色自然，皮肤柔哑光，保留细微真实纹理，不出现油膜、蜡感或厚重磨皮。
商品配色忠于参考，织纹、针织纹路、接缝和自然褶皱清楚；不凭空添加参考中没有的纹理，不靠过度锐化制造细节。全身主要部位清晰，避免景深虚化遮没商品。
只输出一张独立完整图片，不加入标题、说明、尺寸标线、水印、边框或拼图。不要复制参考图中的附加文字；商品本身的既有图案与标识按商品参考处理。
用户特殊要求及排除项：【没有则删除；有时同步覆盖前文对应默认规则，避免冲突。】
```
