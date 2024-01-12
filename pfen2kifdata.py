class InputData:
    def __init__(self, command, tumos):
        self.p1_field_pfen, self.p1_tumonum, self.p2_field_pfen, self.p2_tumonum, self.val1, self.val2, self.val3 = command.split(' ')[1:]
        self.color_dict = {'r': 1, 'g': 2, 'b': 3, 'y': 4, 'p': 5, 'o': 6}
        self.p1_field_kif, self.p2_field_kif = self.pfen2kif(self.p1_field_pfen), self.pfen2kif(self.p2_field_pfen)
        self.tumos = tumos
        self.input_data = self.encode_data(self.p1_field_kif, int(self.p1_tumonum))
        self.encoded_field = self.input_data[:432]
        self.encoded_others = self.input_data[432:]
        pass

    def encode_data(self, field_kif, tumonum):
        _field = self.encode_field(field_kif)
        _tumo = self.encode_next(self.tumos[tumonum % len(self.tumos)])
        _next1 = self.encode_next(self.tumos[tumonum + 1 % len(self.tumos)])
        _next2 = self.encode_next(self.tumos[tumonum + 2 % len(self.tumos)])
        return *_field, *_tumo, *_next1, *_next2


    def pfen2kif(self, pfen):
        cols = pfen.split('/')
        puyo_exist = []
        for c_i, col in enumerate(cols):
            for r_i, row in enumerate(col):
                puyo_exist.append((c_i, r_i, self.color_dict[row]))

        field = [0] * 72
        for ele in puyo_exist:
            point = ele[1] + ele[0] * 12
            field[point] = ele[2]
        field[35] = 7
        field = ''.join(map(str,field))
        return field

    def encode_field(self, field):
        encoded_field = [0] * 12 * 6 * 6
        for i, cell in enumerate(field):
            color = int(cell)
            if color == 7 or color == 0:  # 窒息のばってん or 空きマス
                pass
            else:
                pos = (color - 1) * 72 + i
                encoded_field[pos] = 1
        return encoded_field

    def encode_next(self, tumo):
        encoded_tumo = [0] * 2 * 5
        for i, puyo in enumerate(tumo):
            color = int(self.color_dict[puyo])
            pos = (color - 1) * 2 + i
            encoded_tumo[pos] = 1
        return encoded_tumo


command = 'position gggb/ppbgg/gpb//// 6 gggbpp/bp/gggb//// 6 0 0 0'
tumos = 'tumo gg gb pp gb pg gb br gp rp bp bp pg br gr gr pr bg pb pp pg gp pr br rr pr bg gg bp rr rr pp gg br bp bb gb rr rb pb rg gr rp br br pp pp gg rp gg rg pb bp pb pg pg bp rp gr bg pb bb bg gp bg pp rr gp rg br bp bp pp pr rp bp br pg bb rr bp gp pb gb pr rb pr pg pp rp rp rb gb br pg gp br pp pb pr pb rp rg pp gg rp rg gb bp pp pb pp gp gb pr pb bg bb bg gp rp gg rg gp gr rp pg gb pb'
tmp = InputData(command, tumos.split(' ')[1:])