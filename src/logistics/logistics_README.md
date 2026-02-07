1) 物流的子域拆分（你要的全局視角）

我建議 Logistics 先切 6 個子 watcher（都由同一個物流 agent 實作）：

Maritime Shipping（海運）：油輪/LNG/成品油 船隊、航線、停靠、等待

Chokepoints（咽喉點）：運河、海峽、主要航道風險（先做狀態，不做軍事解讀）

Ports & Congestion（港口擁堵）：排隊、吞吐、罷工、關閉、限制

Pipelines（管線）：流量、維護、事故、關閉、改道

Insurance & War Risk（保險/戰險）：保費跳升、承保限制、條款變動

Freight & Costs（運費與到岸成本構成）：運費指數、燃油附加、繞道成本