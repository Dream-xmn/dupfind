# dupfind

中文命令行工具：找出内容完全相同的重复文件。

默认只查看，**不删除、不移动**。不需要安装额外 Python 包。

## 需要什么

- Windows
- Python 3（能在终端里运行 `python`）

## 怎么运行

在仓库目录打开终端：

```text
python dupfind.py 文件夹路径
python dupfind.py 文件夹路径 --min-size 1mb
```

例如：

```text
python dupfind.py D:\Download
```

## 示例输出

```text
扫描完成：1234 个文件，跳过 5 个，发现 2 组重复，多占 80.0 MB

[1] 每个 40.0 MB，共 2 个
  D:\Download\a.mp4
  D:\Download\copy\a.mp4
```

没有重复时会打印：`没有发现重复文件`。

## 它怎么判断重复

1. 先比较文件大小
2. 大小相同的再计算 SHA-256
3. 哈希相同才算同一组

空文件会跳过。第 1 版不找“长得像”的照片。

## 参数

- `文件夹路径`：必填，会扫描子文件夹
- `--min-size`：忽略小于该大小的文件，支持 `123`、`1kb`、`1mb`、`1gb`

查看帮助：

```text
python dupfind.py -h
```
