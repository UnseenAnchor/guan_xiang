# 观象 · 品牌图形

![图标](../../evidence/brand-512.png)

## 构成

陶土底（`#D97757`，CDS 主色）+ 纸白（`#F9F9F7`）「观象」二字，思源宋体，横向居中。

- 完整版 `icon.svg`：512 网格，圆角 112（22%），两字合计墨迹宽 410（左右各留约 10%），字距 14。
- 小尺寸版 `icon-small.svg`：字重 800 的单字「观」，墨迹宽 340，供 16/24px 使用。
  两个汉字在 16px 下每字只有约 6×7 像素，无法可靠辨认，因此小尺寸用单字，32px 起恢复「观象」二字。
- 两个 SVG 都是**纯路径**：字形由 fontTools 从 `NotoSerifSC-VF.ttf` 取轮廓后转曲，
  不在文件里引用字体，因此任何机器渲染结果一致，也不随包分发字体。

## 文件

| 文件 | 用途 |
| :--- | :--- |
| `icon.svg` / `icon-small.svg` | 矢量源（完整版 / 小尺寸版） |
| `icon-16 … 512.png` | 多尺寸位图（界面、favicon、manifest、文档） |
| `icon.ico` | 7 个尺寸的多层 ICO；16/24px 为单字「观」，其余为「观象」 |
| `../favicon.ico` | 根路径副本，供浏览器与 WebView2 默认请求 |

## 重新生成

```bash
cd desktop
python tools/make_wordmark.py      # 字体 → 矢量路径（需 fonttools + NotoSerifSC-VF.ttf）
python tools/make_brand.py         # 矢量 → 多尺寸 PNG / ICO（需 Playwright + Pillow）
go run github.com/tc-hib/go-winres@latest simply --arch amd64 --out rsrc \
  --icon ui/brand/icon.ico --manifest gui \
  --product-name "观象桌面版" --file-description "观象 · 纯本地四柱排盘客户端" \
  --file-version 1.0.0.0 --product-version 1.0.0.0 --original-filename "观象.exe"
bash build.sh                      # 重新编译 EXE（图标更新时会自动重建 rsrc_windows_amd64.syso）
```

## 权利说明

- 字形来自思源宋体（Noto Serif SC，SIL OFL-1.1），**只取轮廓转曲**，不打包、不再分发字体文件。
- 图形本身为本项目原创，不含任何第三方图标、图片或字体二进制。
- 品牌色取自 open-claude-ui 的 CDS 令牌值（颜色本身不构成作品）。
- ICO 必须逐帧写入专属 PNG；不要用 Pillow 的 `save(..., sizes=...)` 组装，它会把小尺寸帧替换成大图的缩放版。
  验收时从构建后的 EXE 提取 ICO，逐帧与 `icon-{size}.png` 比对，而不只看 SVG 或源 PNG。
- 历史探索稿（几何图形方案、GPT Image 2 生成的 7 版字标及其笔画对照）保留在
  [`evidence/logo-explorations/`](../../evidence/logo-explorations/)，仅作记录，不参与构建。
