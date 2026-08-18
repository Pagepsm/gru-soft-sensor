# GRUソフトセンサーの学習メモ

GRUソフトセンサーに関する取り組みをまとめたリポジトリです。

高頻度のセンサと操作入力から、低頻度かつ遅延を伴う品質値を推定するソフトセンサーという仕組みの個人実装について記録を始めました。
まだ勉強中であり、今後の目標もあるので、随時更新予定です。現在の実験の途中経過を残しています。

※GitHubに関しては初心者で、リポジトリの作成・整理には生成AIの補助を使っています。

## 今までに試したこと

- センサの値をそのまま推定に使う方法(Direct)
- センサ値から潜在表現を作り、それを介して推定する方法(Latent)
- 品質値予測ヘッドとして、MLPとGRUの比較
- 真の品質値を使った状態の再計算、再同期の試み(resync)

v14では4モデルを比べました。Latent GRUとDirect MLPが近い結果でした。この結果から、潜在表現を介した推定が一概にいいとは言えないです。

状態再同期に関しては動くまではいきましたが、今のデータでは単純な出力補正のほうが強くなりました。

ひとまず、潜在表現に関する検証を今後は引き継ぎ進めていく予定です。

数値は[実験メモ](docs/experiment_history.md)にまとめて置いています。

## ファイル

```text
notebooks/  実験用Notebook
results/    保存した実験結果
docs/       実験メモ
tests/      結果の確認
archive/    前のNotebook
```

実際のコードは `notebooks/GRU_soft_sensor_simulation_v14.ipynb` です。状態再同期に関するコードは `notebooks/GRU_state_resync_simulation_v2.ipynb` にあります。

## もし動かす場合

保存結果はPython 3.12で実行しました。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
jupyter lab
```

Notebookの初期設定は `smoke` 実行です。軽い処理のみ通すようにして、とりあえず一通り動くか検証できます。

結果CSVの確認は次で行えます。

```powershell
python -m unittest discover -s tests -v
```
