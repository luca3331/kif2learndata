import os
from collections import deque
from itertools import permutations
import csv
import pandas as pd

def read_txtfile(folder_path='kif_txt'):
    extension = '.txt'
    file_list = [f for f in os.listdir(folder_path) if f.endswith(extension) and os.path.isfile(os.path.join(folder_path, f))]
    files = []
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'r') as file:
            lines = file.readlines()
            files.append((file_name, lines))
    return files

def write_csvfile(kif_elements, csv_file_name, folder_path='kifs'):

    csv_folder_path = './_output'
    csv_file_path = os.path.join(csv_folder_path, csv_file_name +'.csv')
    with open(csv_file_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # csv_writer.writerow(['field', 'tumo', 'next1', 'next2', 'hand'])
        for element in kif_elements:
                for data_row in element.p1_encoded_learn_data:
                    csv_writer.writerow(data_row)
    pass


class Kif:

    def __init__(self, file):
        """
        px_raw_learn_data: 学習データに変換する前の状態
        ↓
        px_encode_learn_data: raw_learn_dataを学習モデル用に変換したもの
            { shape: [12 * 6 * 6, XX, XX, XX, XxXx]
              info: field, tumo, next1, next2, hand }

        about: hand
        ぷよの置き方は22通り，どの置き方をしたかがラベルとなる
        ツモははじめ，↓の状態で落下してくる．下が軸，上が子

         ↓  ↓  ↓  ↓  ↓  ↓   ↑  ↑  ↑  ↑  ↑  ↑
         1  2  3  4  5  6   7  8  9  10 11 12

         ←  ←  ←  ←  ←  →  →  →  →  →
         13 14 15 16 17 18 19 20 21 22

        """
        self.name = file[0]
        self.kifs = file[1:][0]
        self.tumos = self.split_tumos_in_pairs()
        self.hands_len = int(str(self.kifs[-1]).split(',')[1])
        self.p1_fields_history, self.p2_fields_history = self.kif2history()
        self.index_dict = {'field': {1: 13, 2: 53}, 'tumo': {1: 10, 2: 50}, 'next1': {1: 11, 2: 51}, 'next2': {1: 12, 2: 52}}
        self.p1_raw_learn_data = self.history2learndata(self.p1_fields_history, 1)
        # self.p2_raw_learn_data = self.history2learndata(self.p2_fields_history, 2)
        self.p1_ex_learn_data = self.raw_data_augumer(self.p1_raw_learn_data)
        # self.p2_ex_learn_data = self.raw_data_augumer(self.p2_raw_learn_data)
        self.p1_encoded_learn_data = self.encode_data(self.p1_ex_learn_data)
        # self.p1_encoded_learn_data = self.encode_data(self.p1_raw_learn_data)
        # self.p2_encoded_learn_data = self.encode_data(self.p2_raw_learn_data)


    def encode_data(self, raw_learn_datas):
        encoded_learn_data = []
        for raw_learn_data in raw_learn_datas:
            _field = self.encode_field(raw_learn_data[0])
            _tumo = self.encode_next(raw_learn_data[1]) # ツモはネクストと同じコードで変換できる
            _next1 = self.encode_next(raw_learn_data[2])
            _next2 = self.encode_next(raw_learn_data[3])
            encoded_learn_data.append((*_field, *_tumo, *_next1, *_next2, raw_learn_data[4]))
        return encoded_learn_data

    def encode_field(self, field):
        encoded_field = [0] * 12 * 6 * 6
        for i, cell in enumerate(field):
            color = int(cell)
            if color == 7 or color == 0: #窒息のばってん or 空きマス
                pass
            else:
                pos = (color - 1) * 72 + i
                encoded_field[pos] = 1
        return encoded_field

    def encode_next(self, tumo):
        encoded_tumo = [0] * 2 * 5
        for i, puyo in enumerate(tumo):
            color = int(puyo)
            pos = (color - 1) * 2 + i
            encoded_tumo[pos] = 1
        return encoded_tumo

    def kif2history(self):
        prev_turn = 0
        p1_history, p2_history = [self.kifs[1].split(',')], [self.kifs[1].split(',')]
        for kif in self.kifs[2:]:
            kif = kif.split(',')
            cur_turn = int(kif[1])
            if cur_turn - prev_turn == 2: #ターン差分が2なら，同一フレームで1p,2p共に手が進んでいる
                p1_history.append(kif)
                p2_history.append(kif)
            else:
                if kif[13] != p1_history[-1][13]:
                    p1_history.append(kif)
                elif kif[53] != p2_history[-1][53]:
                    p2_history.append(kif)
            prev_turn = int(kif[1])
        return p1_history, p2_history

    def determine_hand(self, prev_tumo, hand):
        pivot_child = [[0, 0], [0, 0]] # handが軸子で受け取るので，divmodでxy座標系に変換
        for i, handd in enumerate(hand): #jiku → ko
            pivot_child[i][0], pivot_child[i][1] = divmod(int(handd), 12)

        if pivot_child[0][0] != pivot_child[1][0]:
            #yokooki
            if pivot_child[0][0] > pivot_child[1][0]:
                # →
                return pivot_child[0][0] + 17
            else: # ←
                return pivot_child[0][0] + 13

        else:
            #tateoki
            if pivot_child[0][1] > pivot_child[1][1]:
                # ↑
                return pivot_child[0][0] + 7
            else: # ↓
                return pivot_child[0][0] + 1


    def history2learndata(self, history, player):
        datas, tumos = [], self.tumos
        prev = history[0]
        tumo_index = 0
        try: #原因未究明のツモ足らないError回避
            for curr in history[1:]:
                is_hand, hand = self.find_field_difference(prev[self.index_dict['field'][player]], curr[self.index_dict['field'][player]], prev[self.index_dict['tumo'][player]])
                # if is_hand and len(hand) == 2:
                if is_hand:
                    hand = self.determine_hand(prev[self.index_dict['tumo'][player]], hand)
                    field, tumo, next1, next2 = prev[self.index_dict['field'][player]], tumos[tumo_index], tumos[tumo_index + 1], tumos[tumo_index + 2]
                    datas.append((field, tumo, next1, next2, hand))
                    tumo_index += 1
                prev = curr
            return datas
        except IndexError:
            return datas

    def find_field_difference(self, prev, curr, prev_tumo):
        diff_index = []
        prev_puyo_count = len([i for i in range(len(prev)) if prev[i] != '0'])
        curr_puyo_count = len([i for i in range(len(prev)) if curr[i] != '0'])
        if prev_puyo_count > curr_puyo_count: #fieldのぷよ数が減っていると連鎖中なので弾く
            return False, None
        for tumo_ in prev_tumo: #jiku → ko
            for i in range(len(prev)):
                if i in diff_index:
                    continue
                if prev[i] != curr[i] and curr[i] == tumo_:
                    diff_index.append(i)
        if len(diff_index) <= 2:
            return True, diff_index
        else:
            return False, None

    def split_tumos_in_pairs(self):
        if len(str(self.kifs[-1]).split(',')[30]) > len(str(self.kifs[-1]).split(',')[70]):
            input_string = str(self.kifs[-1]).split(',')[30]
        else:
            input_string = str(self.kifs[-1]).split(',')[70]
        pairs = [input_string[i:i + 2] for i in range(0, len(input_string), 2)]
        return pairs

    def raw_data_augumer(self, raw_learn_datas):
        ex_learn_data = []

        for raw_learn_data in raw_learn_datas:
            list_raw_learn_data = [list(t) for t in raw_learn_data[:-1]]
            for i, p in enumerate(list(permutations(['1', '2', '3', '4', '5']))):
                change_dict = {'0':'0', '1':p[0], '2':p[1], '3':p[2], '4':p[3], '5':p[4], '6':'6', '7':'7'}
                row = []
                for element in list_raw_learn_data:
                    txt = ''
                    for i in range(len(element)):
                        txt += change_dict[element[i]]
                    row.append(txt)
                row.append(raw_learn_data[-1])
                ex_learn_data.append(row)

        return ex_learn_data


def main():
    root_folder_path = 'kifs'
    folder_list = [f for f in os.listdir(root_folder_path) if not f.startswith('.')]
    for folder_name in folder_list:
        folder_path = os.path.join(root_folder_path, folder_name)
        files = read_txtfile(folder_path)

        kif_elements = []
        for file in files:
            kif_elements.append(Kif(file))
        write_csvfile(kif_elements, folder_name)
        print('{0}のcsv出力が完了しました'.format(folder_name))

    pass

if __name__ == "__main__":
    print('kifを120通りに拡張しcsv出力します．')
    main()