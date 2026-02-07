# Chokepoints — State Variables & Signals (v0)

## Design Principles
- State Variables = 可量測、可時間序列化的世界狀態
- Signals = 對「狀態變化」的結構化解讀
- Events = Signals 的敘事封裝（不在本層定義）

---

## I. State Variables (World State)

### A. Availability & Access
- transit_status: enum
  - open | restricted | closed

- access_restriction_level: enum
  - none | partial | severe

- directional_control: enum
  - normal | alternating | one_way

- vessel_type_restriction: array
  - crude_tanker | lng_carrier | product_tanker | container | bulk
  - 可為空陣列表示無限制

---

### B. Delay & Congestion
- average_wait_time: number
  - 單位：hours

- median_transit_delay: number
  - 單位：hours

- queue_length: number
  - 排隊船舶數

- congestion_level: enum
  - low | medium | high

---

### C. Flow & Throughput
- daily_vessel_count: number
  - 每日通過船舶數

- energy_vessel_count: number
  - 能源相關船舶數（油/LNG）

- throughput_index: number
  - 相對歷史基準（0–1 或 %）

- flow_direction_bias: enum
  - eastbound | westbound | mixed

---

### D. Cost & Risk
- insurance_status: boolean
  - 是否被列為高風險區

- war_risk_premium: number
  - 戰險附加費（bps / %）

- insurance_surcharge_level: enum
  - normal | elevated | extreme

- escort_requirement: boolean
  - 是否需要軍事或武裝護航

---

### E. Stability & Outlook
- incident_active: boolean
  - 是否存在未解決事件

- expected_clearance_time: datetime
  - 預期恢復正常時間

- operational_uncertainty: enum
  - low | medium | high

---

## II. Signals (Detected Changes)

### 1. Availability Signals
- CHOKEPOINT_CLOSED
  - transit_status → closed

- CHOKEPOINT_RESTRICTED
  - open → restricted

- ACCESS_TIGHTENING
  - access_restriction_level 升級

- VESSEL_TYPE_BANNED
  - vessel_type_restriction 新增項目

---

### 2. Congestion & Delay Signals
- CONGESTION_SPIKE
  - average_wait_time > hard_threshold

- QUEUE_BUILDUP
  - queue_length 快速上升

- DELAY_ACCELERATION
  - delay 變化率 > N%

- PERSISTENT_CONGESTION
  - congestion_level = high 且持續 > T

---

### 3. Flow & Topology Signals
- THROUGHPUT_DROP
  - throughput_index 顯著下降

- ENERGY_FLOW_REDUCTION
  - energy_vessel_count 低於基準

- FLOW_REDIRECTION
  - flow_direction_bias 明顯偏移

- DIVERSION_PATTERN_DETECTED
  - 與歷史路徑模式顯著不同

---

### 4. Cost & Risk Signals
- WAR_RISK_SURGE
  - war_risk_premium 上跳

- INSURANCE_TIGHTENING
  - insurance_surcharge_level 升級

- ESCORT_REQUIRED
  - escort_requirement = true

- RISK_ZONE_DECLARED
  - insurance_status 由 false → true

---

### 5. Stability & Persistence Signals
- INCIDENT_UNRESOLVED
  - incident_active 持續 > T

- CLEARANCE_DELAYED
  - expected_clearance_time 延後

- OPERATIONAL_UNCERTAINTY_HIGH
  - operational_uncertainty 升級為 high

---

## III. Impact Hints (for Upper-Layer Agents)

- delay_up
- cost_up
- capacity_down
- route_diversion
- insurance_risk_up
- flow_instability

---

## IV. MVP Minimal Set

### State Variables (Week 1)
- transit_status
- average_wait_time
- queue_length
- throughput_index
- insurance_status
- war_risk_premium
- incident_active
- expected_clearance_time

### Signals (Week 1)
- CHOKEPOINT_CLOSED
- CONGESTION_SPIKE
- THROUGHPUT_DROP
- WAR_RISK_SURGE
- DIVERSION_PATTERN_DETECTED
