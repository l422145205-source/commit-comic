# 活干完了，我怎么反而掉线了？

ReelPilot / 完成状态与监督检查撞在同一瞬间

## 1. 员工交卷了

我完成啦！……你说我失联？

旧监督逻辑先查完成，再单独检查所有权。

## 2. 领导看了两次

第一次还在跑，第二次租约没了。

两次读取之间提交完成，会清空活跃租约，旧检查误报。

## 3. 拍一张再判断

完成和租约，要看同一张快照。

worker_state读取一行；同一行用于完成识别与控制校验。

## 4. 让竞态准时发生

别等它偶发，把时机固定下来。

回归测试强制插入这次完成：旧序列抛错，新序列随后识别完成。

---

Illustrated interpretation of code evidence; review the scope and evidence notes before posting.
