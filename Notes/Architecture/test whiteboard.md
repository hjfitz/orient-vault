---
title: "test whiteboard"
date: "2026-11-12"
kind: whiteboard
---
# test whiteboard

```orient-board
{
  "v": 1,
  "preset": "c4-context",
  "nodes": [
    {"id":"customer","kind":"person","label":"Customer","sub":"Places and tracks orders","x":40,"y":40},
    {"id":"orders","kind":"service","label":"Orders","tech":"Cloud Run","sub":"Takes an order and routes it","icon":"run","x":340,"y":40},
    {"id":"payments","kind":"external","label":"Payments","sub":"Third-party card processor","x":660,"y":40}
  ],
  "edges": [
    {"from":"customer","to":"orders","label":"places an order"},
    {"from":"orders","to":"payments","label":"takes payment"}
  ],
  "groups": [],
  "notes": []
}
```
