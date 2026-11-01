# 工具参数与返回速查

本参考对应连接器包1.2.1，工具接口使用当前已部署服务的稳定schema；包版本不强制与MCP serverInfo.version相等。以实际tools/list及OAuth角色和scope为准，缺失即停，不编造调用。金额为整数人民币分；价格与支付可用性读取当次返回，不固定99/708。

## `penglai_get_me`

取得经OAuth验证的本人资料、真实角色和已授予scope，不接受外部user_id。

所需scope：profile:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "user": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "user_id": {
          "type": "string",
          "description": "不透明业务ID，不接受手机号替代",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[A-Za-z0-9_-]+$"
        },
        "nickname": {
          "type": "string",
          "description": ""
        },
        "phone_masked": {
          "type": "string",
          "description": ""
        },
        "role": {
          "type": "string",
          "description": "",
          "enum": [
            "user",
            "admin"
          ]
        },
        "status": {
          "type": "string",
          "description": "",
          "enum": [
            "active",
            "disabled"
          ]
        }
      },
      "required": [
        "user_id",
        "nickname",
        "phone_masked",
        "role",
        "status"
      ]
    },
    "granted_scopes": {
      "type": "array",
      "items": {
        "type": "string",
        "description": ""
      }
    }
  },
  "required": [
    "user",
    "granted_scopes"
  ]
}
```

## `penglai_get_membership`

读取本人付费、邀请权益和WorkBuddy平台的派生到期；不以连接/刷新Token延长权益。

所需scope：membership:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "platform": {
      "type": "string",
      "description": "",
      "enum": [
        "workbuddy"
      ]
    },
    "website_plan": {
      "type": "string",
      "description": "",
      "enum": [
        "invited",
        "monthly",
        "yearly",
        "expired"
      ]
    },
    "paid_expires_at": {
      "anyOf": [
        {
          "type": "string",
          "description": "UTC时间，RFC3339",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    },
    "workbuddy_invite_expires_at": {
      "anyOf": [
        {
          "type": "string",
          "description": "UTC时间，RFC3339",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    },
    "connector_expires_at": {
      "anyOf": [
        {
          "type": "string",
          "description": "UTC时间，RFC3339",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    },
    "connector_active": {
      "type": "boolean"
    },
    "payment_available": {
      "type": "boolean"
    },
    "subscription_url": {
      "type": "string",
      "description": "",
      "format": "uri"
    }
  },
  "required": [
    "platform",
    "website_plan",
    "paid_expires_at",
    "workbuddy_invite_expires_at",
    "connector_expires_at",
    "connector_active",
    "payment_available",
    "subscription_url"
  ]
}
```

## `penglai_list_my_redemptions`

分页读取本人核销记录，邀请码默认脱敏。

所需scope：invitations:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "type": "string",
      "description": "服务端分页游标，首次省略",
      "maxLength": 1024
    },
    "limit": {
      "type": "integer",
      "description": "页大小，默认20",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    }
  },
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "redemption_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "code_masked": {
            "type": "string",
            "description": ""
          },
          "platform": {
            "type": "string",
            "description": "",
            "enum": [
              "workbuddy",
              "other"
            ]
          },
          "valid_days": {
            "type": "integer",
            "description": ""
          },
          "redeemed_at": {
            "type": "string",
            "description": "UTC时间，RFC3339",
            "format": "date-time"
          },
          "expires_at": {
            "type": "string",
            "description": "UTC时间，RFC3339",
            "format": "date-time"
          }
        },
        "required": [
          "redemption_id",
          "code_masked",
          "platform",
          "valid_days",
          "redeemed_at",
          "expires_at"
        ]
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "description": ""
        },
        {
          "type": "null"
        }
      ]
    },
    "has_more": {
      "type": "boolean"
    }
  },
  "required": [
    "items",
    "next_cursor",
    "has_more"
  ]
}
```

## `penglai_list_my_orders`

分页读取本人实际订单，空库返回空列表，不造记录。

所需scope：orders:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "type": "string",
      "description": "服务端分页游标，首次省略",
      "maxLength": 1024
    },
    "limit": {
      "type": "integer",
      "description": "页大小，默认20",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "status": {
      "type": "string",
      "description": "",
      "enum": [
        "pending",
        "paid",
        "cancelled",
        "refunded"
      ]
    }
  },
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "order_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "user_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "amount_fen": {
            "type": "integer",
            "description": "",
            "minimum": 0
          },
          "currency": {
            "type": "string",
            "description": "",
            "enum": [
              "CNY"
            ]
          },
          "cycle": {
            "type": "string",
            "description": "",
            "enum": [
              "monthly",
              "yearly"
            ]
          },
          "order_status": {
            "type": "string",
            "description": "",
            "enum": [
              "pending",
              "paid",
              "cancelled",
              "refunded"
            ]
          },
          "payment_status": {
            "type": "string",
            "description": "",
            "enum": [
              "unpaid",
              "success",
              "failed"
            ]
          },
          "created_at": {
            "type": "string",
            "description": "UTC时间，RFC3339",
            "format": "date-time"
          },
          "paid_at": {
            "anyOf": [
              {
                "type": "string",
                "description": "UTC时间，RFC3339",
                "format": "date-time"
              },
              {
                "type": "null"
              }
            ]
          }
        },
        "required": [
          "order_id",
          "user_id",
          "amount_fen",
          "currency",
          "cycle",
          "order_status",
          "payment_status",
          "created_at",
          "paid_at"
        ]
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "description": ""
        },
        {
          "type": "null"
        }
      ]
    },
    "has_more": {
      "type": "boolean"
    }
  },
  "required": [
    "items",
    "next_cursor",
    "has_more"
  ]
}
```

## `penglai_get_subscription_options`

读取后台运营配置的当前月付/年付价格、期限与真实支付可用性；不是付款工具。

所需scope：membership:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "plans": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "cycle": {
            "type": "string",
            "description": "",
            "enum": [
              "monthly",
              "yearly"
            ]
          },
          "price_fen": {
            "type": "integer",
            "description": ""
          },
          "valid_days": {
            "type": "integer",
            "description": ""
          }
        },
        "required": [
          "cycle",
          "price_fen",
          "valid_days"
        ]
      }
    },
    "payment_available": {
      "type": "boolean"
    },
    "payment_message": {
      "type": "string",
      "description": ""
    },
    "subscription_url": {
      "type": "string",
      "description": "",
      "format": "uri"
    }
  },
  "required": [
    "plans",
    "payment_available",
    "payment_message",
    "subscription_url"
  ]
}
```

## `penglai_get_service_status`

读取健康、配置可用标志、连接器版本和运行模式，不返回凭证或基础设施地址。

所需scope：profile:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {},
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "service_status": {
      "type": "string",
      "description": "",
      "enum": [
        "ok",
        "degraded",
        "unavailable"
      ]
    },
    "connector_version": {
      "type": "string",
      "description": ""
    },
    "sms_configured": {
      "type": "boolean"
    },
    "payment_available": {
      "type": "boolean"
    },
    "environment": {
      "type": "string",
      "description": "",
      "enum": [
        "production",
        "staging"
      ]
    }
  },
  "required": [
    "service_status",
    "connector_version",
    "sms_configured",
    "payment_available",
    "environment"
  ]
}
```

## `penglai_get_management_overview`

管理员按业务时区读取服务器聚合用户和订单统计，不返回全量快照。

所需scope：admin:overview:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "period_days": {
      "type": "integer",
      "description": "",
      "minimum": 1,
      "maximum": 365,
      "default": 30
    }
  },
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "period_days": {
      "type": "integer",
      "description": ""
    },
    "timezone": {
      "type": "string",
      "description": "",
      "enum": [
        "Asia/Shanghai"
      ]
    },
    "users_total": {
      "type": "integer",
      "description": ""
    },
    "new_users_in_period": {
      "type": "integer",
      "description": ""
    },
    "active_paid_members": {
      "type": "integer",
      "description": ""
    },
    "orders_total": {
      "type": "integer",
      "description": ""
    },
    "paid_revenue_fen": {
      "type": "integer",
      "description": ""
    },
    "paid_revenue_in_period_fen": {
      "type": "integer",
      "description": ""
    },
    "currency": {
      "type": "string",
      "description": "",
      "enum": [
        "CNY"
      ]
    }
  },
  "required": [
    "period_days",
    "timezone",
    "users_total",
    "new_users_in_period",
    "active_paid_members",
    "orders_total",
    "paid_revenue_fen",
    "paid_revenue_in_period_fen",
    "currency"
  ]
}
```

## `penglai_search_users`

管理员按昵称、ID或手机号末4位搜索真实用户，分页且仅返回脱敏资料。

所需scope：admin:users:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "type": "string",
      "description": "服务端分页游标，首次省略",
      "maxLength": 1024
    },
    "limit": {
      "type": "integer",
      "description": "页大小，默认20",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "query": {
      "type": "string",
      "description": "昵称或ID，非完整手机号",
      "maxLength": 64
    },
    "phone_suffix": {
      "type": "string",
      "description": "只接受末4位",
      "pattern": "^[0-9]{4}$"
    },
    "status": {
      "type": "string",
      "description": "",
      "enum": [
        "active",
        "disabled"
      ]
    }
  },
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "user_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "nickname": {
            "type": "string",
            "description": ""
          },
          "phone_masked": {
            "type": "string",
            "description": ""
          },
          "role": {
            "type": "string",
            "description": "",
            "enum": [
              "user",
              "admin"
            ]
          },
          "status": {
            "type": "string",
            "description": "",
            "enum": [
              "active",
              "disabled"
            ]
          }
        },
        "required": [
          "user_id",
          "nickname",
          "phone_masked",
          "role",
          "status"
        ]
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "description": ""
        },
        {
          "type": "null"
        }
      ]
    },
    "has_more": {
      "type": "boolean"
    }
  },
  "required": [
    "items",
    "next_cursor",
    "has_more"
  ]
}
```

## `penglai_get_user`

管理员读取指定用户的脱敏基础信息，不允许任意SQL或导出全库。

所需scope：admin:users:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "user_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    }
  },
  "required": [
    "user_id"
  ]
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "user": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "user_id": {
          "type": "string",
          "description": "不透明业务ID，不接受手机号替代",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[A-Za-z0-9_-]+$"
        },
        "nickname": {
          "type": "string",
          "description": ""
        },
        "phone_masked": {
          "type": "string",
          "description": ""
        },
        "role": {
          "type": "string",
          "description": "",
          "enum": [
            "user",
            "admin"
          ]
        },
        "status": {
          "type": "string",
          "description": "",
          "enum": [
            "active",
            "disabled"
          ]
        }
      },
      "required": [
        "user_id",
        "nickname",
        "phone_masked",
        "role",
        "status"
      ]
    },
    "registered_at": {
      "type": "string",
      "description": "UTC时间，RFC3339",
      "format": "date-time"
    },
    "last_login_at": {
      "anyOf": [
        {
          "type": "string",
          "description": "UTC时间，RFC3339",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    },
    "total_spend_fen": {
      "type": "integer",
      "description": ""
    },
    "order_count": {
      "type": "integer",
      "description": ""
    }
  },
  "required": [
    "user",
    "registered_at",
    "last_login_at",
    "total_spend_fen",
    "order_count"
  ]
}
```

## `penglai_search_orders`

管理员按订单ID、用户ID或状态分页查询实际订单，不提供支付成功修改。

所需scope：admin:orders:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "type": "string",
      "description": "服务端分页游标，首次省略",
      "maxLength": 1024
    },
    "limit": {
      "type": "integer",
      "description": "页大小，默认20",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "order_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    },
    "user_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    },
    "status": {
      "type": "string",
      "description": "",
      "enum": [
        "pending",
        "paid",
        "cancelled",
        "refunded"
      ]
    }
  },
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "order_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "user_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "amount_fen": {
            "type": "integer",
            "description": "",
            "minimum": 0
          },
          "currency": {
            "type": "string",
            "description": "",
            "enum": [
              "CNY"
            ]
          },
          "cycle": {
            "type": "string",
            "description": "",
            "enum": [
              "monthly",
              "yearly"
            ]
          },
          "order_status": {
            "type": "string",
            "description": "",
            "enum": [
              "pending",
              "paid",
              "cancelled",
              "refunded"
            ]
          },
          "payment_status": {
            "type": "string",
            "description": "",
            "enum": [
              "unpaid",
              "success",
              "failed"
            ]
          },
          "created_at": {
            "type": "string",
            "description": "UTC时间，RFC3339",
            "format": "date-time"
          },
          "paid_at": {
            "anyOf": [
              {
                "type": "string",
                "description": "UTC时间，RFC3339",
                "format": "date-time"
              },
              {
                "type": "null"
              }
            ]
          }
        },
        "required": [
          "order_id",
          "user_id",
          "amount_fen",
          "currency",
          "cycle",
          "order_status",
          "payment_status",
          "created_at",
          "paid_at"
        ]
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "description": ""
        },
        {
          "type": "null"
        }
      ]
    },
    "has_more": {
      "type": "boolean"
    }
  },
  "required": [
    "items",
    "next_cursor",
    "has_more"
  ]
}
```

## `penglai_get_order`

管理员读取真实订单详情，支付流水号默认掩码，不可将未验证交易视为成功。

所需scope：admin:orders:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "order_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    }
  },
  "required": [
    "order_id"
  ]
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "order": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "order_id": {
          "type": "string",
          "description": "不透明业务ID，不接受手机号替代",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[A-Za-z0-9_-]+$"
        },
        "user_id": {
          "type": "string",
          "description": "不透明业务ID，不接受手机号替代",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[A-Za-z0-9_-]+$"
        },
        "amount_fen": {
          "type": "integer",
          "description": "",
          "minimum": 0
        },
        "currency": {
          "type": "string",
          "description": "",
          "enum": [
            "CNY"
          ]
        },
        "cycle": {
          "type": "string",
          "description": "",
          "enum": [
            "monthly",
            "yearly"
          ]
        },
        "order_status": {
          "type": "string",
          "description": "",
          "enum": [
            "pending",
            "paid",
            "cancelled",
            "refunded"
          ]
        },
        "payment_status": {
          "type": "string",
          "description": "",
          "enum": [
            "unpaid",
            "success",
            "failed"
          ]
        },
        "created_at": {
          "type": "string",
          "description": "UTC时间，RFC3339",
          "format": "date-time"
        },
        "paid_at": {
          "anyOf": [
            {
              "type": "string",
              "description": "UTC时间，RFC3339",
              "format": "date-time"
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "order_id",
        "user_id",
        "amount_fen",
        "currency",
        "cycle",
        "order_status",
        "payment_status",
        "created_at",
        "paid_at"
      ]
    },
    "transaction_id_masked": {
      "anyOf": [
        {
          "type": "string",
          "description": ""
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "order",
    "transaction_id_masked"
  ]
}
```

## `penglai_search_invitations`

管理员按批次、平台、状态分页查询邀请码，仅返回掩码，不批量泄露权益凭证。

所需scope：admin:invitations:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "type": "string",
      "description": "服务端分页游标，首次省略",
      "maxLength": 1024
    },
    "limit": {
      "type": "integer",
      "description": "页大小，默认20",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "batch_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    },
    "platform": {
      "type": "string",
      "description": "",
      "enum": [
        "workbuddy",
        "other"
      ]
    },
    "status": {
      "type": "string",
      "description": "",
      "enum": [
        "available",
        "redeemed",
        "disabled",
        "expired"
      ]
    }
  },
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "invite_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "batch_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "code_masked": {
            "type": "string",
            "description": ""
          },
          "platform": {
            "type": "string",
            "description": "",
            "enum": [
              "workbuddy",
              "other"
            ]
          },
          "valid_days": {
            "type": "integer",
            "description": "",
            "minimum": 1,
            "maximum": 3650
          },
          "status": {
            "type": "string",
            "description": "",
            "enum": [
              "available",
              "redeemed",
              "disabled",
              "expired"
            ]
          },
          "created_at": {
            "type": "string",
            "description": "UTC时间，RFC3339",
            "format": "date-time"
          },
          "redeem_before": {
            "anyOf": [
              {
                "type": "string",
                "description": "UTC时间，RFC3339",
                "format": "date-time"
              },
              {
                "type": "null"
              }
            ]
          },
          "redeemed_at": {
            "anyOf": [
              {
                "type": "string",
                "description": "UTC时间，RFC3339",
                "format": "date-time"
              },
              {
                "type": "null"
              }
            ]
          }
        },
        "required": [
          "invite_id",
          "batch_id",
          "code_masked",
          "platform",
          "valid_days",
          "status",
          "created_at",
          "redeem_before",
          "redeemed_at"
        ]
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "description": ""
        },
        {
          "type": "null"
        }
      ]
    },
    "has_more": {
      "type": "boolean"
    }
  },
  "required": [
    "items",
    "next_cursor",
    "has_more"
  ]
}
```

## `penglai_get_invitation`

管理员读取单码及核销详情，手机号与邀请码保持掩码。

所需scope：admin:invitations:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "invite_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    }
  },
  "required": [
    "invite_id"
  ]
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "invitation": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "invite_id": {
          "type": "string",
          "description": "不透明业务ID，不接受手机号替代",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[A-Za-z0-9_-]+$"
        },
        "batch_id": {
          "type": "string",
          "description": "不透明业务ID，不接受手机号替代",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[A-Za-z0-9_-]+$"
        },
        "code_masked": {
          "type": "string",
          "description": ""
        },
        "platform": {
          "type": "string",
          "description": "",
          "enum": [
            "workbuddy",
            "other"
          ]
        },
        "valid_days": {
          "type": "integer",
          "description": "",
          "minimum": 1,
          "maximum": 3650
        },
        "status": {
          "type": "string",
          "description": "",
          "enum": [
            "available",
            "redeemed",
            "disabled",
            "expired"
          ]
        },
        "created_at": {
          "type": "string",
          "description": "UTC时间，RFC3339",
          "format": "date-time"
        },
        "redeem_before": {
          "anyOf": [
            {
              "type": "string",
              "description": "UTC时间，RFC3339",
              "format": "date-time"
            },
            {
              "type": "null"
            }
          ]
        },
        "redeemed_at": {
          "anyOf": [
            {
              "type": "string",
              "description": "UTC时间，RFC3339",
              "format": "date-time"
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "invite_id",
        "batch_id",
        "code_masked",
        "platform",
        "valid_days",
        "status",
        "created_at",
        "redeem_before",
        "redeemed_at"
      ]
    },
    "redemption": {
      "anyOf": [
        {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "redemption_id": {
              "type": "string",
              "description": "不透明业务ID，不接受手机号替代",
              "minLength": 1,
              "maxLength": 64,
              "pattern": "^[A-Za-z0-9_-]+$"
            },
            "code_masked": {
              "type": "string",
              "description": ""
            },
            "platform": {
              "type": "string",
              "description": "",
              "enum": [
                "workbuddy",
                "other"
              ]
            },
            "valid_days": {
              "type": "integer",
              "description": ""
            },
            "redeemed_at": {
              "type": "string",
              "description": "UTC时间，RFC3339",
              "format": "date-time"
            },
            "expires_at": {
              "type": "string",
              "description": "UTC时间，RFC3339",
              "format": "date-time"
            }
          },
          "required": [
            "redemption_id",
            "code_masked",
            "platform",
            "valid_days",
            "redeemed_at",
            "expires_at"
          ]
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "invitation",
    "redemption"
  ]
}
```

## `penglai_list_invitation_batches`

管理员分页查询批次数量、平台、权益天数、最晚核销时间与创建时间。

所需scope：admin:invitations:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "type": "string",
      "description": "服务端分页游标，首次省略",
      "maxLength": 1024
    },
    "limit": {
      "type": "integer",
      "description": "页大小，默认20",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "platform": {
      "type": "string",
      "description": "",
      "enum": [
        "workbuddy",
        "other"
      ]
    }
  },
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "batch_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "quantity": {
            "type": "integer",
            "description": "",
            "minimum": 1,
            "maximum": 500
          },
          "platform": {
            "type": "string",
            "description": "",
            "enum": [
              "workbuddy",
              "other"
            ]
          },
          "valid_days": {
            "type": "integer",
            "description": "",
            "minimum": 1,
            "maximum": 3650
          },
          "created_at": {
            "type": "string",
            "description": "UTC时间，RFC3339",
            "format": "date-time"
          },
          "redeem_before": {
            "anyOf": [
              {
                "type": "string",
                "description": "UTC时间，RFC3339",
                "format": "date-time"
              },
              {
                "type": "null"
              }
            ]
          }
        },
        "required": [
          "batch_id",
          "quantity",
          "platform",
          "valid_days",
          "created_at",
          "redeem_before"
        ]
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "description": ""
        },
        {
          "type": "null"
        }
      ]
    },
    "has_more": {
      "type": "boolean"
    }
  },
  "required": [
    "items",
    "next_cursor",
    "has_more"
  ]
}
```

## `penglai_list_audit_events`

管理员分页查询实际操作事件。参数变更、Token、Cookie、验证码及邀请码明文不得进入返回。

所需scope：admin:audit:read

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "cursor": {
      "type": "string",
      "description": "服务端分页游标，首次省略",
      "maxLength": 1024
    },
    "limit": {
      "type": "integer",
      "description": "页大小，默认20",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "event_type": {
      "type": "string",
      "description": "",
      "maxLength": 64
    },
    "actor_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    }
  },
  "required": []
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "event_id": {
            "type": "string",
            "description": "不透明业务ID，不接受手机号替代",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[A-Za-z0-9_-]+$"
          },
          "actor_id": {
            "anyOf": [
              {
                "type": "string",
                "description": "不透明业务ID，不接受手机号替代",
                "minLength": 1,
                "maxLength": 64,
                "pattern": "^[A-Za-z0-9_-]+$"
              },
              {
                "type": "null"
              }
            ]
          },
          "target_user_id": {
            "anyOf": [
              {
                "type": "string",
                "description": "不透明业务ID，不接受手机号替代",
                "minLength": 1,
                "maxLength": 64,
                "pattern": "^[A-Za-z0-9_-]+$"
              },
              {
                "type": "null"
              }
            ]
          },
          "event_type": {
            "type": "string",
            "description": ""
          },
          "summary": {
            "type": "string",
            "description": ""
          },
          "created_at": {
            "type": "string",
            "description": "UTC时间，RFC3339",
            "format": "date-time"
          }
        },
        "required": [
          "event_id",
          "actor_id",
          "target_user_id",
          "event_type",
          "summary",
          "created_at"
        ]
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "description": ""
        },
        {
          "type": "null"
        }
      ]
    },
    "has_more": {
      "type": "boolean"
    }
  },
  "required": [
    "items",
    "next_cursor",
    "has_more"
  ]
}
```

## `penglai_prepare_action`

校验作用域、目标归属和参数，生成不可更改操作单；不执行业务写入，也不接受confirmed或approved参数。

所需scope：按action要求

参数：

```json
{
  "oneOf": [
    {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action": {
          "const": "update_my_nickname"
        },
        "request_id": {
          "type": "string",
          "description": "每个新操作UUID；同操作重试保持相同",
          "format": "uuid"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "nickname": {
              "type": "string",
              "description": "去首尾空格后1-64字符",
              "minLength": 1,
              "maxLength": 64
            }
          },
          "required": [
            "nickname"
          ]
        }
      },
      "required": [
        "action",
        "request_id",
        "parameters"
      ]
    },
    {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action": {
          "const": "redeem_invitation"
        },
        "request_id": {
          "type": "string",
          "description": "每个新操作UUID；同操作重试保持相同",
          "format": "uuid"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "code": {
              "type": "string",
              "description": "真实邀请码，只作核销参数，不在结果/日志复述",
              "minLength": 1,
              "maxLength": 64,
              "pattern": "^[A-Za-z0-9-]+$"
            }
          },
          "required": [
            "code"
          ]
        }
      },
      "required": [
        "action",
        "request_id",
        "parameters"
      ]
    },
    {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action": {
          "const": "cancel_my_order"
        },
        "request_id": {
          "type": "string",
          "description": "每个新操作UUID；同操作重试保持相同",
          "format": "uuid"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "order_id": {
              "type": "string",
              "description": "不透明业务ID，不接受手机号替代",
              "minLength": 1,
              "maxLength": 64,
              "pattern": "^[A-Za-z0-9_-]+$"
            }
          },
          "required": [
            "order_id"
          ]
        }
      },
      "required": [
        "action",
        "request_id",
        "parameters"
      ]
    },
    {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action": {
          "const": "create_invite_batch"
        },
        "request_id": {
          "type": "string",
          "description": "每个新操作UUID；同操作重试保持相同",
          "format": "uuid"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "quantity": {
              "type": "integer",
              "description": "",
              "minimum": 1,
              "maximum": 500,
              "default": 1
            },
            "platform": {
              "type": "string",
              "description": "",
              "enum": [
                "workbuddy",
                "other"
              ],
              "default": "workbuddy"
            },
            "valid_days": {
              "type": "integer",
              "description": "",
              "minimum": 1,
              "maximum": 3650,
              "default": 7
            },
            "redeem_before": {
              "type": "string",
              "description": "UTC时间，RFC3339",
              "format": "date-time"
            }
          },
          "required": [
            "quantity",
            "platform",
            "valid_days"
          ]
        }
      },
      "required": [
        "action",
        "request_id",
        "parameters"
      ]
    },
    {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action": {
          "const": "set_user_status"
        },
        "request_id": {
          "type": "string",
          "description": "每个新操作UUID；同操作重试保持相同",
          "format": "uuid"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "user_id": {
              "type": "string",
              "description": "不透明业务ID，不接受手机号替代",
              "minLength": 1,
              "maxLength": 64,
              "pattern": "^[A-Za-z0-9_-]+$"
            },
            "status": {
              "type": "string",
              "description": "",
              "enum": [
                "active",
                "disabled"
              ]
            }
          },
          "required": [
            "user_id",
            "status"
          ]
        }
      },
      "required": [
        "action",
        "request_id",
        "parameters"
      ]
    },
    {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action": {
          "const": "disable_invitation"
        },
        "request_id": {
          "type": "string",
          "description": "每个新操作UUID；同操作重试保持相同",
          "format": "uuid"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "invite_id": {
              "type": "string",
              "description": "不透明业务ID，不接受手机号替代",
              "minLength": 1,
              "maxLength": 64,
              "pattern": "^[A-Za-z0-9_-]+$"
            }
          },
          "required": [
            "invite_id"
          ]
        }
      },
      "required": [
        "action",
        "request_id",
        "parameters"
      ]
    },
    {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action": {
          "const": "update_user_nickname"
        },
        "request_id": {
          "type": "string",
          "description": "每个新操作UUID；同操作重试保持相同",
          "format": "uuid"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "user_id": {
              "type": "string",
              "description": "不透明业务ID，不接受手机号替代",
              "minLength": 1,
              "maxLength": 64,
              "pattern": "^[A-Za-z0-9_-]+$"
            },
            "nickname": {
              "type": "string",
              "description": "",
              "minLength": 1,
              "maxLength": 64
            }
          },
          "required": [
            "user_id",
            "nickname"
          ]
        }
      },
      "required": [
        "action",
        "request_id",
        "parameters"
      ]
    },
    {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action": {
          "const": "export_invite_batch"
        },
        "request_id": {
          "type": "string",
          "description": "每个新操作UUID；同操作重试保持相同",
          "format": "uuid"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "batch_id": {
              "type": "string",
              "description": "不透明业务ID，不接受手机号替代",
              "minLength": 1,
              "maxLength": 64,
              "pattern": "^[A-Za-z0-9_-]+$"
            }
          },
          "required": [
            "batch_id"
          ]
        }
      },
      "required": [
        "action",
        "request_id",
        "parameters"
      ]
    }
  ]
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action_id": {
          "type": "string",
          "description": "不透明业务ID，不接受手机号替代",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[A-Za-z0-9_-]+$"
        },
        "action": {
          "type": "string",
          "description": "",
          "enum": [
            "update_my_nickname",
            "redeem_invitation",
            "cancel_my_order",
            "create_invite_batch",
            "set_user_status",
            "disable_invitation",
            "update_user_nickname",
            "export_invite_batch"
          ]
        },
        "status": {
          "type": "string",
          "description": "",
          "enum": [
            "prepared",
            "approved",
            "executing",
            "succeeded",
            "failed",
            "rejected",
            "expired"
          ]
        },
        "expires_at": {
          "type": "string",
          "description": "UTC时间，RFC3339",
          "format": "date-time"
        },
        "summary": {
          "type": "string",
          "description": ""
        },
        "confirmation_url": {
          "anyOf": [
            {
              "type": "string",
              "description": "",
              "format": "uri"
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "action_id",
        "action",
        "status",
        "expires_at",
        "summary",
        "confirmation_url"
      ]
    }
  },
  "required": [
    "action"
  ]
}
```

## `penglai_get_action_status`

仅查询同一OAuth用户与客户端绑定操作的人工批准结果，不自动轮询或代用户点击确认。

所需scope：与原action一致

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    }
  },
  "required": [
    "action_id"
  ]
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "action_id": {
          "type": "string",
          "description": "不透明业务ID，不接受手机号替代",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[A-Za-z0-9_-]+$"
        },
        "action": {
          "type": "string",
          "description": "",
          "enum": [
            "update_my_nickname",
            "redeem_invitation",
            "cancel_my_order",
            "create_invite_batch",
            "set_user_status",
            "disable_invitation",
            "update_user_nickname",
            "export_invite_batch"
          ]
        },
        "status": {
          "type": "string",
          "description": "",
          "enum": [
            "prepared",
            "approved",
            "executing",
            "succeeded",
            "failed",
            "rejected",
            "expired"
          ]
        },
        "expires_at": {
          "type": "string",
          "description": "UTC时间，RFC3339",
          "format": "date-time"
        },
        "summary": {
          "type": "string",
          "description": ""
        },
        "confirmation_url": {
          "anyOf": [
            {
              "type": "string",
              "description": "",
              "format": "uri"
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "action_id",
        "action",
        "status",
        "expires_at",
        "summary",
        "confirmation_url"
      ]
    }
  },
  "required": [
    "action"
  ]
}
```

## `penglai_execute_action`

只执行服务端已批准且未过期的不可变操作单；事务内再次校验身份/权限/归属，并保证重试不重复核销或生成。

所需scope：与原action一致

参数：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    }
  },
  "required": [
    "action_id"
  ]
}
```

data返回：

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action_id": {
      "type": "string",
      "description": "不透明业务ID，不接受手机号替代",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9_-]+$"
    },
    "status": {
      "type": "string",
      "description": "",
      "enum": [
        "succeeded"
      ]
    },
    "result": {
      "type": "object",
      "description": "详见各action结果契约，禁止Token/OTP/手机号/邀请码明文",
      "additionalProperties": true
    }
  },
  "required": [
    "action_id",
    "status",
    "result"
  ]
}
```

## OAuth连接与恢复说明（2026-10-22）

本包版本为1.2.1，正式服务OAuth审核兼容及授权网页完成状态修复已部署，提交为`4a9081ec2cf295ddf621c0901ea8f01fef32add2`。
已支持通用WorkBuddy回调、朋来精确回调的编码/未编码形式及限定IPv4/IPv6 loopback；S256 verifier支持RFC合法字符。
回调需保持注册和原授权绑定，不能循环解码、替换回调或绕过PKCE。

协议发现、DCR、授权码交换及Token刷新交给WorkBuddy客户端处理。
授权失败时引导用户在连接器界面亲自完成新的浏览器授权；不得读取本地凭据、索取code/verifier/Token、构造token请求或为了接通而修改认证模式。
新授权页会显示已确认授权并引导返回客户端；网页提交成功不等于MCP已连接，应以客户端连接状态和实际工具发现为准。

此次服务修复已发布，197项隔离回归与真实数据库临时表合法交换验证通过，但官方复审和新包实际安装不能据此标为通过。
`service_unavailable`不得视为正常空列表，禁止用旧版本业务查询成功冒充当前包验证。价格及支付状态继续以当次工具返回为准。
