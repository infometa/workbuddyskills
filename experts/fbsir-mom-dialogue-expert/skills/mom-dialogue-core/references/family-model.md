# 家庭动态模型

## Person

```yaml
person_id: PER-001
display_name: ""
aliases: []
birth_year: null
birth_year_precision: unknown
languages: []
notes: ""
```

## Relationship

```yaml
relationship_id: REL-001
person_a: PER-001
person_b: PER-002
relation_from_a: ""
relation_from_b: ""
confirmed_by: ""
status: unknown
```

## 原则

每人只建立一份档案；关系按双方视角保存；项目角色与亲属关系分开。支持自定义关系、跨语言、重组、养育、伴侣和专业机构代整理。不得自动生成未出现的人物或关系。
