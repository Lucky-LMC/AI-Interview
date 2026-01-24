# Git 操作指南 📚

## 📥 拉取最新代码

```bash
git pull origin main
```

---

## 📤 上传代码到 GitHub

```bash
# 1. 添加所有修改的文件
git add .

# 2. 提交到本地仓库（附带提交信息）
git commit -m "更新代码"

# 3. 推送到远程仓库
git push origin main
```

---

## 🚀 完整流程（推荐）

```bash
# === 一键执行（PowerShell通用版）===
git pull origin main; git add .; git commit -m "更新代码"; git push origin main

# === 分步执行 ===
# 先拉取最新代码（避免冲突）
git pull origin main

# 添加修改的文件
git add .

# 提交
git commit -m "更新代码"

# 推送
git push origin main
```

---

## 📝 提交信息示例

```bash
git commit -m "添加新功能"
git commit -m "修复bug"
git commit -m "更新文档"
git commit -m "优化代码"
```
