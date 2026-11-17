# idea

短念头。源文件在 `notes/`，构建进 [shippingwang.com/idea](https://shippingwang.com/idea/)。

样式（front matter `style`，也可按篇幅自动选）：

| style | 样子 |
|-------|------|
| `lined` | 横线本，圆珠笔蓝字 |
| `receipt` | 小票 |
| `textbook` | 课本页 |
| `card` | 名片 |

文件名建议：`{style}-{slug}.md`，例如 `lined-pixelumm.md`、`card-shipping.md`。

```bash
python3 build.py
MSG="..." bash ../site/scripts/publish.sh idea
```
