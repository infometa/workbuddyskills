---
slug: shopify-admin-api
display_name: Shopify Admin API
version: 1.0.0
tags: [latest]
---

# Shopify Admin API

## Description

Full read/write access to Shopify Admin REST API for managing orders, products, customers, inventory, fulfillments, refunds, returns, and transactions.

## Setup

### Environment Variables

- `SHOPIFY_STORE_DOMAIN` - Your store's myshopify.com domain (e.g., `my-store.myshopify.com`)
- `SHOPIFY_ACCESS_TOKEN` - Admin API access token from custom app

### Required API Scopes

| Scope | Access |
|-------|--------|
| `read_orders` / `write_orders` | Orders, Fulfillments, Abandoned Checkouts |
| `read_products` / `write_products` | Products, Variants, Collections |
| `read_customers` / `write_customers` | Customers, Segments |
| `read_inventory` / `write_inventory` | Inventory Levels, Items |
| `read_returns` / `write_returns` | Returns |
| `read_all_orders` | Orders older than 60 days (requires approval) |

### Authentication

All requests require this header:

```
X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN
```

### Getting an Access Token

1. Go to your Shopify Admin > Settings > Apps and sales channels
2. Click "Develop apps" > "Create an app"
3. Configure Admin API scopes based on what you need
4. Install the app to your store
5. Copy the Admin API access token

## API Reference

Base URL: `https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10`

### Orders

#### List Orders

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

Query parameters: `ids`, `limit`, `since_id`, `created_at_min`, `created_at_max`, `updated_at_min`, `updated_at_max`, `processed_at_min`, `processed_at_max`, `status` (open, closed, cancelled, any), `financial_status`, `fulfillment_status`, `fields`

#### Get Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Order Count

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/count.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Update Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{"order":{"id":{ORDER_ID},"note":"Updated note","tags":"priority,vip"}}'
```

#### Close Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/close.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -X POST
```

#### Re-open Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/open.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -X POST
```

#### Cancel Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/cancel.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"reason":"customer","email":true,"restock":true}'
```

Cancel reasons: `customer`, `fraud`, `inventory`, `declined`, `other`

### Products

#### List Products

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

Query parameters: `ids`, `limit`, `since_id`, `title`, `vendor`, `handle`, `product_type`, `collection_id`, `created_at_min`, `created_at_max`, `updated_at_min`, `updated_at_max`, `published_at_min`, `published_at_max`, `published_status` (published, unpublished, any), `fields`, `status` (active, archived, draft)

#### Get Product

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products/{PRODUCT_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Product Count

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products/count.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Create Product

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"product":{"title":"Burton Custom Freestyle","body_html":"<strong>Good snowboard!</strong>","vendor":"Burton","product_type":"Snowboard","status":"draft","variants":[{"price":"99.99","sku":"BOARD-001"}]}}'
```

#### Update Product

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products/{PRODUCT_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{"product":{"id":{PRODUCT_ID},"title":"Updated Product Title","status":"active"}}'
```

#### Delete Product

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products/{PRODUCT_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -X DELETE
```

### Product Variants

#### List Variants for Product

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products/{PRODUCT_ID}/variants.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Variant

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/variants/{VARIANT_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Create Variant

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products/{PRODUCT_ID}/variants.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"variant":{"option1":"Blue","price":"19.99","sku":"BLUE-001","inventory_management":"shopify"}}'
```

#### Update Variant

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/variants/{VARIANT_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{"variant":{"id":{VARIANT_ID},"price":"24.99","compare_at_price":"29.99"}}'
```

#### Delete Variant

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products/{PRODUCT_ID}/variants/{VARIANT_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -X DELETE
```

### Customers

#### List Customers

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/customers.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

Query parameters: `ids`, `limit`, `since_id`, `created_at_min`, `created_at_max`, `updated_at_min`, `updated_at_max`, `fields`

#### Search Customers

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/customers/search.json?query=email:customer@example.com" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

Search fields: `email`, `phone`, `first_name`, `last_name`, `company`, `orders_count`, `total_spent`, `country`, `state`

#### Get Customer

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/customers/{CUSTOMER_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Customer Count

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/customers/count.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Create Customer

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/customers.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"customer":{"first_name":"John","last_name":"Doe","email":"john.doe@example.com","phone":"+15551234567","addresses":[{"address1":"123 Main St","city":"Ottawa","province":"ON","country":"CA","zip":"K1A 0B1"}]}}'
```

#### Update Customer

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/customers/{CUSTOMER_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{"customer":{"id":{CUSTOMER_ID},"tags":"vip,wholesale","note":"Important customer"}}'
```

#### Delete Customer

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/customers/{CUSTOMER_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -X DELETE
```

#### Get Customer Orders

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/customers/{CUSTOMER_ID}/orders.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

### Inventory

#### List Inventory Levels

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/inventory_levels.json?inventory_item_ids={ITEM_ID}" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

Query parameters: `inventory_item_ids` (required), `location_ids`, `limit`, `updated_at_min`

#### Adjust Inventory Level

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/inventory_levels/adjust.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"location_id":{LOCATION_ID},"inventory_item_id":{ITEM_ID},"available_adjustment":5}'
```

#### Set Inventory Level

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/inventory_levels/set.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"location_id":{LOCATION_ID},"inventory_item_id":{ITEM_ID},"available":100}'
```

#### Connect Inventory to Location

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/inventory_levels/connect.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"location_id":{LOCATION_ID},"inventory_item_id":{ITEM_ID}}'
```

### Inventory Items

#### List Inventory Items

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/inventory_items.json?ids={ITEM_IDS}" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Inventory Item

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/inventory_items/{ITEM_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Update Inventory Item

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/inventory_items/{ITEM_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{"inventory_item":{"id":{ITEM_ID},"cost":"25.00","tracked":true}}'
```

### Locations

#### List Locations

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/locations.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Location

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/locations/{LOCATION_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Location Count

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/locations/count.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Inventory Levels for Location

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/locations/{LOCATION_ID}/inventory_levels.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

### Fulfillments

#### List Fulfillments for Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/fulfillments.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Fulfillment

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/fulfillments/{FULFILLMENT_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Fulfillment Count

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/fulfillments/count.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Create Fulfillment

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/fulfillments.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"fulfillment":{"line_items_by_fulfillment_order":[{"fulfillment_order_id":{FULFILLMENT_ORDER_ID}}],"tracking_info":{"number":"1Z999AA10123456784","url":"https://www.ups.com/track?tracknum=1Z999AA10123456784","company":"UPS"}}}'
```

#### Update Tracking

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/fulfillments/{FULFILLMENT_ID}/update_tracking.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"fulfillment":{"tracking_info":{"number":"1Z999AA10123456784","url":"https://www.ups.com/track?tracknum=1Z999AA10123456784","company":"UPS"},"notify_customer":true}}'
```

#### Cancel Fulfillment

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/fulfillments/{FULFILLMENT_ID}/cancel.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -X POST
```

### Fulfillment Orders

#### List Fulfillment Orders for Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/fulfillment_orders.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Fulfillment Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/fulfillment_orders/{FULFILLMENT_ORDER_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

### Refunds

#### List Refunds for Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/refunds.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Refund

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/refunds/{REFUND_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Calculate Refund

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/refunds/calculate.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"refund":{"shipping":{"full_refund":true},"refund_line_items":[{"line_item_id":{LINE_ITEM_ID},"quantity":1,"restock_type":"return"}]}}'
```

Restock types: `no_restock`, `cancel`, `return`, `legacy_restock`

#### Create Refund

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/refunds.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"refund":{"currency":"USD","notify":true,"note":"Customer returned item","shipping":{"full_refund":true},"refund_line_items":[{"line_item_id":{LINE_ITEM_ID},"quantity":1,"restock_type":"return"}],"transactions":[{"parent_id":{TRANSACTION_ID},"amount":"10.00","kind":"refund","gateway":"shopify_payments"}]}}'
```

### Returns

#### List Returns

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/returns.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

Query parameters: `limit`, `status` (open, closed, cancelled, requested, in_progress)

#### Get Return

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/returns/{RETURN_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Create Return

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/returns.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"return":{"order_id":{ORDER_ID},"return_line_items":[{"fulfillment_line_item_id":{FULFILLMENT_LINE_ITEM_ID},"quantity":1,"return_reason":"WRONG_ITEM"}]}}'
```

Return reasons: `UNKNOWN`, `SIZE_TOO_SMALL`, `SIZE_TOO_LARGE`, `UNWANTED`, `NOT_AS_DESCRIBED`, `WRONG_ITEM`, `DEFECTIVE`, `STYLE`, `COLOR`, `OTHER`

### Transactions

#### List Transactions for Order

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/transactions.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Transaction

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/transactions/{TRANSACTION_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Transaction Count

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/transactions/count.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Create Transaction (Capture)

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/orders/{ORDER_ID}/transactions.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"transaction":{"kind":"capture","amount":"10.00","parent_id":{AUTHORIZATION_ID}}}'
```

Transaction kinds: `authorization`, `capture`, `sale`, `void`, `refund`

### Collections

#### List Custom Collections

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/custom_collections.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Custom Collection

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/custom_collections/{COLLECTION_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Create Custom Collection

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/custom_collections.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"custom_collection":{"title":"Summer Collection","body_html":"<p>Summer products</p>"}}'
```

#### Update Custom Collection

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/custom_collections/{COLLECTION_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{"custom_collection":{"id":{COLLECTION_ID},"title":"Updated Collection"}}'
```

#### Delete Custom Collection

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/custom_collections/{COLLECTION_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -X DELETE
```

#### List Smart Collections

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/smart_collections.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Get Smart Collection

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/smart_collections/{COLLECTION_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

#### Create Smart Collection

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/smart_collections.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"smart_collection":{"title":"Sale Items","rules":[{"column":"compare_at_price","relation":"greater_than","condition":"0"}]}}'
```

Rule columns: `title`, `type`, `vendor`, `variant_price`, `tag`, `compare_at_price`, `weight`, `inventory_stock`, `variant_compare_at_price`, `variant_weight`, `variant_inventory`, `variant_title`

Rule relations: `equals`, `not_equals`, `greater_than`, `less_than`, `starts_with`, `ends_with`, `contains`, `not_contains`

### Collects (Product-Collection Links)

#### List Collects

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/collects.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

Query parameters: `product_id`, `collection_id`, `limit`, `since_id`, `fields`

#### Create Collect

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/collects.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"collect":{"product_id":{PRODUCT_ID},"collection_id":{COLLECTION_ID}}}'
```

#### Delete Collect

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/collects/{COLLECT_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -X DELETE
```

### Abandoned Checkouts

#### List Abandoned Checkouts

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/checkouts.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

Query parameters: `limit`, `since_id`, `created_at_min`, `created_at_max`, `updated_at_min`, `updated_at_max`, `status` (open, closed)

#### Get Abandoned Checkout Count

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/checkouts/count.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

## Status Reference

### Order Status

| Field | Values |
|-------|--------|
| `financial_status` | pending, authorized, partially_paid, paid, partially_refunded, refunded, voided |
| `fulfillment_status` | null (unfulfilled), partial, fulfilled, restocked |

### Product Status

| Status | Description |
|--------|-------------|
| `active` | Available for sale |
| `archived` | No longer available, hidden from admin lists |
| `draft` | Not ready for sale |

### Return Status

| Status | Description |
|--------|-------------|
| `requested` | Return requested by customer |
| `in_progress` | Return being processed |
| `open` | Return accepted, awaiting items |
| `closed` | Return completed |
| `cancelled` | Return cancelled |

## Pagination

Shopify uses cursor-based pagination via the `Link` header.

### Using Page Info

```bash
# First request
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products.json?limit=50" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -i
```

Response includes `Link` header:
```
Link: <https://store.myshopify.com/admin/api/2024-10/products.json?page_info=abc123&limit=50>; rel="next"
```

```bash
# Next page
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/products.json?page_info=abc123&limit=50" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

Note: When using `page_info`, you cannot use other query parameters except `limit` and `fields`.

## Rate Limiting

Shopify uses a leaky bucket algorithm:

- **Bucket size**: 40 requests
- **Leak rate**: 2 requests/second
- **Restoration**: ~20 seconds for full bucket

Response headers:
- `X-Shopify-Shop-Api-Call-Limit`: Current usage (e.g., `32/40`)
- `Retry-After`: Seconds to wait (on 429 response)

### Best Practices

1. Check `X-Shopify-Shop-Api-Call-Limit` header
2. If near limit, add delays between requests
3. On 429 response, wait for `Retry-After` seconds
4. Use bulk operations for large data sets

## Webhooks

### List Webhooks

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/webhooks.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN"
```

### Create Webhook

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/webhooks.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"webhook":{"topic":"orders/create","address":"https://example.com/webhooks/orders","format":"json"}}'
```

Common topics: `orders/create`, `orders/updated`, `orders/fulfilled`, `orders/cancelled`, `products/create`, `products/update`, `products/delete`, `customers/create`, `customers/update`, `inventory_levels/update`, `refunds/create`

### Delete Webhook

```bash
curl "https://$SHOPIFY_STORE_DOMAIN/admin/api/2024-10/webhooks/{WEBHOOK_ID}.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -X DELETE
```

## Changelog

### v1.0.0

- Initial release with full Admin REST API coverage
- Orders, Products, Variants, Customers
- Inventory management (levels, items, locations)
- Fulfillments and fulfillment orders
- Refunds, Returns, Transactions
- Collections (custom, smart) and collects
- Abandoned checkouts
- Webhooks management
- Status reference tables
- Pagination and rate limiting documentation
