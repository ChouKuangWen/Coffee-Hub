#  Coffee Hub - 職人咖啡交易平台 (Coffee Hub Trading Platform)
基於 **FastAPI + Vue 3 + MySQL（Async）** 建構的全端系統，
專注於 **後端架構設計、系統穩定性與可觀測性（Observability）**。
 **三層架構重構 (API / Service / CRUD)**，並強化了 **交易安全性、審計追蹤、非同步併發處理**。 
目標是打造一個 **可擴展、可維護、具備安全防護** 的全端平台。
---

##  專案簡介
Coffee Hub 是一個支援多角色的應用系統，包含：

- 商品管理（Product）
- 訂單管理（Order）
- 購物車（Cart）
- 權限控管（RBAC）

本專案重點不在於功能數量，而在於：

- 系統架構設計（Layered Architecture）
- 非同步處理（Async）
- 錯誤處理與資料一致性（Transaction Control）
- 系統可觀測性（Logging / Audit Log）

---

## 專案價值

本專案以「後端工程實務」為核心，著重：
- **架構設計**：設計並落實 API / Service / CRUD 三層分離，提升維護性與測試性。
- **交易安全**：統一由 Service 層管理 commit/rollback，確保資料一致性。
- **可觀測性**：導入 request_id middleware、system log、audit log，提升問題追蹤能力。
- **安全防護**：實作 CSP、Rate Limiting、JWT + HttpOnly Cookie，符合企業級安全需求。
- **雲端部署**：使用 GCP Cloud Run + Cloud SQL，支援容器化與水平擴展

---

## 系統架構

<div align="center">
  <a href="https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1&dark=auto#R%3Cmxfile%3E%3Cdiagram%20name%3D%22%E7%AC%AC%201%20%E9%A1%B5%22%20id%3D%22em90Szxs1QBensiMStdb%22%3E7T1bc6M4ur9lH1K15yGULgjBY%2BIkPb2b7GSSnZ6Z8zKFDXHYto0X4ySeX78SIAcJGWQMtpO2uypthCSDvou%2Bu87wYPr2JfHnz3dxEE7OEAjezvDVGUIQA8T%2B4y2rvIUCJ28YJ1GQN4H3hsfor7AYKVqXURAuira8KY3jSRrN5cZRPJuFo1Rq85MkfpW7PcWTQGqY%2B%2BOw0vA48ifV1t%2BiIH3OW4mL39t%2FCqPxc%2FHLLqL5jakv%2BhYvsnj2g%2Fi11ISvz%2FAgieM0%2FzZ9G4QTvnbystxsuLt%2BriScpSYDgvDleTLz7n51vv0Op%2F%2B8md3crc6JtHj%2BULw1qM5e%2FOAiXYlO4yRezvPWF3%2ByLFqLhjBJw7fSyOKhvoTxNEyTFevyXFo2aBfr%2Bfq%2BxtBx87ZiGg%2Fa%2BXWBSZAW134B4vF67vdlYF%2BKldCvyp9%2FPb2ML5%2FRn0%2F2n8H5Xfx76H49x7j6%2BnXLV1oT%2Ft4Rw55bfxhO7uNFlEbxjN0axmkaT8%2FwpehwMYnG%2FEYaz1nrczplT3gF2VeGJ3M%2B2fRtzCnKGvqLaGTN%2FTQNk9lNNJk8ZGh%2B%2BcS%2BPhY%2FnNPS5SIN2WRXZH03ib%2BvsRZYSGofxJM4yR4aB9mnuFtq97zB4OYmm1gZAbIPu8MwJ%2FWjWcjb%2BfUe0KF7cNutwc1eKpXB9%2FocpeHj3B%2FxHq8MgpXlm8WzUFnroskvcGLEHoOvaAVZplEQ8J%2B%2BZJQ3C8KgWHQDIDiTDGdYR%2BkFnP8uY3HjfJEx3wvWAdrzt2wecZ99Gxf%2FZxMNRQOy2Dd%2Fyt9yNlzMS10YKIbqsMXcn23%2B%2FSd%2FGk1W%2BRMso%2FOFP1ucL8IkejpDDLDg3J%2FPJ%2BH5YsXQfJo3XU6i2fc7f%2FSYtd1kb8fb189UTP8YjuOQtf%2F6lf355idRxukQuIoW84m%2FUrs3T6Lr%2F1M4eQk5uPTDL%2FjTs%2FYc5ghcT%2BP%2FRGa%2F%2FK84jVnzI1sQ9t9F4g%2BjUZuRP4XDJHzVj7xgizLJv6oLX7uaW7yGNO5xNR3Gk8pAPhao2OgU2Agy4jpf5NTFb83igsQMUPU6GPNfv%2FVXIV%2F%2F8zpEZW05rlaacxKSm4PoRW3qjNJOJHMimYORjMrbv%2Fhp%2BJoBX0M5oIF4Ns66vs7%2F8jcNR8skSjf8UC0tsmaJHFtIHxhUhQ%2FiWlSSRm3LIeD9g2XZ1NldVNFKIMWvhEFFaTEUXeJlMgrrZCGvIuPwHxOCZpykz%2FE4nvmT6%2FdWRRp573Mbc%2BE2E4v%2BE6bpqtDu%2FCWjMEloKvQ6PxmHdS%2BBtdJlFZhJOPHT6EVeou7FRm%2BvYiOTurGDPayR08Psc9ajAPllcM%2B3ztgP%2BBbiT%2FzZiG%2BiLYgLeVXiYsTkOtiGtvgjURqCFqHQIxDlf1wqkRpBPdFaeyXww4H3JGychI0thI02MoWxQIw2CMR3GW6%2FMmrkT5f6o%2B%2FNkoAshuyNWzle6YNloxUgPW1HyD0SWx6CTmXREJRXySGOvCzCbNr5skBoIDLVLughRKHuRJxs6EWScC667jCPo1m6KM18zxtK4PEsD5ZwWAEWUSzNu4xmX%2FKn089FgTwYK0bAXKAtBrV%2FJkcRInJRtDJthoFrKOyAlO1R8FMZmLl5%2BdrRyUI9G5hreVT3rLk9uH94AzO0uEw2icJs4pLxDtwkbM5wFmxlJOjIHEBlYwB0LSIrJT1hktsek3R4U0KrTTrHZi2lESnu4mGUidT8nZkwHy6%2Bc2bE1ALulm2pP2JahYZDZBHMVqBhg57A4Z1kixayhQQbz27Yt2t6N8gOyliqiJjmooMsKwAFm3qWFYRkvAOSNRn9RKzFoY1%2B%2BocTO%2FxxWP2gRp06Xhb8bcn5L%2BYa8%2F1FV%2FzWg1YDw4Wgt%2BXfQZba%2F%2FI%2Fpn7KAXDnz%2FxxOA0LDtHFngdti8pQgMhyadnyoMBE1XE6M5S6BgxKWBwaWdEhOBF7ymT1e6bCQA6MvOGPrMF2XNFw9Vb8RH61Kl%2Fdh0nEVnONCuFblOYzOi4prvMJMXGL6%2Ff5%2BMWqdKHOZsgqcecOklY7vAtkzEM2rN1gXUDr%2Bjfs8q6N2Rq%2Fe%2BKgPBfwLEUYN9332WNZJQ%2BfCGQUE3u2OnF3gsDt4GI1DP7%2Frz9WV7%2Bvwl9%2F%2Be3a%2BafwRxzcvkdRhRvZIl5LhOoB2R2Kvb4kcMEay29ft3qfxpKi7j3T%2BKVACf5kSch07fJ1zHai0nUQTsLydRhE5ctJPPpeVv5LCLdRj%2BgUjzrHE%2BElbIEnDWKDCgitLebA0Gnw7o3yh%2BWGmWQ8%2FDuBuX%2Fo%2Ff%2F%2F09pqBkm8WJyPlmkazcY1YYC6YJCun6XsHerQ%2FVMVvJCIXxezVGw%2FfaGwrWH0hijc0iENAcWeakpk7UMYBE%2BgT3viQy4330bTKEeuzOL3OIlfL%2B6%2FtpOhNVY8jCyK3iMLkARYl23%2BpagDxY%2BH%2B9rQbI3w%2FFmhPPj54fFMmAcHj%2FddAdYFMonanoXKkhzpHJRaCP1AkHwI%2F7sMF1x4%2FnrVExSRcP31ToHtRYWWcBvaDmEScwVuT35A%2FVGfcLt%2BG4XzTO5F4Cd%2FxuZIOuOuEDGqQzaT%2FYs%2FEjgxcizPc6kL7OyP1zlwtTAT2tLhtahqhgvbkKQlWieZiUVx%2BworNcV4VDUUf2wtSrX5wYCEVEeinkOx73Sn%2B9RAv3OcN1WRNdD9YO7niv93Z3805u7nh%2BUsjaZK8ggYTOJlkN9tjkQbdu2CRpDht2IAtrBs%2F1UMwJaLS3dpBz5qvdijiYs2xbf9m%2BgbFVJOAucF5nJUmYRPqV4dLuMDeAyTl2jUqTaKoaUJW4EZ3CVEsInlymZQvC%2FgExOXuKkzAFclrP16A6hzJjkDHHK2ky8A2%2Fis7AvwiHPWzhdwYBO%2FJ4x3a3nNLaNOc3%2Fs1PZ3XW%2Bn%2FjYmCirXuRCYHGqhMnko70aZpFqK6VWkMFN%2FAiVQ8idA5YltS5m4Z3%2BC8AceXhSmboWrEVdWF2woR2wSwWi61xBM1Xaxfp9VGH4i%2FF8hK5X31uyj23Wd7NOdkFyHF93D3VQJ0sD9g4nJ3Udp2lxM5hk07DELc4IUqukv0sxwu%2FdITZ2YjLCl2JL6wqli1zJisaa41mWmBrGr4qQLLLGZCsubEk3ZQWyPngI10a21y%2FppOO9%2BwNk9wDQpkqYAK1hmg8JXYYWVlcrYimA2bRatusc4nuXITj5CLKfGg9DblmSqSWvW9yNr0verwJ%2BlPIcSfGP9g2JLOYAmjTyLEm%2BjZtDbvmEqi%2BwMeIgcel0NW8gycJzrixsN4BVx8Cn79IsQOZE%2FxMs0XOwBD0So19rFL0EddZHCqYemphCVKdjF9vUcvvljvvVdzkuGg6J1bUtAzaz3KXoLRT0%2BDeLsoB3kAuYVtQixgYs826GUItpJ7ArIw0TEf3mwCDBGtH%2F89m8uyC7T55AzoO4ZD6piGyYWlh0%2FCFm0FNEIZDdQb9s5NgnkrcfHkkVP37FaLOEgmQa1XPfQCTKyqQwW8N6YnlLbXbZ8dRaKSn4kRuUy%2BiTQcTwMIWGbvn0EjOrh8oKPG7B3SrIyDb2yKDV7X8Y427VgWUjqIJVfrwybpPIb86c6R%2FieHQ5r%2F4BtI8k%2F4NKt3QMl7wXylFwGXmWhhf%2FiKLgiUkLKz2GhfW7ii5UBXr2LgqBdutP6znhz5wbfBHsNC7nv3gdXXQVkITWzx9QjQZDlQs919R4JjHmATkXn7d47kXyLrr5%2F%2B%2BMf%2Fxp%2BvbuavC6nXy%2Fuzp2daf1QTkOb7cAS2fE4no9Kdq4iXWBggbJoWp%2B9qwQw1Y9uyvNRnoQp65q5ts%2FyQZZNCM%2FqzT8yfWV7W9n0o8To9Oyis4%2FcfmxXlWcCZOOxiFpfm0w6qOKsp3tTY5n92azHHy%2F1pxZxOscM48QJDWZ0ZaZuVA%2FqaqoBw6QY8DSJ%2FVQMz3yJ7FtQFNHLmqPZJJrxSLa%2FRdM52%2Bf8mV6%2F6KBsG3jyR%2FKYUgU%2B9fculwv2XAteBe82HmemX27T30eJN01yNVUSCByv%2BxwfPQaaSjkaVN3O8Ov4AGRm26rFnwIwGPRq%2BD2VkzyVk8wGHq6c5H0SB8sRn6MaqdkXq9ngboAKt6mUL%2BrL32Cc6aLhNmz6aL4IDfbGxTw%2Flyez02nsc8DHwK%2Byl3UFuAqDuryi%2BZ0K4%2Fl3wnDZHxURKHnVjaQVqKC28qcs2kIhsayrnqC%2BAGXqaD9tC6dt4bQt7LAt%2FJwEWdTa8W0KSrhwb3uCqQ96Z1YzGBQM5RChBydWc2I1B2Y1F1lMy8WXI%2BQ2yNmXBGrqSD4JNiduc%2BI2O3CbgZ8co7K7zmnvkNNo%2FYkmJycZ674%2FSKleSPE6IFYEnxEB1U0ONZNBDa4%2BzRTUWWPTth4%2BzWwQwMp0PbvyyBbHcxzAlQc1cfDQg7IOAmV7h4N689iYliwgn%2B2AhD1As3PWKgpXbM9biaZCtb7jQeJG3wOzyiVcxR19TFb%2BnI2xpuL8m%2F1XtdYTnGnqlYbgTvURhft1z4LdVg7WK7aCXA4ejQova54xdQj3qrKtECVCpCcUJyZ19D8il%2FqYHIeYav4ajvP5zlc8Zs7xEM65FBVnyHGfS0H7YBw6B1zt0XsYW6B89B6WVUtM1YLd3SGzc0Lmk7XrZO06GmvX4y%2B3F5PRczjlXOVisZrxgLKfH%2B4OxLcItpQK%2BdC1qFeKXqaKxaSDKFmtrtZaVdOYH8JZcJEk8StnMhN%2FwZRkmY%2FJfKV8yIa9PlOjSEyxdyysxRdMKqyFRaGtzgtrlWEtRFetyCTFtm4Gp95oRakFPAeLyHMlA5k6lufCjRlXxhWpqOXA92lcpcCuhyybVupV7Sn%2FgxwDoiIi4WkTjvaAjo1iveArh8HbrevGqSlG9XlTSImwUvo3lXVTqaYlmfDzriBxRG1NqiETt5SJ0ptdWW98A4cjlPe8RSjnLeL%2B6hoeBRpDYFvY3VwXBNanbGPq1PVv8o4AOTFPqYyXbQ5OqRBsS7dJ5SE9tF%2FEbp3t2%2BUOwNRNRVRxUdM2sDmZr7kEgfehyEBxCCGvHu9tWtu%2FCe%2FVX2vLz7EHsrM91nKPclgVRRbApZw%2FJbOwb7xHO%2BN9k53S1hDI8dgpiSEJ9FzhVk5dZQJAvYwgd3eKbNVeq3A4Jsqc5kDFrXjhIfmRZutTjgoUdYe3DwqozKSW1ek5HoAW63Hw6rtQnBNaPodNMGpR8EORMSC2ldXqrsiHafwxra7Kx3b9bzr8ZfNxMXtAgO7ha%2Br30cC3ZTKu2cIWnuiYzRulHM%2B9vbtyzLwyO5hFCS%2FT%2B3X2lPjs3ZejdJmoh1p8GdzvIzZQExjoqKdKQ%2BKujzgW22pfSGnqv9EgpWAZgZ%2ByVY2TsBlDFYQMSOgGto7SXTTEmwpqH4NHUU1M1xa1aul2FMdpPP5yW%2BDm3Sr73jt2Uk1GOFLN97J02BtimgbCaRCzswzNNqcifQmn0SxibXnpTg6%2B6ze%2BiXK%2FlJr10GbTMsnPVLhHf1AyjZ7qhX08uaNwpBcUXGKTj7%2BLbcll8ofKNrL1GU238XicH1J7BMwDC%2F27Q7zUmhJQ65CnNaI2HtFDq3ynta0NKfXqeJG1ndyCrmNLdmkXi2tzu3Q1%2FTz7x%2B4E%2FuI5e48tAvaPwm7nUDnkjgnlDTVGqVp8r6jFuNHSZxNlAJHK6TWY%2BhxH1jfPsaOEBZrq%2BesTxQWtKfaCno15QmL9YSnQQXhnCpTobDM5fiQKJI5ax9FrICioEpQHtiAoolTPO8fqpmNMUJB7n97dS%2FWCcN9GNCNj2efT0I5DxPrGtIYs%2Bo3Hlg%2F9xT6yCk10M6iWxMaor6xCEwFLo5n9IPmDRDk5SIgRm%2BvR1vZv4nHqaEeBunlZXGUiT2H%2FfXsATXJVNeJBbWjyUfr6nIPlJOilNa%2FDhReu%2FIPVEociBqeIyVnH6LQqJk5tJRCCuzxbiIZbqVPNCGQfBaNzFHEOimjJjZGXypky2w%2BAtL78ORUeutYDcINIqp7pqg5o1PGoBQBeR1nIk3lZjAZWA6y2jnDFQPUhQAioRfcbpIdNYpkOIid0a93ol8qoCkl7q6oC6nDPbWlTcKFjMewFyMZZKCDVP9XekGsbceEYkau8y1B5k9mhcP5H2Tuop7LRhsMkPJfsOsDDZ1vQjfKA7ekG46Oim5bKW8sY6Y%2BeorL1yRFQrbli1wsgEKmHLwB7qwMilB9sjadQTTtgFLbfGFCjk9iOCzW35%2FUudhSNgrrHwO6Pg3o8JeKuiXoqAyCoj1iFAFYEY2lEE7kpP9ie3IAweKx3gn2HXG9BbU1qP6pmeI%2BWyUuJANrRqOPJKTY23T7FpgWNghONbqRR4sjbBCWSS6baX0lIow1OVErUGmiovr%2FijGnq7ypn81CnYYMGSHam0oajKSGoVEh3t5I8FUO%2Bqwrf5iwG2%2BqDKMkjrVkMu0xi7hd5785Dh%2B%2FiIOQ9%2Fgc%3D%3C%2Fdiagram%3E%3C%2Fmxfile%3E" target="_blank">
    <img src="https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1&dark=auto#R%3Cmxfile%3E%3Cdiagram%20name%3D%22%E7%AC%AC%201%20%E9%A1%B5%22%20id%3D%22em90Szxs1QBensiMStdb%22%3E7T1bc6M4ur9lH1K15yGULgjBY%2BIkPb2b7GSSnZ6Z8zKFDXHYto0X4ySeX78SIAcJGWQMtpO2uypthCSDvou%2Bu87wYPr2JfHnz3dxEE7OEAjezvDVGUIQA8T%2B4y2rvIUCJ28YJ1GQN4H3hsfor7AYKVqXURAuira8KY3jSRrN5cZRPJuFo1Rq85MkfpW7PcWTQGqY%2B%2BOw0vA48ifV1t%2BiIH3OW4mL39t%2FCqPxc%2FHLLqL5jakv%2BhYvsnj2g%2Fi11ISvz%2FAgieM0%2FzZ9G4QTvnbystxsuLt%2BriScpSYDgvDleTLz7n51vv0Op%2F%2B8md3crc6JtHj%2BULw1qM5e%2FOAiXYlO4yRezvPWF3%2ByLFqLhjBJw7fSyOKhvoTxNEyTFevyXFo2aBfr%2Bfq%2BxtBx87ZiGg%2Fa%2BXWBSZAW134B4vF67vdlYF%2BKldCvyp9%2FPb2ML5%2FRn0%2F2n8H5Xfx76H49x7j6%2BnXLV1oT%2Ft4Rw55bfxhO7uNFlEbxjN0axmkaT8%2FwpehwMYnG%2FEYaz1nrczplT3gF2VeGJ3M%2B2fRtzCnKGvqLaGTN%2FTQNk9lNNJk8ZGh%2B%2BcS%2BPhY%2FnNPS5SIN2WRXZH03ib%2BvsRZYSGofxJM4yR4aB9mnuFtq97zB4OYmm1gZAbIPu8MwJ%2FWjWcjb%2BfUe0KF7cNutwc1eKpXB9%2FocpeHj3B%2FxHq8MgpXlm8WzUFnroskvcGLEHoOvaAVZplEQ8J%2B%2BZJQ3C8KgWHQDIDiTDGdYR%2BkFnP8uY3HjfJEx3wvWAdrzt2wecZ99Gxf%2FZxMNRQOy2Dd%2Fyt9yNlzMS10YKIbqsMXcn23%2B%2FSd%2FGk1W%2BRMso%2FOFP1ucL8IkejpDDLDg3J%2FPJ%2BH5YsXQfJo3XU6i2fc7f%2FSYtd1kb8fb189UTP8YjuOQtf%2F6lf355idRxukQuIoW84m%2FUrs3T6Lr%2F1M4eQk5uPTDL%2FjTs%2FYc5ghcT%2BP%2FRGa%2F%2FK84jVnzI1sQ9t9F4g%2BjUZuRP4XDJHzVj7xgizLJv6oLX7uaW7yGNO5xNR3Gk8pAPhao2OgU2Agy4jpf5NTFb83igsQMUPU6GPNfv%2FVXIV%2F%2F8zpEZW05rlaacxKSm4PoRW3qjNJOJHMimYORjMrbv%2Fhp%2BJoBX0M5oIF4Ns66vs7%2F8jcNR8skSjf8UC0tsmaJHFtIHxhUhQ%2FiWlSSRm3LIeD9g2XZ1NldVNFKIMWvhEFFaTEUXeJlMgrrZCGvIuPwHxOCZpykz%2FE4nvmT6%2FdWRRp573Mbc%2BE2E4v%2BE6bpqtDu%2FCWjMEloKvQ6PxmHdS%2BBtdJlFZhJOPHT6EVeou7FRm%2BvYiOTurGDPayR08Psc9ajAPllcM%2B3ztgP%2BBbiT%2FzZiG%2BiLYgLeVXiYsTkOtiGtvgjURqCFqHQIxDlf1wqkRpBPdFaeyXww4H3JGychI0thI02MoWxQIw2CMR3GW6%2FMmrkT5f6o%2B%2FNkoAshuyNWzle6YNloxUgPW1HyD0SWx6CTmXREJRXySGOvCzCbNr5skBoIDLVLughRKHuRJxs6EWScC667jCPo1m6KM18zxtK4PEsD5ZwWAEWUSzNu4xmX%2FKn089FgTwYK0bAXKAtBrV%2FJkcRInJRtDJthoFrKOyAlO1R8FMZmLl5%2BdrRyUI9G5hreVT3rLk9uH94AzO0uEw2icJs4pLxDtwkbM5wFmxlJOjIHEBlYwB0LSIrJT1hktsek3R4U0KrTTrHZi2lESnu4mGUidT8nZkwHy6%2Bc2bE1ALulm2pP2JahYZDZBHMVqBhg57A4Z1kixayhQQbz27Yt2t6N8gOyliqiJjmooMsKwAFm3qWFYRkvAOSNRn9RKzFoY1%2B%2BocTO%2FxxWP2gRp06Xhb8bcn5L%2BYa8%2F1FV%2FzWg1YDw4Wgt%2BXfQZba%2F%2FI%2Fpn7KAXDnz%2FxxOA0LDtHFngdti8pQgMhyadnyoMBE1XE6M5S6BgxKWBwaWdEhOBF7ymT1e6bCQA6MvOGPrMF2XNFw9Vb8RH61Kl%2Fdh0nEVnONCuFblOYzOi4prvMJMXGL6%2Ff5%2BMWqdKHOZsgqcecOklY7vAtkzEM2rN1gXUDr%2Bjfs8q6N2Rq%2Fe%2BKgPBfwLEUYN9332WNZJQ%2BfCGQUE3u2OnF3gsDt4GI1DP7%2Frz9WV7%2Bvwl9%2F%2Be3a%2BafwRxzcvkdRhRvZIl5LhOoB2R2Kvb4kcMEay29ft3qfxpKi7j3T%2BKVACf5kSch07fJ1zHai0nUQTsLydRhE5ctJPPpeVv5LCLdRj%2BgUjzrHE%2BElbIEnDWKDCgitLebA0Gnw7o3yh%2BWGmWQ8%2FDuBuX%2Fo%2Ff%2F%2F09pqBkm8WJyPlmkazcY1YYC6YJCun6XsHerQ%2FVMVvJCIXxezVGw%2FfaGwrWH0hijc0iENAcWeakpk7UMYBE%2BgT3viQy4330bTKEeuzOL3OIlfL%2B6%2FtpOhNVY8jCyK3iMLkARYl23%2BpagDxY%2BH%2B9rQbI3w%2FFmhPPj54fFMmAcHj%2FddAdYFMonanoXKkhzpHJRaCP1AkHwI%2F7sMF1x4%2FnrVExSRcP31ToHtRYWWcBvaDmEScwVuT35A%2FVGfcLt%2BG4XzTO5F4Cd%2FxuZIOuOuEDGqQzaT%2FYs%2FEjgxcizPc6kL7OyP1zlwtTAT2tLhtahqhgvbkKQlWieZiUVx%2BworNcV4VDUUf2wtSrX5wYCEVEeinkOx73Sn%2B9RAv3OcN1WRNdD9YO7niv93Z3805u7nh%2BUsjaZK8ggYTOJlkN9tjkQbdu2CRpDht2IAtrBs%2F1UMwJaLS3dpBz5qvdijiYs2xbf9m%2BgbFVJOAucF5nJUmYRPqV4dLuMDeAyTl2jUqTaKoaUJW4EZ3CVEsInlymZQvC%2FgExOXuKkzAFclrP16A6hzJjkDHHK2ky8A2%2Fis7AvwiHPWzhdwYBO%2FJ4x3a3nNLaNOc3%2Fs1PZ3XW%2Bn%2FjYmCirXuRCYHGqhMnko70aZpFqK6VWkMFN%2FAiVQ8idA5YltS5m4Z3%2BC8AceXhSmboWrEVdWF2woR2wSwWi61xBM1Xaxfp9VGH4i%2FF8hK5X31uyj23Wd7NOdkFyHF93D3VQJ0sD9g4nJ3Udp2lxM5hk07DELc4IUqukv0sxwu%2FdITZ2YjLCl2JL6wqli1zJisaa41mWmBrGr4qQLLLGZCsubEk3ZQWyPngI10a21y%2FppOO9%2BwNk9wDQpkqYAK1hmg8JXYYWVlcrYimA2bRatusc4nuXITj5CLKfGg9DblmSqSWvW9yNr0verwJ%2BlPIcSfGP9g2JLOYAmjTyLEm%2BjZtDbvmEqi%2BwMeIgcel0NW8gycJzrixsN4BVx8Cn79IsQOZE%2FxMs0XOwBD0So19rFL0EddZHCqYemphCVKdjF9vUcvvljvvVdzkuGg6J1bUtAzaz3KXoLRT0%2BDeLsoB3kAuYVtQixgYs826GUItpJ7ArIw0TEf3mwCDBGtH%2F89m8uyC7T55AzoO4ZD6piGyYWlh0%2FCFm0FNEIZDdQb9s5NgnkrcfHkkVP37FaLOEgmQa1XPfQCTKyqQwW8N6YnlLbXbZ8dRaKSn4kRuUy%2BiTQcTwMIWGbvn0EjOrh8oKPG7B3SrIyDb2yKDV7X8Y427VgWUjqIJVfrwybpPIb86c6R%2FieHQ5r%2F4BtI8k%2F4NKt3QMl7wXylFwGXmWhhf%2FiKLgiUkLKz2GhfW7ii5UBXr2LgqBdutP6znhz5wbfBHsNC7nv3gdXXQVkITWzx9QjQZDlQs919R4JjHmATkXn7d47kXyLrr5%2F%2B%2BMf%2Fxp%2BvbuavC6nXy%2Fuzp2daf1QTkOb7cAS2fE4no9Kdq4iXWBggbJoWp%2B9qwQw1Y9uyvNRnoQp65q5ts%2FyQZZNCM%2FqzT8yfWV7W9n0o8To9Oyis4%2FcfmxXlWcCZOOxiFpfm0w6qOKsp3tTY5n92azHHy%2F1pxZxOscM48QJDWZ0ZaZuVA%2FqaqoBw6QY8DSJ%2FVQMz3yJ7FtQFNHLmqPZJJrxSLa%2FRdM52%2Bf8mV6%2F6KBsG3jyR%2FKYUgU%2B9fculwv2XAteBe82HmemX27T30eJN01yNVUSCByv%2BxwfPQaaSjkaVN3O8Ov4AGRm26rFnwIwGPRq%2BD2VkzyVk8wGHq6c5H0SB8sRn6MaqdkXq9ngboAKt6mUL%2BrL32Cc6aLhNmz6aL4IDfbGxTw%2Flyez02nsc8DHwK%2Byl3UFuAqDuryi%2BZ0K4%2Fl3wnDZHxURKHnVjaQVqKC28qcs2kIhsayrnqC%2BAGXqaD9tC6dt4bQt7LAt%2FJwEWdTa8W0KSrhwb3uCqQ96Z1YzGBQM5RChBydWc2I1B2Y1F1lMy8WXI%2BQ2yNmXBGrqSD4JNiduc%2BI2O3CbgZ8co7K7zmnvkNNo%2FYkmJycZ674%2FSKleSPE6IFYEnxEB1U0ONZNBDa4%2BzRTUWWPTth4%2BzWwQwMp0PbvyyBbHcxzAlQc1cfDQg7IOAmV7h4N689iYliwgn%2B2AhD1As3PWKgpXbM9biaZCtb7jQeJG3wOzyiVcxR19TFb%2BnI2xpuL8m%2F1XtdYTnGnqlYbgTvURhft1z4LdVg7WK7aCXA4ejQova54xdQj3qrKtECVCpCcUJyZ19D8il%2FqYHIeYav4ajvP5zlc8Zs7xEM65FBVnyHGfS0H7YBw6B1zt0XsYW6B89B6WVUtM1YLd3SGzc0Lmk7XrZO06GmvX4y%2B3F5PRczjlXOVisZrxgLKfH%2B4OxLcItpQK%2BdC1qFeKXqaKxaSDKFmtrtZaVdOYH8JZcJEk8StnMhN%2FwZRkmY%2FJfKV8yIa9PlOjSEyxdyysxRdMKqyFRaGtzgtrlWEtRFetyCTFtm4Gp95oRakFPAeLyHMlA5k6lufCjRlXxhWpqOXA92lcpcCuhyybVupV7Sn%2FgxwDoiIi4WkTjvaAjo1iveArh8HbrevGqSlG9XlTSImwUvo3lXVTqaYlmfDzriBxRG1NqiETt5SJ0ptdWW98A4cjlPe8RSjnLeL%2B6hoeBRpDYFvY3VwXBNanbGPq1PVv8o4AOTFPqYyXbQ5OqRBsS7dJ5SE9tF%2FEbp3t2%2BUOwNRNRVRxUdM2sDmZr7kEgfehyEBxCCGvHu9tWtu%2FCe%2FVX2vLz7EHsrM91nKPclgVRRbApZw%2FJbOwb7xHO%2BN9k53S1hDI8dgpiSEJ9FzhVk5dZQJAvYwgd3eKbNVeq3A4Jsqc5kDFrXjhIfmRZutTjgoUdYe3DwqozKSW1ek5HoAW63Hw6rtQnBNaPodNMGpR8EORMSC2ldXqrsiHafwxra7Kx3b9bzr8ZfNxMXtAgO7ha%2Br30cC3ZTKu2cIWnuiYzRulHM%2B9vbtyzLwyO5hFCS%2FT%2B3X2lPjs3ZejdJmoh1p8GdzvIzZQExjoqKdKQ%2BKujzgW22pfSGnqv9EgpWAZgZ%2ByVY2TsBlDFYQMSOgGto7SXTTEmwpqH4NHUU1M1xa1aul2FMdpPP5yW%2BDm3Sr73jt2Uk1GOFLN97J02BtimgbCaRCzswzNNqcifQmn0SxibXnpTg6%2B6ze%2BiXK%2FlJr10GbTMsnPVLhHf1AyjZ7qhX08uaNwpBcUXGKTj7%2BLbcll8ofKNrL1GU238XicH1J7BMwDC%2F27Q7zUmhJQ65CnNaI2HtFDq3ynta0NKfXqeJG1ndyCrmNLdmkXi2tzu3Q1%2FTz7x%2B4E%2FuI5e48tAvaPwm7nUDnkjgnlDTVGqVp8r6jFuNHSZxNlAJHK6TWY%2BhxH1jfPsaOEBZrq%2BesTxQWtKfaCno15QmL9YSnQQXhnCpTobDM5fiQKJI5ax9FrICioEpQHtiAoolTPO8fqpmNMUJB7n97dS%2FWCcN9GNCNj2efT0I5DxPrGtIYs%2Bo3Hlg%2F9xT6yCk10M6iWxMaor6xCEwFLo5n9IPmDRDk5SIgRm%2BvR1vZv4nHqaEeBunlZXGUiT2H%2FfXsATXJVNeJBbWjyUfr6nIPlJOilNa%2FDhReu%2FIPVEociBqeIyVnH6LQqJk5tJRCCuzxbiIZbqVPNCGQfBaNzFHEOimjJjZGXypky2w%2BAtL78ORUeutYDcINIqp7pqg5o1PGoBQBeR1nIk3lZjAZWA6y2jnDFQPUhQAioRfcbpIdNYpkOIid0a93ol8qoCkl7q6oC6nDPbWlTcKFjMewFyMZZKCDVP9XekGsbceEYkau8y1B5k9mhcP5H2Tuop7LRhsMkPJfsOsDDZ1vQjfKA7ekG46Oim5bKW8sY6Y%2BeorL1yRFQrbli1wsgEKmHLwB7qwMilB9sjadQTTtgFLbfGFCjk9iOCzW35%2FUudhSNgrrHwO6Pg3o8JeKuiXoqAyCoj1iFAFYEY2lEE7kpP9ie3IAweKx3gn2HXG9BbU1qP6pmeI%2BWyUuJANrRqOPJKTY23T7FpgWNghONbqRR4sjbBCWSS6baX0lIow1OVErUGmiovr%2FijGnq7ypn81CnYYMGSHam0oajKSGoVEh3t5I8FUO%2Bqwrf5iwG2%2BqDKMkjrVkMu0xi7hd5785Dh%2B%2FiIOQ9%2Fgc%3D%3C%2Fdiagram%3E%3C%2Fmxfile%3E" alt="Coffee Hub System Architecture" width="850">
  </a>
  <p align="center">
    <em>Coffee Hub 系統架構圖：展示從入口防護、FastAPI 三層架構到 RAG AI 服務的完整流量與事務控管。</em>
  </p>
</div>


---

## 核心設計（Engineering Design）

### 1.分層架構（Layered Architecture）

- API：處理 request / response
- Service：商業邏輯與流程控制
- CRUD：資料庫操作

提升可維護性與測試性

---

### 2.Transaction 控制

- commit / rollback 統一由 Service 層管理
- CRUD 不直接 commit

確保資料一致性與錯誤復原能力

---

### 3.非同步架構（Async）

- 使用 async / await
- FastAPI + SQLAlchemy Async

提升併發處理能力

---

### 4️.可觀測性（Observability）

- request_id middleware（請求追蹤）
- system log（API 層）
- audit log（非同步紀錄使用者行為）

可追蹤系統行為與錯誤來源

---

### 錯誤處理策略
- DB error → rollback
- 記錄 log，不影響主流程

---


## 核心技術棧 (Technology Stack)

| 類別 | 技術 |
|------|------|
| Backend | FastAPI（Python, async） |
| Database | MySQL |
| ORM | SQLAlchemy Async |
| Frontend | Vue 3 |
| Auth | JWT（HttpOnly Cookie） |
| Security | CSP / Rate Limit / Bcrypt |
| Cloud | GCP Cloud Run + Cloud SQL |
| Container | Docker |

---

## 安全設計（Security）

- CSP（Content Security Policy）防止 XSS
- Rate Limiting（SlowAPI）防止濫用
- JWT + HttpOnly Cookie
- 密碼雜湊（bcrypt）

---

## 核心功能（Core Features）

- RBAC 多角色權限控管（Admin / Seller / Customer）
- 訂單管理（建立 / 更新 / 刪除）
- 購物車狀態管理（Pinia）

---

### Service Layer 架構
- 商業邏輯與資料庫解耦
- 集中 transaction 控制

---

### 錯誤處理策略
- DB error → rollback
- 記錄 log，但不影響主流程

---

### Logging 系統
- System Log（middleware）
- Audit Log（BackgroundTasks 非同步寫入）

---

## 金流設計（簡述）

> 目前尚未串接第三方金流，僅預留設計

- 訂單狀態支援付款流程（PENDING / PAID）
- 預留第三方支付整合（如 Webhook 回調）
- 設計考量：冪等性 / 狀態一致性

---


##  專案結構與檔案說明
```
Member-order-management-system/
├── backend/                          # 後端主程式
│   ├── app/
│   │   ├── api/                      # API 路由
│   │   ├── core/                     # 核心設定模組 middleware / logging / security
│   │   ├── crud/                     # 資料庫操作層
│   │   ├── models/                   # ORM 模型
│   │   ├── schemas/                  # Pydantic定義驗證API請求與回傳的資料結構
│   │   ├── services/                 # 商業邏輯層（Transaction / Business rules）
│   │   ├── dependencies.py           # 依賴與權限判斷
│   │   └── main.py                   # FastAPI 進入點
│   │
│   ├── scripts/                      # 開發輔助腳本（資料同步 / RAG / 實驗用）
│   │
│   ├── tests/                        # 單元測試
│   │
│   ├── Dockerfile                    # 後端 Docker 設定
│   └── requirements.txt              # 依賴套件列表
│
├── database/                         # 資料庫初始化 SQL
│
├── frontend/                         # 前端專案
│   ├── public/                       # 靜態資源
│   │
│   ├── src/
│   │   ├── assets/                   # 靜態資源（CSS / 圖片模組化）
│   │   ├── components/               # 可重用元件
│   │   ├── stores/                   # Pinia 狀態管理（auth / cart）
│   │   ├── views/                    # 頁面
│   │   ├── App.vue                   # 根元件
│   │   ├── api.js                    # 後端 API 串接設定
│   │   ├── main.js                   # Vue 入口
│   │   ├── router.js                 # Vue Router 設定
│   │   └── style.css                 # 全域樣式
│   │
│   ├── .dockerignor
│   ├── .gitignore
│   ├── Dockerfile                    # 前端 Docker 設定
│   ├── index.html
│   ├── nginx.conf
│   ├── package-lock.json
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── README.md
└── .gitignore
```
---

## 測試（Testing）

- pytest（基礎功能測試）
- 持續補強中（API / transaction / service）

---

## 安裝與使用方式

1. 環境安裝
```
git clone https://github.com/ChouKuangWen/Coffee-Hub.git
cd Coffee-Hub
```
```
pip install -r requirements.txt
```

2. 環境變數設定
```
# Database 設定
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=mysql
DB_PORT=3306
DB_NAME=coffee_hub_db

# MySQL 初始化設定
MYSQL_ROOT_PASSWORD=your_password
MYSQL_DATABASE=coffee_hub_db

# JWT 設定
SECRET_KEY=使用_openssl_rand_hex_32_生成的隨機字串
ALGORITHM=HS256

# GCP 雲端相關 (選填)
GCP_BUCKET_NAME=your-gcs-bucket-name
```

3. 啟動
```
docker-compose up --build
```

4. 訪問網址
啟動成功後，您可以透過以下網址存取服務：
```
http://localhost:3000
```
---

## 專案未來規劃 (Roadmap)

本專案持續優化性能與擴展功能，目前已規劃以下三大核心迭代目標：

---
### 1.  AI 智能助手整合 (RAG 檢索增強生成)
* **技術路徑**：導入大語言模型 (LLM) 並結合向量資料庫。
* **功能目標**：實作「咖啡職人 AI 助手」，能根據平台現有商品資訊回答用戶提問，並根據用戶口味偏好提供精準的咖啡豆推薦。

### 2.  進階防禦機制 (CSRF Token 實作)
* **技術路徑**：在現有 `SameSite` Cookie 防護基礎上，新增 **Double Submit Cookie** 驗證機制。
* **功能目標**：針對金流結帳、修改權限等高敏感操作提供銀行級防禦，確保請求 100% 來自合法授權前端。
---
