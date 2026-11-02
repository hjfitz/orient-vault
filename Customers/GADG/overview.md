---
tags: [customer, GADG]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Gadgets — overview
thesis: "Gadgets exists in config-service (production) with no connectors. No narrative has been captured."
confidence: high
---
# Gadgets — overview

```orient-bluf
{"v": 1, "bluf": "Gadgets exists in config-service (production) with no connectors. No narrative has been captured.", "confidence": "high", "action": "none"}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| AlexP-REST-TEST | rest | no mappings | off | 0 |
| Emerald Sea | rest | no mappings | on | 0 |
| Fulfil.io Testing | rest | no mappings | off | 0 |
| Primary API | rest | no mappings | on | 0 |
| AlexP-Test | sftp | sales_order, pick_confirmation, pack_confirmation, finished_good_receipt | off | 4 |
| Custom CSV | sftp | purchase_order, sales_order, goods_in_confirmation, goods_out_confirmation, stock_adjustment | off | 5 |
| Harry's Test SFTP | sftp | no mappings | off | 0 |
| ILG Test Account | sftp | purchase_order, sales_order, master_data, goods_out_confirmation, goods_in_confirmation, stock_adjustment, return_goods_authorization, return_goods_confirmation, pick_confirmation, pack_confirmation | on | 10 |
| Primary SFTP | sftp | purchase_order, sales_order, master_data, goods_in_confirmation, goods_out_confirmation, stock_adjustment, return_goods_authorization, return_goods_confirmation, pick_confirmation, pack_confirmation, finished_good_receipt, work_order_confirmation, work_order | on | 13 |
| Test Business ID | sftp | goods_in_confirmation | off | 1 |
| Testing | sftp | no mappings | off | 0 |
| Zedonk | sftp | goods_out_confirmation | off | 1 |
| AlexP-Shopify-Test | shopify | sales_order, goods_out_confirmation | on | 2 |
| AlexP-Temp-Shopify | shopify | sales_order, goods_out_confirmation | on | 2 |
| ILG Test Store | shopify | sales_order, goods_out_confirmation | on | 2 |
| Nylah's Bees | shopify | sales_order | on | 1 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
