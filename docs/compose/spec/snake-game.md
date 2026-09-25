---
feature: snake-game
status: in-progress
updated: 2026-09-25
branch: feat/band11-snake-quickapp
commits: 496b84c..5b9f8de # 第一轮交付；第二轮（rpk 打包）进行中
---

# 小米手环 11 贪吃蛇（快应用）

## Report

**What was built** — 单文件 Web 可玩原型 `prototype/index.html`：按手环 11 跑道屏逻辑分辨率 212×520 设计（HUD 40px + 13×30 网格），AMOLED 纯黑视觉，完整状态机（开始/游玩/暂停/结束）、键盘与触屏转向、计分与最高分 localStorage 持久化、随进食加速。转向保护实现为"反向输入仅对照当前方向拒绝"，从结构上保证单步内不可能 180° 掉头（含同 tick 双键序列）。另交付 macOS→rpk 真机打包链路调研结论（S2「真机打包链路」小节）。

**Verification** — `python3 scripts/verify_prototype.py`（headless Chromium）：9 项 PASS，含无 JS/console 错误、节拍推进、转向与掉头保护、同 tick 双键无法绕过掉头保护、进食计分与加速、撞墙死亡+最高分持久化、重开/暂停恢复、刷新后最高分存活；`ALL CHECKS PASSED`。回归有效性：对修复前代码（stash 后）运行同脚本，在双键断言处 AssertionError、EXIT=1。独立评审子代理对 critical 修复 diff（496b84c..5b9f8de）复审：三项结论均无 critical。

**Journey log** —
1. 首版掉头保护比对 `queued||dir`，同 tick 先↑后← 可绕过导致单步掉头撞颈即死；评审发现后改为仅对照 `dir`，不变式"dir 仅在 step 中变更"保证任意按键序列无法产生单步 180°。
2. 验证脚本最初只测单次反向，漏报上述漏洞；补充同 tick 双键断言后旧代码 FAIL、新代码 PASS，测试有效性经反向验证。
3. 手环 11 无官方三方 SDK，调研确立 AstroBox/aiot-toolkit 侧载链路；plugin-dev（WASM 宿主插件）与本特性无关，早期方向为死胡同。

## [S1] Problem

用户想在自己的小米手环 11 上玩一个贪吃蛇小游戏。小米官方不提供第三方应用开发 SDK，但手环 11 搭载 Vela 系统与快应用引擎，社区已验证可通过 AstroBox 侧载第三方软件（含游戏）。当前项目从零开始，缺少：一个按手环 11 屏幕特性设计的可玩游戏本体，以及一条在 macOS 上可复现的 rpk 打包链路。

## [S2] Design

### 设备与平台契约

- 目标设备：小米手环 11（Vela 系统，快应用引擎），屏幕 1.72" AMOLED 跑道屏，分辨率 **212×520**（官方参数页），全屏触摸。
- 应用形态：Vela 快应用（.ux + JS，打包为 rpk），非 AstroBox 宿主插件（plugin-dev 文档是宿主端 WASM 插件，与本特性无关）。
- 安装方式：AstroBox 本地侧载（免官方审核）。真机侧载不属于本次交付范围，见 S3。

### 本体形态：交付物

1. **Web 可玩原型**（第一轮已交付）：单文件 `prototype/index.html`，自包含（内联 CSS/JS，无外部依赖），在浏览器中完整可玩。画布逻辑分辨率固定 **212×520**，居中显示并按视口等比缩放；AMOLED 纯黑背景。
2. **真机打包链路**（第一轮已交付）：S2「真机打包链路」小节记录 macOS 上从原型到 rpk 的可复现工具链结论。
3. **签名 rpk 包**（第二轮新增）：`quickapp/` 下的 Vela 快应用项目，移植原型玩法，自签证书打包出可侧载的 `.rpk`。

### 游戏规则契约

- 网格：顶部 HUD 高 40px（得分/最高分），游戏区 212×480；单元格 16px，**13 列 × 30 行**（208×480），水平居中（两侧各 2px 边距）。
- 初始状态：蛇长 3，位于游戏区中央，向右移动；食物随机生成在空格。
- 碰撞：撞墙、撞自身即游戏结束，不穿墙。
- 速度：基础节拍 200ms/步，每吃一个食物减少 4ms，下限 80ms。
- 计分：每个食物 +10 分；最高分持久化到 `localStorage`，原型与真机分别独立存储。
- 状态机：开始页 → 游玩中 → 暂停 → 游戏结束；游戏结束后再次滑动/点击/按键重新开始。

### 操作契约

- 触屏（真机）：上下左右滑动转向；轻点暂停/继续。
- 键盘（桌面调试）：方向键或 WASD 转向，空格暂停/继续，回车开始/重开。
- 转向保护：单步内不允许 180° 掉头（按当前方向的反向输入忽略）。

### 视觉契约

- 背景 `#000000`（AMOLED），蛇身 `#4ADE80`（圆角矩形，蛇头略亮 `#86EFAC`），食物 `#F87171`，HUD 文字 `#FFFFFF`、最高分次级色 `#9CA3AF`。
- 字体：系统无衬线；HUD 得分为半粗 16px。
- 无图片资源、无音效（S3）。

### 验证边界

- 自动化验证：headless 浏览器加载 `prototype/index.html`，断言——页面无 JS 错误；键盘开始游戏后蛇位置随节拍前进；触发转向后方向改变；模拟撞墙后进入游戏结束状态且最高分写入 localStorage。
- 打包链路调研的验收以「真机打包链路」小节结论为准（可行给可复现步骤；不可行给明确阻塞点与替代方案），不在本次执行真机安装。
- rpk 构建验收见「快应用交付契约」（第二轮）。

### 快应用交付契约（第二轮）

- 项目位置：`quickapp/`，Vela 快应用标准结构（`manifest.json` + 页面 `.ux`），单页游戏。
- 设计基准：`designWidth: 212`，页面铺满 212×520；布局遵守胶囊屏安全区（内容避开上下端圆弧、左右留 ≥8px）。
- 玩法：完整沿用「游戏规则契约」（13×30、200ms 起步 -4ms/食物下限 80ms、撞墙撞自身即死、+10 分、状态机、掉头保护对照当前方向）。
- 操作：仅触屏——滑动转向，轻点暂停/继续，游戏结束后滑动或轻点重开（无键盘）。
- 最高分持久化：使用 Vela 快应用本地存储 API；若实测该环境不可用，降级为进程内存保留最高分，并在 Report 记录降级原因。
- 打包：`sign/` 下自签证书（openssl），`aiot release` 产出签名 rpk 至 `quickapp/dist/`；`aiot build` 产出 debug rpk 一并保留。**`sign/` 私钥与证书不入库**（.gitignore 排除）。
- 验收：`aiot release` 无错误退出；产物 rpk 为合法 zip，内含应用元数据（app.json 等）与页面文件。

### 真机打包链路

**结论：可行。** macOS 上存在两条官方打包路径（GUI 的 AIoT-IDE macOS 版，或纯命令行的 npm 包 `aiot-toolkit`），产物为 `.rpk`；侧载端 AstroBox 提供 macOS 版且米坛知识库明确标注「小米手环 11 系列：完整支持」。唯一待真机验证的不确定点：免审核本地安装时设备是否接受**未签名的 debug rpk**（官方与 AstroBox 文档均未写明，稳妥做法是用自签证书打出 release rpk）。真机安装本身按 S3 不在本次执行范围。

#### 1. macOS 打包工具（问题 1）

- **(a) 官方 AIoT-IDE 有 macOS 版。** 官方「安装环境」页明确写「本应用支持 macOS、Windows 及 Ubuntu」，macOS 最低 **14 (Sonoma)**，下载区含 Apple 栏的 `.arm` / `.x64` 两个下载按钮；macOS 安装报错用 `sudo xattr -r -d com.apple.quarantine`（空格后拖入 .app）解决。官方 FAQ 亦直接回答「**Windows 和 Mac 是否可以打包 rpk？——Windows 和 Mac 可以打包 rpk**」。注：页面下载按钮由 JS 触发，本次未能捕获 dmg 直链（该页面本身即下载入口；历史版本在小米网盘 kpan 链接，密码 99E6）。教程只写 Windows 属教程覆盖面问题，非平台限制。
- **(b) 纯命令行 `aiot-toolkit`（npm，推荐，可完全绕开 IDE）。** 官方文档「AIoT-toolkit」称其为「脱离 AIoT-IDE 独立开发的命令行工具」；npm 包 `aiot-toolkit`（2.0.5，作者 yinhunfeixue）README 给出 `npm i aiot-toolkit -g`、`npm create aiot ux` 建项目、`aiot build`（debug）、`aiot release`（release，需签名）、`aiot resign`（对 build 目录重签出 rpk）。Node 工具，天然跨平台，macOS 可用。npm 下载慢时在项目根目录建 `.npmrc` 写入 `registry="https://registry.npmmirror.com/"`（官方 FAQ 同款建议）。
- **(c) 标准快应用 `hap-toolkit` 不采用。** `hap-toolkit`（npm）是 Android 端标准快应用工具链，README/变更记录未提 Vela；Vela 官方文档全链路均以 AIoT-toolkit/AIoT-IDE 为准。**无官方依据表明 hap-toolkit 产物能在 Vela 手环上运行**（此点为文档证据推断，未实测）。
- **(d) 米坛知识库（wiki.bandbbs.cn）没有 Mac 打包专项教程**，其快应用栏目是「付费快应用激活」类内容；打包结论应以官方文档为准。
- **(e) AstroBox「资源内容规范」页不说明技术格式。** 该页只规定内容/质量/版本/版权（用于上架审核），不含本地快应用资源的制作方式。技术格式与本地安装方式见 AstroBox「资源安装」文档：支持**设备页加号选文件 / 队列 / 电脑端直接拖拽**三种本地安装（未声明需要何种签名）。

#### 2. 手环 11 支持证据（问题 2）

- 米坛知识库《AstroBox 从此开始》设备支持表：「**小米手环 11 系列 ✔️ 完整支持**」（同表 手环 10 系列/10 Pro/9 系列完整支持，手环 8 及更老不支持）。
- AstroBox 官方文档未直接给出机型清单文本（安装页是「点击选择设备」向导，文本层未渲染出列表），但官方文档确认 macOS 有 ARM/x86 两个 V2.1.0 安装包及 `curl -fsSL https://abox.run/install.sh | bash` 一键安装。
- 社区旁证（搜索结果页，未逐一点开）：Bilibili《如何下载和安装小米手环11的第三方软件（含游戏）》BV1XVhh6XEMG、抖音/贴吧同类手环 11 第三方软件安装教程，均指向 AstroBox/米坛路线。

#### 3. 签名/证书要求（问题 3）

- **debug rpk（`aiot build` / IDE「打包」）不需要签名**，产物为 `dist/*.debug.rpk`。
- **release rpk（`aiot release` / IDE「发布」）必须先有签名文件**：项目 `sign/` 目录下放 `private.pem` + `certificate.pem`。IDE 内点「发布」可自动生成（需系统有 openssl）；手动命令（官方文档原文）：
  ```bash
  mkdir -p sign && cd sign
  openssl req -newkey rsa:2048 -nodes -keyout private.pem -x509 -days 3650 -out certificate.pem
  cd ..
  ```
  重签已有包可用 `aiot resign`（build/ + 可选 sign/ → dist/*.rpk）。
- **证书要求宽松**：官方 FAQ《构建 release 版本 rpk 时打包证书有什么要求？》——不涉及手表↔手机通信时「**对证书无特殊要求，按照文档中的步骤生成即可**」；涉及通信才需与手机 App 证书一致。自签即可，**无需向小米申请、与上架审核无关**；唯一要求是后续更新沿用同一证书（证书变更可能导致「无法上架」，对本地侧载无影响）。
- **AstroBox 免审核侧载是否强制签名：未查到任何说明。** AstroBox「资源安装报错」全文无签名/证书类报错；其安装失败只泛泛报 `InstallFailed / VerifyFailed`。→ 标注**不确定**；稳妥策略：侧载 release 包（已自签），若真机拒装再回退试 debug 包。

#### 4. 手环 11 跑道屏适配要点（问题 4）

手环 11 规格 1.72" 212×520 与官方文档中的**小米手环 10 完全相同**（胶囊/跑道形，PPI 326，DPR 2.0，屏幕宽度 106dp，长宽比 0.4），可直接沿用其适配依据：

- **designWidth**：框架默认按 480×480 换算，Vela 三方应用自动适配；在 `manifest.json` 配 `designWidth: 212`，CSS 尺寸直接按 212×520 设计稿写（官方 FAQ《如何适配不同尺寸的屏幕？》）。
- **圆角安全区**：官方《多屏设计》要求胶囊屏把主体内容置于安全区内（边缘易裁切、难点击）；推荐胶囊屏长宽比 0.3–0.5。设计稿层面，路明笔记给出实测「小米手环 10 圆角半径 999px」（即两端全圆弧）——对应到 212 宽画布，**上下两端整段都是半圆弧，HUD/文字不要贴到屏幕最上最下，左右留 ≥8px 安全边距**。
- **多屏规范**：官方《多屏适配》给出设备屏幕表与「多屏规范 / 多屏 UI 模拟器」入口；本项目为单机型（手环 11）专供，可只按 212×520 一套稿，但 manifest 里声明的分辨率/设备类型需与手环 11 一致（官方设备表暂未列手环 11，属文档滞后——同分辨率手环 10 在列）。
- 原型阶段的 13 列 × 30 行、顶部 40px HUD 布局与该分辨率契约一致，无需改动，仅需在 .ux 阶段补 designWidth 与安全区留白。

#### 可复现步骤（macOS）

```bash
# ① 打包工具（二选一；推荐纯 CLI）
npm i -g aiot-toolkit create-aiot        # 方案 A：命令行
npm create aiot ux                       # 创建 ux 模板项目
cd <project> && npm i                    # 慢则先写 .npmrc: registry=https://registry.npmmirror.com/
# 方案 B：官方 AIoT-IDE macOS 版（macOS 14+）从
#   https://iot.mi.com/vela/quickapp/zh/guide/start/use-ide.html 下载（.arm/.x64）
#   报 Gatekeeper 错: sudo xattr -r -d com.apple.quarantine（空格+拖入 .app）

# ② 签名（release 必需；系统自带 openssl 即可，macOS 走 LibreSSL 也够用）
mkdir -p sign
openssl req -newkey rsa:2048 -nodes -keyout sign/private.pem -x509 -days 3650 -out sign/certificate.pem

# ③ 出包
aiot build      # → dist/*.debug.rpk（免签名，能否侧载未验证）
aiot release    # → dist/*release*.rpk（已自签，侧载推荐）

# ④ 侧载：安装 AstroBox macOS 版（ARM/x86 皆有 V2.1.0）
curl -fsSL https://abox.run/install.sh | bash
# 或从 https://abox.run/docs/usage/install 下载 dmg；Gatekeeper:
#   sudo xattr -r -d com.apple.quarantine /Applications/AstroBox.app
# ⑤ 打开 AstroBox → 连接小米手环 11 → 把 .rpk 直接拖入窗口
#    （或设备页/队列右上角 + 选文件）→ 队列「开始」推送安装
```

**阻塞点**：本仓库无手环 11 实机与配对环境，第 ⑤ 步真机安装未执行（S3 明确排除）；debug rpk 兼容性、手环 11 上的圆角裁切效果需实机复核。

#### 来源列表

1. 使用 AIoT-IDE 来开发 JS 应用（安装环境：macOS 支持/下载/签名/打包） — https://iot.mi.com/vela/quickapp/zh/guide/start/use-ide.html
2. AIoT-toolkit（命令行脱离 IDE 打包） — https://iot.mi.com/vela/quickapp/zh/tools/toolkit/start.html
3. 打包应用（debug rpk） — https://iot.mi.com/vela/quickapp/zh/tools/release/start.html
4. 发布应用（release 需签名文件） — https://iot.mi.com/vela/quickapp/zh/tools/release/release.html
5. 常见问题（Mac 可打包 rpk；release 证书无特殊要求；designWidth 适配） — https://iot.mi.com/vela/quickapp/zh/guide/other/faq.html
6. aiot-toolkit — npm（install/build/release/resign 命令与 sign 目录结构） — https://www.npmjs.com/package/aiot-toolkit
7. hap-toolkit — npm（标准快应用工具，无 Vela 依据） — https://www.npmjs.com/package/hap-toolkit
8. 从此开始 | 米坛知识库（**手环 11 系列 完整支持** + 各平台下载表） — https://wiki.bandbbs.cn/Guides/astrobox/astrobox-start.html
9. 适用条件与安装 | AstroBox 文档（macOS ARM/x86 V2.1.0、一键安装、quarantine 处理） — https://abox.run/docs/usage/install
10. 资源安装 | AstroBox 文档（本地安装三种方式） — https://abox.run/docs/usage/resource
11. 资源内容规范 | AstroBox 文档（仅内容规范，无技术格式） — https://abox.run/docs/creator-tools/resource-std/content
12. 资源安装报错 | AstroBox 文档（无签名类报错） — https://abox.run/docs/usage/errors/install-errors
13. 多屏设计（胶囊屏安全区、设备屏幕表） — https://iot.mi.com/vela/quickapp/zh/guide/design/multi-screens.html
14. 多屏适配（手环 10 = 212×520 胶囊屏参数） — https://iot.mi.com/vela/quickapp/zh/guide/multi-screens/
15. 从零开始，为小米穿戴设备编写快应用 — 路明笔记（Windows 教程；OpenSSL 签名；手环 10 212×520、圆角半径 999px；release → dist/*.rpk） — https://www.luming.cool/posts/2025/08/build-a-quick-app-for-vela-devices/
16. （旁证，仅搜索结果页）Bilibili《如何下载和安装小米手环11的第三方软件（含游戏）》 — https://www.bilibili.com/video/BV1XVhh6XEMG/

## [S3] Out of Scope

- 真机侧载安装（需要手环实机 + AstroBox 配对，本次不执行）。
- 官方快应用商店上架与审核流程。
- AstroBox 宿主端 WASM 插件开发。
- 官方 AIoT IDE 的 Windows 环境搭建。
- 音效、震动反馈、多档难度、排行榜联网。
- 手环 11 以外机型的适配（规格以手环 11 为准）。

## Tasks

- [x] T1: 撰写并确认特性文档 — acceptance: 本文档经用户确认，无未决产品问题（covers: S1, S2, S3）
- [x] T2: 实现 Web 可玩原型 `prototype/index.html` — acceptance: headless 浏览器验证通过：无 JS 错误、蛇随节拍移动、转向有效、撞墙进入游戏结束且最高分持久化（covers: S2; depends: T1）
- [x] T3: 调研 macOS 打包链路并回填文档 — acceptance: S2「真机打包链路」小节包含可复现结论或明确阻塞点+替代方案，并记录手环 11 适配依据（covers: S2; depends: T1）
- [x] T4: 验证、独立评审并 Finalize — acceptance: 验证命令与结果记录于 Report，评审子代理三结论（规格符合性/正确性/一致性）均无 critical，文档 status: delivered 并提交（covers: 全部; depends: T2, T3）
- [ ] T5: 移植原型到 `quickapp/` 并打出签名 rpk — acceptance: `aiot release` 无错误退出产出 rpk，zip 结构检查含应用元数据与页面文件；`sign/` 私钥不入库（covers: 快应用交付契约; depends: T4）
- [ ] T6: 第二轮验证、评审并 Finalize — acceptance: 构建验证命令与结果记入 Report，评审子代理三结论均无 critical，status: delivered 并提交（covers: 快应用交付契约; depends: T5）
