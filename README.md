# GRUソフトセンサー｜遅れて届く品質値を推定する

高頻度のセンサ値と操作入力から、測定頻度が低く結果の到着も遅れる品質値を推定するため、GRUを使ったソフトセンサーを実装しました。シミュレーションでDirect（センサ値を直接利用）とLatent（潜在表現を経由）を比較しています。

## 制作したもの

- **品質値の推定**　センサ系列をMLPまたはGRUに入力し、観測が少ない品質値を推定します。
- **表現方法の比較**　DirectとLatentをそれぞれMLP・GRUと組み合わせ、同じ条件で4モデルを比較しました。
- **状態の再同期**　遅れて届いた品質値に合わせて過去の状態を修正し、現在まで計算し直す方法を試しています。

## 実験結果

v14では5つの乱数seedで比較しました。真の品質値に対する平均MAEはLatent GRUが0.2092、Direct MLPが0.2145で、結果は近接しています。seed別ではDirect MLPが3回、Latent GRUが2回優位でした。この条件だけで潜在表現の優位性は結論づけられません。

状態再同期の検証では単純な出力補正が良好でした。実験条件と数値は[実験メモ](docs/experiment_history.md)に、集計結果は[results/v14](results/v14)に保存しています。

## コードを試す

実装は[主Notebook](notebooks/GRU_soft_sensor_simulation_v14_1_10.ipynb)にあります。状態再同期の試作コードは[archive](archive/GRU_state_resync_simulation_v2.ipynb)に保存しています。

Python 3.12での実行を想定しています。PowerShellでリポジトリのフォルダを開き、次を実行してください。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
jupyter lab
```

主Notebookは短い確認用の`smoke`を既定にしています。Google ColabでDriveを使用する場合は、Notebook冒頭の`mount`を`True`に変更してください。長時間の実験は設定を`full`に変更して実行します。

保存済みCSVの集計整合とNotebookの構文は、次のコマンドで検査できます。

```powershell
python -m unittest discover -s tests -v
```

`notebooks/`が実験用コード、`archive/`が以前の試作、`results/`が保存済みの実験結果、`docs/`が検証記録です。
