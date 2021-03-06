from flask import Flask, request,render_template
import time
from enum import Enum
import numpy as np
import librosa
import pyaudio  #録音機能を使うためのライブラリ
import wave     #wavファイルを扱うためのライブラリ

app = Flask(__name__)

@app.route('/',methods=['GET'])
def home_page():
    return render_template('index.html')

@app.route('/home', methods=['GET', 'POST'])
def form():
    return render_template('wav.html')

@app.route("/uploaded", methods=["POST"])
def uploaded():
    f = request.files["datafile"]
    f.save("./user.wav")

    PATH_LIST = "wav_list.txt"

    # 自動でリサンプリングされるときのサンプリング周波数
    DEFAULT_FS = 44100

    # 特徴量の種類
    class Feature_Types(Enum):
        SPECTRUM = 1
        SPECTRUM_CENTROID = 2
        MFCC = 3

    # 使用する特徴量の種類
    feature_type = Feature_Types.SPECTRUM_CENTROID

    # 処理時間計測開始
    start = time.time()

    # (1) wavファイル読み込み
    print("#1 [Wav files read]")

    # change
    # path_list = [f.filename]

    # wavファイルのパスを読み込み、リストに格納
    with open(PATH_LIST) as f:
        path_list = [line.strip() for line in f.readlines()] # 改行削除

    # 各wavファイルの振幅データ列とサンプリング周波数を取得し、リストに格納
    x_and_fs_list = []
    # change
    # x,fs = librosa.load(f.filename, DEFAULT_FS)
    # x_and_fs_list = [(x,fs)]
    for path in path_list:
        x, fs = librosa.load(path, DEFAULT_FS)
        x_and_fs_list.append((x, fs))

    # 読み込んだwavファイルのパスを一覧表示
    print("> | {} : {}".format("Index", "Path"))
    for index in range(len(path_list)):
        print("> | {} : {}".format(index + 1, path_list[index]))

    print("")

    # (2) 特徴抽出
    print("#2 [Feature extraction]")

    # 使用する特徴量を表示
    print("> Selected feature type : {}".format(feature_type.name))

    # 使用する特徴量を抽出し、リストに格納
    feature_list = []
    for x_and_fs in x_and_fs_list:
        x = x_and_fs[0]
        fs = x_and_fs[1]
        if feature_type == Feature_Types.SPECTRUM:
            feature = np.abs(librosa.stft(x))
        elif feature_type == Feature_Types.SPECTRUM_CENTROID:
            feature = librosa.feature.spectral_centroid(x, fs)
        elif feature_type == Feature_Types.MFCC:
            feature = librosa.feature.mfcc(x, fs)
        feature_list.append(feature)

    print("")

    # (3) 類似度計算
    print("#3 [Evaluation]")

    # 比較の基準とする特徴量
    reference_index = 0
    reference_feature = feature_list[reference_index]
    print("> Reference : {} ({})".format(reference_index + 1, path_list[reference_index]))

    # 類似度を計算し、リストに格納
    eval_list = []
    for target_feature in feature_list:
        ac, wp = librosa.sequence.dtw(reference_feature, target_feature)
        eval = 1 - (ac[-1][-1] / np.array(ac).max())
        eval_list.append(eval)

    # 類似度を一覧表示
    print("> | {} , {} : {}".format("Reference", "Target", "Score"))
    maximum = 0
    for target_index in range(len(eval_list)):
        eval = eval_list[target_index]
        print("> | {} , {} : {}".format(reference_index + 1, target_index + 1, round(eval, 4)))
        if (maximum < eval) & (target_index != 0):
            maximum = eval
            max_index = target_index

    print("")

    # 処理時間計測終了
    end = time.time()
    # 処理時間表示
    print("Total elapsed time : {}[sec]".format(round(end - start, 4)))


    return "similar: " + path_list[max_index] + " percent: " + str(int(maximum*100))
    # + f.filename

# アプリケーションを動かすためのおまじない
if __name__ == "__main__":
    app.run(port = 8000, debug=False)