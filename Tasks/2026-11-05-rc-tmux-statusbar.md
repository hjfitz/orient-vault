---
tags: [adhoc-task]
date: 2026-11-05
tldr: "Replaced dracula tmux status bar on the remote-compute VM with an rc-banner-palette theme (CPU/MEM gauges, no weather)"
session_id: b3653dc6-4e7c-4069-bef6-085494408847
status: done
---
# Restyle remote-compute tmux status bar

## Outcome
New ~/.tmux/theme.conf + ~/.tmux/bin/sysstat on the rc VM (hjf): rc-banner colours (39/44/220), CPU/MEM bar gauges, operator@host, clock; phone-width collapse kept. Dracula/base16 plugins dropped from ~/.tmux.conf; old config in ~/.tmux/backup/. Gauge greys brightened after feedback.
