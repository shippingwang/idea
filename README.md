# idea

短念头。源文件在 `notes/`，构建进 [shippingwang.com/idea](https://shippingwang.com/idea/)。

纸样按篇幅轮换（也可在 front matter 写死 `style`）：

| 长度 | 样式 |
|------|------|
| 短 | `slip` 小纸条 / `receipt` 小票 |
| 中 | `kraft` 牛皮纸 / `lined` 横线草稿 |
| 长 | `textbook` 课本页 / `lined` |

```bash
python3 build.py
```

```bash
MSG="..." bash ../site/scripts/publish.sh idea
```
