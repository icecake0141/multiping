<!--
Copyright 2025 icecake0141
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

This file was created or modified with the assistance of an AI (Large Language Model).
Review required for correctness, security, and licensing.
-->

# ParaPing — 日本語ドキュメント

（英語版 README の日本語訳です。内容に差異がないように保守してください。）

## 機能
- 複数ホストへ並列に ICMP ping を実行（capability ベースの補助バイナリ使用）
- 成功/遅延/失敗を示すタイムラインやスパークラインのライブ表示
- Knight Rider スタイルのアクティビティインジケータ表示
- ホスト統計、RTT ジッタ/標準偏差、集計カウント、TTL 表示を含むサマリーパネル
- ボックス化されたパネルレイアウト（結果、サマリー、ステータス行）
- サマリーホストは現在のソート順に一致
- 失敗数、連続失敗、レイテンシ、ホスト名でソート/フィルタ
- 表示名モードの切替: IP / 逆引き / エイリアス
- 任意で ASN 表示（Team Cymru）を自動リトライ付きで取得
- 成功/遅延/失敗の色分け（任意）
- 一時停止モード（表示のみ停止 / ping も停止）
- タイムスタンプ付きスナップショット出力
- フルスクリーン ASCII RTT グラフ（軸ラベル、スケール、秒前ラベル）
- タイムゾーン設定可能（表示用・スナップショット名用）
- 入力ファイル対応（1 行ごとに `IP,alias`、`#` コメント対応）

（中略: インストール、ヘルパーの説明など省略せずに英語 README に合わせてください）

### インタラクティブ操作
- `n`: 表示名モードを切替（ip/rdns/alias）
- `v`: 表示切替（timeline/sparkline）
- `g`: ホスト選択を開き、フルスクリーン RTT グラフへ
- `o`: ソート切替（failures/streak/latency/host）
- `f`: フィルタ切替（failures/latency/all）
- `a`: ASN 表示切替（表示領域が狭い場合は自動で非表示）
- `m`: サマリ情報切替（rates/avg RTT/TTL/streak）
- `c`: 色付き表示の切替
- `b`: 失敗時のターミナルベル切替
- `F`: サマリのフルスクリーン切替
- `w`: サマリーパネルの表示/非表示切替
- `W`: サマリーパネル位置を切替（left/right/top/bottom）
- `p`: 一時停止/再開（表示のみ または ping + 表示）
- `s`: スナップショットを `paraping_snapshot_YYYYMMDD_HHMMSS.txt` に保存
- `←` / `→`: 1 ページずつ時間を遡る/進める（履歴は記録され続け、ライブに戻るまで表示は固定）
- `↑` / `↓`: ホスト選択モードでないときはホスト一覧をスクロールします。ホスト選択モードでは選択移動に `n`（次）と `p`（前）を使用してください。選択が表示領域を越えた場合、一覧がスクロールして選択を表示に保ちます。
- `H`: ヘルプ表示（任意のキーで閉じる）
- `ESC`: フルスクリーングラフを終了
- `q`: 終了

（以降、英語版 README と同様の説明が続きます）
