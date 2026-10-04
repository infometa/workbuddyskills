# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "marketplace"
  ],
  "properties": {
    "sort": {
      "type": "string",
      "examples": [
        {
          "value": "name",
          "summary": "名称升序(默认)"
        },
        {
          "value": "-name",
          "summary": "名称降序"
        },
        {
          "value": "category",
          "summary": "类目升序"
        },
        {
          "value": "-category",
          "summary": "类目降序"
        },
        {
          "value": "revenue",
          "summary": "收入升序"
        },
        {
          "value": "-revenue",
          "summary": "收入降序"
        },
        {
          "value": "sales",
          "summary": "销量升序"
        },
        {
          "value": "-sales",
          "summary": "销量降序"
        },
        {
          "value": "price",
          "summary": "价格升序"
        },
        {
          "value": "-price",
          "summary": "价格降序"
        },
        {
          "value": "rank",
          "summary": "排名升序"
        },
        {
          "value": "-rank",
          "summary": "排名降序"
        },
        {
          "value": "reviews",
          "summary": "评论数升序"
        },
        {
          "value": "-reviews",
          "summary": "评论数降序"
        },
        {
          "value": "lqs",
          "summary": "列表质量分升序"
        },
        {
          "value": "-lqs",
          "summary": "列表质量分降序"
        },
        {
          "value": "sellers",
          "summary": "卖家数升序"
        },
        {
          "value": "-sellers",
          "summary": "卖家数降序"
        }
      ],
      "maxLength": 1000,
      "description": "排序字段。可选值: name, -name, category, -category, revenue, -revenue, sales, -sales, price, -price, rank, -rank, reviews, -reviews, lqs, -lqs, sellers, -sellers。默认: name"
    },
    "maxLqs": {
      "type": "integer",
      "description": "最高列表质量分 LQS(1-10)"
    },
    "maxNet": {
      "type": "number",
      "description": "最高净利润(价减FBA费等)"
    },
    "minLqs": {
      "type": "integer",
      "description": "最低列表质量分 LQS(1-10)"
    },
    "minNet": {
      "type": "number",
      "description": "最低净利润(价减FBA费等)"
    },
    "maxRank": {
      "type": "integer",
      "description": "最高 BSR 排名"
    },
    "minRank": {
      "type": "integer",
      "description": "最低 BSR 排名"
    },
    "maxPrice": {
      "type": "number",
      "description": "最高价格"
    },
    "maxSales": {
      "type": "integer",
      "description": "最高月销量估算"
    },
    "minPrice": {
      "type": "number",
      "description": "最低价格"
    },
    "minSales": {
      "type": "integer",
      "description": "最低月销量估算"
    },
    "maxRating": {
      "type": "number",
      "description": "最高星级评分(1.0-5.0)"
    },
    "maxWeight": {
      "type": "number",
      "description": "最大重量(磅)"
    },
    "minRating": {
      "type": "number",
      "description": "最低星级评分(1.0-5.0)"
    },
    "minWeight": {
      "type": "number",
      "description": "最小重量(磅)"
    },
    "needCount": {
      "type": "integer",
      "description": "需要返回的总条数(系统内部自动分页拉取)"
    },
    "categories": {
      "type": "string",
      "examples": [
        {
          "value": "Electronics",
          "summary": "单类目(us)"
        },
        {
          "value": "Baby,Toys & Games",
          "summary": "多类目(us)"
        }
      ],
      "maxLength": 1000,
      "description": "主类目筛选，多值逗号分隔；为空表示不限。须与所选 marketplace 下官方类目名称完全一致。 us marketplace: Appliances,Arts, Crafts & Sewing,Automotive,Baby,Beauty & Personal Care,Camera & Photo,Cell Phones & Accessories,Clothing, Shoes & Jewelry,Computers & Accessories,Electronics,Grocery & Gourmet Food,Health & Household,Home & Kitchen,Industrial & Scientific,Kitchen & Dining,Musical Instruments,Office Products,Patio, Lawn & Garden,Pet Supplies,Software,Sports & Outdoors,Tools & Home Improvement,Toys & Games,Video Games uk marketplace: Automotive,Baby Products,Beauty,Business, Industry & Science,Fashion,Computers & Accessories,DIY & Tools,Electronics & Photo,Garden,Grocery,Health & Personal Care,Home & Kitchen,Jewellery,Large Appliances,Lighting,Luggage,Musical Instruments & DJ,PC & Video Games,Pet Supplies,Shoes & Bags,Sports & Outdoors,Stationery & Office Supplies,Toys & Games,Watches ca marketplace: Automotive,Baby,Beauty & Personal Care,Clothing & Accessories,Electronics,Grocery & Gourmet Food,Health & Personal Care,Industrial & Scientific,Jewelry,Luggage & Bags,Musical Instruments, Stage & Studio,Office Products,Patio, Lawn & Garden,Pet Supplies,Shoes & Handbags,Sports & Outdoors,Tools & Home Improvement,Toys & Games,Watches de marketplace: Auto & Motorrad,Baby,Baumarkt,Beauty,Bekleidung,Beleuchtung,Bücher,Bürobedarf & Schreibwaren,Computer & Zubehör,DVD & Blu-ray,Drogerie & Körperpflege,Elektro-Großgeräte,Elektronik & Foto,Fremdsprachige Bücher,Games,Garten,Gewerbe, Industrie & Wissenschaft,Haustier,Kamera & Foto,Koffer, Rucksäcke & Taschen,Küche, Haushalt & Wohnen,Lebensmittel & Getränke,Musikinstrumente & DJ-Equipment,Schmuck,Schuhe & Handtaschen,Software,Spielzeug,Sport & Freizeit,Uhren fr marketplace: Animalerie,Auto & Moto,Bagages,Beauté & Parfum,Bijoux,Bricolage,Bébé et Puériculture,Chaussures & Sacs,Commerce, Industrie & Science,Cuisine & Maison,DVD & Blu-ray,Epicerie,Fournitures de bureau,Gros électroménager,High-tech,Hygiène & Santé,Informatique,Instruments de musique & Sono,Jardin,Jeux & Jouets,Jeux vidéo,Livres,Livres anglais & étrangers,Logiciels,Luminaires & Eclairage,Montres,Sports & Loisirs,Vêtements in marketplace: Baby,Baby Products,Bags, Wallets & Luggage,Beauty,Books,Car & Motorbike,Clothing & Accessories,Electronics,Gift Cards,Grocery & Gourmet Foods,Health & Personal Care,Home & Kitchen,Industrial & Scientific,Jewellery,Movies & TV Shows,Music,Musical Instruments,Office Products,Pet Supplies,Shoes & Handbags,Software,Sports, Fitness & Outdoors,Toys & Games,Video Games,Watches it marketplace: Abbigliamento,Alimentari e cura della casa,Auto e Moto,Bellezza,Buoni regalo,CD e Vinili,Casa e cucina,Commercio, Industria e Scienza,Elettronica,Fai da te,Film e TV,Giardino e giardinaggio,Giochi e giocattoli,Gioielli,Illuminazione,Informatica,Kindle Store,Libri,Libri in altre lingue,Orologi,Prima infanzia,Salute e cura della persona,Scarpe e borse,Software,Sport e tempo libero,Valigeria,Videogiochi es marketplace: Apps y Juegos,Bebé,Belleza,Bricolaje y herramientas,Coche y moto,Deportes y aire libre,Electrónica,Equipaje,Hogar y cocina,Iluminación,Industria, empresas y ciencia,Informática,Instrumentos musicales,Jardín,Joyería,Juguetes y juegos,Libros,Oficina y papelería,Películas y TV,Relojes,Ropa,Salud y cuidado personal,Software,Tienda Kindle,Videojuegos,Zapatos y complementos mx marketplace: Bebé,Deportes y Aire Libre,Electrónicos,Herramientas y Mejoras del Hogar,Hogar y Cocina,Industria, Empresas y Ciencia,Instrumentos Musicales,Juguetes y Juegos,Libros,Música,Oficina y papelería,Ropa, Zapatos y Accesorios,Salud, Belleza y Cuidado Personal,Software,Tienda Kindle,Videojuegos jp marketplace: DIY・工具・ガーデン,おもちゃ,シューズ&バッグ,ジュエリー,スポーツ&アウトドア,ドラッグストア,ビューティー,ベビー&マタニティ,ペット用品,ホビー,ホーム&キッチン,大型家電,家電&カメラ,文房具・オフィス用品,服&ファッション小物,産業・研究開発用品,腕時計,車&バイク,食品・飲料・お酒"
    },
    "maxRevenue": {
      "type": "number",
      "description": "最高月收入估算"
    },
    "maxReviews": {
      "type": "integer",
      "description": "最多评论数"
    },
    "maxSellers": {
      "type": "integer",
      "description": "最多卖家数"
    },
    "minRevenue": {
      "type": "number",
      "description": "最低月收入估算"
    },
    "minReviews": {
      "type": "integer",
      "description": "最少评论数"
    },
    "minSellers": {
      "type": "integer",
      "description": "最少卖家数(FBA+FBM+AMZ合计)"
    },
    "marketplace": {
      "type": "string",
      "examples": [
        {
          "value": "us",
          "summary": "美国"
        },
        {
          "value": "uk",
          "summary": "英国"
        },
        {
          "value": "de",
          "summary": "德国"
        },
        {
          "value": "in",
          "summary": "印度"
        },
        {
          "value": "ca",
          "summary": "加拿大"
        },
        {
          "value": "fr",
          "summary": "法国"
        },
        {
          "value": "it",
          "summary": "意大利"
        },
        {
          "value": "es",
          "summary": "西班牙"
        },
        {
          "value": "mx",
          "summary": "墨西哥"
        },
        {
          "value": "jp",
          "summary": "日本"
        }
      ],
      "maxLength": 1000,
      "description": "目标市场代码"
    },
    "sellerTypes": {
      "type": "string",
      "examples": [
        {
          "value": "fba,fbm",
          "summary": "FBA与FBM"
        }
      ],
      "maxLength": 1000,
      "description": "卖家履约类型，多值逗号分隔；可选 amz(亚马逊), fba, fbm"
    },
    "maxUpdatedAt": {
      "type": "string",
      "examples": [
        {
          "value": "2020-09-29",
          "summary": "示例"
        }
      ],
      "maxLength": 1000,
      "description": "产品最晚更新日期(YYYY-MM-DD)"
    },
    "minUpdatedAt": {
      "type": "string",
      "examples": [
        {
          "value": "2020-09-28",
          "summary": "示例"
        }
      ],
      "maxLength": 1000,
      "description": "产品最早更新日期(YYYY-MM-DD)"
    },
    "productTiers": {
      "type": "string",
      "examples": [
        {
          "value": "standard",
          "summary": "标准件"
        },
        {
          "value": "oversize,standard",
          "summary": "多选"
        }
      ],
      "maxLength": 1000,
      "description": "产品规格层级，多值逗号分隔；可选 oversize, standard"
    },
    "excludeKeywords": {
      "type": "string",
      "examples": [
        {
          "value": "sushi,ramen",
          "summary": "排除示例"
        }
      ],
      "maxLength": 1000,
      "description": "标题排除的关键词或ASIN，多值逗号分隔(单条最长50字符，最多100项)"
    },
    "includeKeywords": {
      "type": "string",
      "examples": [
        {
          "value": "pasta,spaghetti",
          "summary": "关键词示例"
        }
      ],
      "maxLength": 1000,
      "description": "标题包含的关键词或ASIN，多值逗号分隔(单条最长50字符，最多100项)"
    },
    "excludeTopBrands": {
      "type": "boolean",
      "examples": [
        {
          "value": "false",
          "summary": "默认不排除"
        },
        {
          "value": "true",
          "summary": "排除"
        }
      ],
      "description": "是否排除头部品牌"
    },
    "excludeUnavailableProducts": {
      "type": "boolean",
      "examples": [
        {
          "value": "false",
          "summary": "默认不排除"
        },
        {
          "value": "true",
          "summary": "排除"
        }
      ],
      "description": "是否排除缺货/不可售产品"
    }
  }
}
```

</details>

## 原始 Output Schema

<details>
<summary>展开查看完整 Output Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "productDatabaseList": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "id": {
            "type": "string",
            "description": "产品唯一标识(市场/ASIN)"
          },
          "type": {
            "type": "string",
            "description": "响应资源类型(固定 product_database_result)"
          },
          "brand": {
            "type": "string",
            "description": "品牌名称"
          },
          "price": {
            "type": "number",
            "description": "当前售价"
          },
          "title": {
            "type": "string",
            "description": "产品完整标题"
          },
          "rating": {
            "type": "number",
            "description": "平均评分(1-5星)"
          },
          "eanList": {
            "type": "array",
            "items": {},
            "description": "EAN 列表"
          },
          "reviews": {
            "type": "integer",
            "description": "评论总数"
          },
          "upcList": {
            "type": "array",
            "items": {},
            "description": "UPC 列表"
          },
          "category": {
            "type": "string",
            "description": "产品主要类别"
          },
          "gtinList": {
            "type": "array",
            "items": {},
            "description": "GTIN 列表"
          },
          "imageUrl": {
            "type": "string",
            "description": "产品主图链接"
          },
          "isParent": {
            "type": "boolean",
            "description": "是否父ASIN"
          },
          "isbnList": {
            "type": "array",
            "items": {},
            "description": "ISBN 列表"
          },
          "variants": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "isVariant": {
            "type": "boolean",
            "description": "是否变体ASIN"
          },
          "updatedAt": {
            "type": "string",
            "description": "数据最后更新时间"
          },
          "parentAsin": {
            "type": "string",
            "description": "父产品ASIN"
          },
          "sellerType": {
            "type": "string",
            "description": "卖家履约类型(FBA/FBM/AMZ)"
          },
          "weightUnit": {
            "type": "string",
            "description": "重量单位"
          },
          "widthValue": {
            "type": "number",
            "description": "包装宽度"
          },
          "buyBoxOwner": {
            "type": "string",
            "description": "购物车(Buy Box)拥有者"
          },
          "heightValue": {
            "type": "number",
            "description": "包装高度"
          },
          "isAvailable": {
            "type": "boolean",
            "description": "是否有库存/可购买"
          },
          "lengthValue": {
            "type": "number",
            "description": "包装长度"
          },
          "productRank": {
            "type": "integer",
            "description": "类别内销售排名(BSR)"
          },
          "weightValue": {
            "type": "number",
            "description": "重量数值"
          },
          "feeBreakdown": {
            "type": "object",
            "required": [],
            "properties": {
              "fbaFee": {
                "type": "number",
                "description": "FBA 费用"
              },
              "totalFees": {
                "type": "number",
                "description": "费用合计"
              },
              "referralFee": {
                "type": "number",
                "description": "推荐费"
              },
              "variableClosingFee": {
                "type": "number",
                "description": "变动结算费"
              }
            }
          },
          "isStandalone": {
            "type": "boolean",
            "description": "是否独立ASIN"
          },
          "breadcrumbPath": {
            "type": "string",
            "description": "分类面包屑路径"
          },
          "dimensionsUnit": {
            "type": "string",
            "description": "尺寸单位"
          },
          "variantReviews": {
            "type": "integer",
            "description": "变体评论数(仅变体时有值)"
          },
          "numberOfSellers": {
            "type": "integer",
            "description": "卖家数量"
          },
          "subcategoryRanks": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "id": {
                  "type": "string",
                  "description": "子类目节点ID"
                },
                "rank": {
                  "type": "number",
                  "description": "在该子类目中的排名"
                },
                "subcategory": {
                  "type": "string",
                  "description": "子类目名称"
                }
              }
            },
            "description": "子类目排名列表"
          },
          "dateFirstAvailable": {
            "type": "string",
            "description": "首次上架日期(YYYY-MM-DD)"
          },
          "buyBoxOwnerSellerId": {
            "type": "string",
            "description": "购物车卖家ID"
          },
          "listingQualityScore": {
            "type": "integer",
            "description": "列表质量评分(LQS)"
          },
          "approximate30DayRevenue": {
            "type": "number",
            "description": "近30天收入估算(USD)"
          },
          "approximate30DayUnitsSold": {
            "type": "integer",
            "description": "近30天销量估算"
          },
          "dateFirstAvailableIsEstimated": {
            "type": "boolean",
            "description": "首次上架日期是否为估算值"
          }
        }
      },
      "description": "产品库查询结果列表"
    }
  }
}
```

</details>
