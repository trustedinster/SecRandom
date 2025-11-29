<div align="center">

<image src="../resources/secrandom-icon-paper.png" height="128"/>

# SecRandom - 公平隨機選擇系統

🎯 **真正公平的隨機選擇算法** | 🚀 **現代化教育工具** | 🎨 **優雅的互動體驗**

> 本 Readme **由 AI 翻譯**，並由我們的開發人員審核。如果您發現任何錯誤，請向我們報告。
</div>

<!-- 專案狀態徽章 -->
<div align="center">

[![GitHub Issues](https://img.shields.io/github/issues-search/SECTL/SecRandom?query=is%3Aopen&style=for-the-badge&color=00b4ab&logo=github&label=问题)](https://github.com/SECTL/SecRandom/issues)
[![最新版本](https://img.shields.io/github/v/release/SECTL/SecRandom?style=for-the-badge&color=00b4ab&label=最新正式版)](https://github.com/SECTL/SecRandom/releases/latest)
[![最新Beta版本](https://img.shields.io/github/v/release/SECTL/SecRandom?include_prereleases&style=for-the-badge&label=测试版)](https://github.com/SECTL/SecRandom/releases/)
[![上次更新](https://img.shields.io/github/last-commit/SECTL/SecRandom?style=for-the-badge&color=00b4ab&label=最后更新时间)](https://github.com/SECTL/SecRandom/commits/master)
[![下载统计](https://img.shields.io/github/downloads/SECTL/SecRandom/total?style=for-the-badge&color=00b4ab&label=累计下载)](https://github.com/SECTL/SecRandom/releases)

[![QQ群](https://img.shields.io/badge/-QQ%E7%BE%A4%EF%BD%9C833875216-blue?style=for-the-badge&logo=QQ)](https://qm.qq.com/q/iWcfaPHn7W)
[![bilibili](https://img.shields.io/badge/-UP%E4%B8%BB%EF%BD%9C黎泽懿-%23FB7299?style=for-the-badge&logo=bilibili)](https://space.bilibili.com/520571577)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](https://opensource.org/licenses/GPL-3.0)

[简体中文](../README.md) | [English](./README_EN.md) | **✔繁體中文**

![Code Contribution Statistics](https://repobeats.axiom.co/api/embed/7d42538bcd781370672c00b6b6ecd5282802ee3d.svg "Code Contribution Statistics Chart")

</div>

> [!NOTE]
>
> SecRandom 將在 GNU GPLv3 許可證下開源
>
> GNU GPLv3 具有 Copyleft 特性，這意味著您可以修改 SecRandom 的原始碼，但**必須也以 GNU GPLv3 許可證開源修改後的版本**
---------
> [!note]
>
> **SecRandom v2** 將會在 2025/12/14 (GMT +8:00 中國標準時間) 左右 發布！
>
> 敬請關注我們的 BiliBili、QQ 頻道中的內容，我們會不定期發布開發動態！

## 📖 目錄

- [SecRandom - 公平隨機選擇系統](#secrandom---公平隨機選擇系統)
  - [📖 目錄](#-目錄)
  - [🎯 為何選擇公平選擇](#-為何選擇公平選擇)
  - [🌟 核心亮點](#-核心亮點)
    - [🎯 智能公平選擇系統](#-智能公平選擇系統)
    - [🎨 現代化用戶體驗](#-現代化用戶體驗)
    - [🚀 強大功能集](#-強大功能集)
    - [💻 系統兼容性](#-系統兼容性)
  - [📥 下載](#-下載)
    - [🌐 官方下載頁面](#-官方下載頁面)
  - [📸 軟體截圖](#-軟體截圖)
  - [🙏 貢獻者與特別感謝](#-貢獻者與特別感謝)
  - [💝 支持我們](#-支持我們)
    - [愛發電支援](#愛發電支援)
  - [📞 聯絡方式](#-聯絡方式)
  - [📄 官方文檔](#-官方文檔)
  - [✨ Star 歷程](#-star-歷程)
  - [📖 GitHub 貢獻教程](#-github-貢獻教程)
    - [🚀 快速開始](#-快速開始)
    - [📤 提交您的貢獻](#-提交您的貢獻)
    - [📋 貢獻指南](#-貢獻指南)
      - [代碼標準](#代碼標準)
      - [提交信息標準](#提交信息標準)
      - [Pull Request 要求](#pull-request-要求)
  - [📖 使用教程](#-使用教程)
    - [🚀 GitHub Actions 統一構建工作流使用指南](#-github-actions-統一構建工作流使用指南)
      - [通過提交消息觸發特定構建](#通過提交消息觸發特定構建)
      - [構建參數關鍵字說明](#構建參數關鍵字說明)

## 🎯 為何選擇公平選擇

傳統隨機選擇常常存在"某些人反覆被選中，而其他人很少被選中"的問題。SecRandom 使用**智能動態權重算法**，確保每位成員都有公平的被選中機會：

- **避免重複選中**：被選中次數越多的人，再次被選中的概率越低
- **平衡群體機會**：確保不同群體的成員有相等的選中機會
- **性別平衡考慮**：在選擇過程中考慮不同性別的選中頻率平衡
- **冷啟動保護**：新成員或長期未被選中的成員不會因權重過低而失去機會
- **概率可視化**：實時顯示每位成員的選中概率，讓選擇過程透明可信

## 🌟 核心亮點

### 🎯 智能公平選擇系統

- ✅ **動態權重算法**：基於選中次數、群體、性別等多維度計算，確保真正的公平
- ✅ **冷啟動保護**：防止新成員權重過低，確保人人都有平等機會
- ✅ **概率可視化**：直觀顯示每位成員的被選中概率，讓選擇過程透明可信

### 🎨 現代化用戶體驗

- ✅ **優雅的UI設計**：基於Fluent Design的現代界面，支持明暗主題
- ✅ **浮窗模式**：隨時隨地進行選擇，不影響其他工作
- ✅ **語音播報**：自動語音播報選中結果，支持自定義語音引擎

### 🚀 強大功能集

- ✅ **多種選擇模式**：單人/多人/群組/性別選擇，滿足不同場景需求
- ✅ **智能歷史記錄**：詳細記錄選中歷史，支持自動清理
- ✅ **多列表管理**：支持導入導出列表，輕鬆管理不同班級/團隊

### 💻 系統兼容性

- ✅ **全平台支持**：完美兼容 Windows 7/10/11 系統和 Linux 系統
- ✅ **多架構支持**：原生支持 x64 和 x86 架構
- ✅ **開機自啟**：支持開機自啟，隨時可用 (Windows)

## 📥 下載

### 🌐 官方下載頁面

- 📥 **[官方下載頁面](https://secrandom.netlify.app/download)** - 獲取最新穩定版本和測試版本

## 📸 軟體截圖

<details>
<summary>📸 軟體截圖展示 ✨</summary>

![點名介面](./ScreenShots/主界面_抽人_浅色.png)
![抽獎介面](./ScreenShots/主界面_抽奖_浅色.png)
![歷史記錄](./ScreenShots/主界面_抽人历史记录_浅色.png)
![設定介面](./ScreenShots/设置_抽人设置_浅色.png)

</details>

## 🙏 貢獻者與特別感謝

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/lzy98276"><img src="../app/resources/assets/contribution/contributor1.png" width="100px;" alt="lzy98276"/><br /><sub><b>lzy98276 (黎澤懿_Aionflux)</b></sub></a><br /><a href="#content-lzy98276" title="Content">🖋</a> <a href="#design-lzy98276" title="Design">🎨</a> <a href="#ideas-lzy98276" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-lzy98276" title="Maintenance">🚧</a> <a href="#doc-lzy98276" title="Documentation">📖</a> <a href="#bug-lzy98276" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/chenjintang-shrimp"><img src="../app/resources/assets/contribution/contributor2.png" width="100px;" alt="chenjintang-shrimp"/><br /><sub><b>chenjintang-shrimp</b></sub></a><br /><a href="#code-chenjintang-shrimp" title="Code">💻</a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/yuanbenxin"><img src="../app/resources/assets/contribution/contributor3.png" width="100px;" alt="yuanbenxin"/><br /><sub><b>yuanbenxin (本新同學)</b></sub></a><br /><a href="#code-yuanbenxin" title="Code">💻</a> <a href="#design-yuanbenxin" title="Design">🎨</a> <a href="#maintenance-yuanbenxin" title="Maintenance">🚧</a> <a href="#doc-yuanbenxin" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/LeafS825"><img src="../app/resources/assets/contribution/contributor4.png" width="100px;" alt="LeafS"/><br /><sub><b>LeafS</b></sub></a><br /><a href="#doc-LeafS" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/QiKeZhiCao"><img src="../app/resources/assets/contribution/contributor5.png" width="100px;" alt="QiKeZhiCao"/><br /><sub><b>QiKeZhiCao (棄稞之草)</b></sub></a><br /><a href="#ideas-QiKeZhiCao" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-QiKeZhiCao" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/Fox-block-offcial"><img src="../app/resources/assets/contribution/contributor6.png" width="100px;" alt="Fox-block-offcial"/><br /><sub><b>Fox-block-offcial</b></sub></a><br /><a href="#bug-Fox-block-offcial" title="Bug reports">🐛</a> <a href="#testing-Fox-block-offcial" title="Testing">⚠️</a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/jursin"><img src="../app/resources/assets/contribution/contributor7.png" width="100px;" alt="Jursin"/><br /><sub><b>Jursin</b></sub></a><br /><a href="#code-jursin" title="Code">💻</a> <a href="#design-jursin" title="Design">🎨</a> <a href="#maintenance-jursin" title="Maintenance">🚧</a> <a href="#doc-jursin" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/LHGS-github"><img src="../app/resources/assets/contribution/contributor8.png" width="100px;" alt="LHGS-github"/><br /><sub><b>LHGS-github</b></sub></a><br /><a href="#doc-LHGS-github" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/real01bit"><img src="../app/resources/assets/contribution/contributor9.png" width="100px;" alt="real01bit"/><br /><sub><b>real01bit</b></sub></a><br /><a href="#code-real01bit" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

## 💝 支持我們

如果您覺得 SecRandom 有幫助，歡迎支持我們的開發工作！

### 愛發電支援

> [!CAUTION]
> **愛發電是一個大陸網站。**在中國大陸之外，您可能不能正常訪問愛發電。

- 🌟 **[愛發電支援連接](https://afdian.com/a/lzy0983)** - 通過愛發電平臺支持開發者

## 📞 聯絡方式

* 📧 [電子郵件](mailto:lzy.12@foxmail.com)
* 👥 [QQ群 833875216](https://qm.qq.com/q/iWcfaPHn7W)
* 💬 [QQ頻道](https://pd.qq.com/s/4x5dafd34?b=9)
* 🎥 [B站主頁](https://space.bilibili.com/520571577)
* 🐛 [問題回饋](https://github.com/SECTL/SecRandom/issues)

## 📄 官方文檔

- 📄 **[SecRandom 官方文檔](https://secrandom.netlify.app)**
- [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SECTL/SecRandom)

## 📖 GitHub 貢獻教程

針對繁體中文貢獻教程的翻譯仍然在進行中。您可以先查看簡體中文的版本：[貢獻教程（簡體中文）](../CONTRIBUTING.md)

## ✨ Star 歷程

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=SECTL/SecRandom&type=Date&theme=dark">
  <img alt="Star History" src="https://api.star-history.com/svg?repos=SECTL/SecRandom&type=Date">
</picture>


**Copyright © 2025 SECTL**
