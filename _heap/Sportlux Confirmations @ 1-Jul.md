
![[Pasted image 20260701164457.png]]

7 files created

Looks like 1k confirmations found on the queue

![[Pasted image 20260701164734.png]]


smoking gun:
https://app.datadoghq.com/logs?query=%40domain%3Afuse%20service%3Asnap-polling-service%20%40businessId%3ASPORTLUX%20%40confirmationType%3Agood_out%20-%40count%3A0%20%40requestor.correlationId%3A0ced784d-53ae-4922-a4c7-d6b1cdd26166&agg_m=count&agg_m_source=base&agg_q=%40count%2C%40requestor.correlationId&agg_t=count&analyticsOptions=%5B%22bars%22%2C%22dog_classic%22%2Cnull%2Cnull%2C%22value%22%5D&clustering_pattern_field_path=message&cols=host%2Cservice&flat_group_bys=true&messageDisplay=inline&refresh_mode=paused&sort_m=count&sort_t=count&storage=hot&stream_sort=desc&top_n=10&top_o=top&viz=toplist&x_missing=true&from_ts=1782774000000&to_ts=1782860399999&live=false

![[Pasted image 20260701170534.png]]

156 confirmations all retrieved in the same poll. but 6 times over - dafuq?