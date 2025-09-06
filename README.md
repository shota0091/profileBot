# ProfileBot

Discord プロフィール登録 Bot。ユーザーが自分のプロフィール（名前、性別、都道府県、年齢、誕生日、職業、趣味、特技、好きなタイプ、ひとこと）を登録でき、プロフィール表示や削除が可能。

---

## 📂 モジュール構成

```
profileBot/
├── app.py                 # エントリーポイント (Bot起動)
├── config/
│   └── constants.py       # 地域・性別など固定値リスト
├── db/
│   └── connection.py      # DB接続管理 (pymysql)
├── models/
│   └── user.py            # Userモデル定義
├── repositories/
│   └── user_repo.py       # Userテーブル操作 (CRUD)
├── services/
│   └── profile_service.py # ビジネスロジック (登録/削除/チェック)
├── ui/
│   └── flows.py           # UIフロー (Select, Modal, View)
├── views/
│   └── profile_view.py    # Embed表示生成
├── requirements.txt       # 依存パッケージ
├── .env.example           # 環境変数サンプル
└── README.md              # 本ドキュメント
```

---

## 🗄️ データベース構成

### users テーブル

| カラム名         | 型        | 説明 |
|------------------|-----------|------|
| id               | BIGINT    | DiscordユーザーID (PK) |
| name             | VARCHAR   | ユーザー名 |
| age              | INT NULL  | 年齢 (秘密の場合はNULL) |
| birth_year       | INT NULL  | 誕生年（未使用だがDB保持可） |
| birth_month      | INT NULL  | 誕生月 |
| birth_day        | INT NULL  | 誕生日 |
| delete_flag      | TINYINT   | 論理削除フラグ (1=削除, 0=有効) |
| last_message_id  | BIGINT    | 最後に投稿したプロフィール埋め込みのメッセージID |
| last_channel_id  | BIGINT    | 最後に投稿したチャンネルID |

---

### SQL 初期化例

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    age INT NULL,
    birth_year INT NULL,
    birth_month INT NULL,
    birth_day INT NULL,
    delete_flag TINYINT DEFAULT 0,
    last_message_id BIGINT NULL,
    last_channel_id BIGINT NULL
);
```

---

## 🤖 Bot 概要

### 主な機能
- `/profile` : プロフィール登録フローを開始  
  1. 地域 → 都道府県 → 性別 選択  
  2. 年齢・誕生日入力（任意、バリデーションあり）  
  3. 職業・趣味・特技・好きなタイプ・ひとこと入力（任意）  
  4. Embed 形式でプロフィールを投稿  
- `/delete_profile` : 登録済みプロフィールを削除し、DBのフラグを更新。投稿済みメッセージも削除。  

### Embed 出力例
```
✅ あなたのプロフィール
👤 名前: しょうた
🗾 都道府県: 埼玉県
🚹 性別: 男性
🎂 年齢: 20
📅 誕生日: 3月11日
💼 職業: 学生
🎯 趣味: 筋トレ
✨ 特技: プログラミング
💖 好きなタイプ: 優しい人
💬 ひとこと: よろしくお願いします！
```

---

## ⚙️ セットアップ手順

```bash
# 1) clone
git clone <repo-url>
cd profileBot

# 2) venv 作成
python3 -m venv venv
source venv/bin/activate

# 3) 依存インストール
pip install -r requirements.txt

# 4) 環境変数設定
cp .env.example .env
# 中身を編集して DISCORD_BOT_TOKEN, DB 接続情報を記入

# 5) 実行
python3 app.py
```

---

## 🔑 .env.example

```
DISCORD_BOT_TOKEN=
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=Profile
```
