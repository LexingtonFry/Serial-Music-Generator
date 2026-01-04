import random
import datetime
import music21
import tkinter as tk
from tkinter import messagebox, scrolledtext
import sys
import threading

# ==========================================
# 1. 核心配置与逻辑
# ==========================================
INSTRUMENT_CONFIG = {
    "Flute": {"range": (60, 93), "clef": music21.clef.TrebleClef()},
    "Oboe": {"range": (58, 88), "clef": music21.clef.TrebleClef()},
    "Clarinet": {"range": (50, 89), "clef": music21.clef.TrebleClef()},
    "Bassoon": {"range": (36, 72), "clef": music21.clef.BassClef()},
    "Horn": {"range": (53, 79), "clef": music21.clef.TrebleClef()},
    "Trumpet": {"range": (55, 84), "clef": music21.clef.TrebleClef()},
    "Trombone": {"range": (40, 72), "clef": music21.clef.BassClef()},
    "Tuba": {"range": (28, 55), "clef": music21.clef.BassClef()},
    "Violin": {"range": (55, 100), "clef": music21.clef.TrebleClef()},
    "Viola": {"range": (48, 84), "clef": music21.clef.AltoClef()},
    "Violoncello": {"range": (36, 72), "clef": music21.clef.BassClef()},
    "Contrabass": {"range": (40, 67), "clef": music21.clef.BassClef()}
}

INSTRUMENT_GROUPS = {
    "Woodwinds": ["Flute", "Oboe", "Clarinet", "Bassoon"],
    "Brass": ["Horn", "Trumpet", "Trombone", "Tuba"],
    "Strings": ["Violin", "Viola", "Violoncello", "Contrabass"]
}


class TwelveToneComposer:
    def __init__(self, p0_notes):
        # 1. 输入识别字典 (全部大写，以匹配用户的 .upper() 输入)
        self.note_to_num = {
            "C": 0, "C#": 1, "DB": 1,
            "D": 2, "D#": 3, "EB": 3,
            "E": 4, "F": 5, "F#": 6, "GB": 6,
            "G": 7, "G#": 8, "AB": 8,
            "A": 9, "A#": 10, "BB": 10,
            "B": 11
        }

        # 2. 输出字典 (使用 music21 喜欢的标准格式: Bb, Eb 等)
        self.num_to_note = {
            0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
            6: "F#", 7: "G", 8: "G#", 9: "A", 10: "Bb", 11: "B"
        }

        try:
            # 这里输入的 n 已经是大写 (如 'BB')，现在字典能识别了
            self.p0_nums = [self.note_to_num[n] for n in p0_notes]
        except KeyError as e:
            # 这里的 e 就是那个报错的音符
            raise ValueError(f"无法识别的音符: {e}")

        if len(set(self.p0_nums)) != 12:
            raise ValueError("输入的序列必须包含12个不重复的半音！")

        self.matrix_data = self._calculate_matrix()

    def _calculate_matrix(self):
        matrix = {}
        p0 = self.p0_nums
        start_note = p0[0]
        i0 = [(start_note + (start_note - x)) % 12 for x in p0]
        grid = []
        for i in range(12):
            target_start = i0[i]
            semitone_shift = target_start - p0[0]
            row_sequence = [(n + semitone_shift) % 12 for n in p0]
            grid.append(row_sequence)
            matrix[f"P{i}"] = row_sequence
            matrix[f"R{i}"] = row_sequence[::-1]
            inv_row = [(start_note + (start_note - x) + i) % 12 for x in p0]
            matrix[f"I{i}"] = inv_row
            matrix[f"RI{i}"] = inv_row[::-1]
        self.full_grid = grid
        return matrix

    def get_generator(self, seq_key):
        if seq_key not in self.matrix_data: seq_key = "P0"
        sequence = self.matrix_data[seq_key]
        idx = 0
        while True:
            yield sequence[idx % 12]
            idx += 1

    def save_matrix_file(self):
        filename = f"Matrix_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== 12-Tone Matrix ===\n")
            f.write("      " + "  ".join([f"I{i:<2}" for i in range(12)]) + "\n")
            f.write("     " + "----" * 12 + "\n")
            for i, row in enumerate(self.full_grid):
                row_notes = [self.num_to_note[n].ljust(3) for n in row]
                f.write(f"P{i:<2} | " + " ".join(row_notes) + f" | R{i}\n")
        return filename


class Orchestrator:
    def __init__(self, total_measures, log_func):
        self.structure = []
        self.log_func = log_func
        self.generate_structure(total_measures)

    def generate_structure(self, total_measures):
        current_measure = 0
        self.log_func("\n=== 乐曲结构规划 ===")
        while current_measure < total_measures:
            length = random.randint(4, 8)
            if current_measure + length > total_measures:
                length = total_measures - current_measure

            roll = random.random()
            mode = ""
            active = []

            if roll < 0.50:
                mode = "Tutti (全奏)"
                active = "ALL"
            elif roll < 0.80:
                g_name = random.choice(list(INSTRUMENT_GROUPS.keys()))
                mode = f"Section ({g_name})"
                active = INSTRUMENT_GROUPS[g_name]
            else:
                mode = "Chamber (室内乐)"
                all_insts = list(INSTRUMENT_CONFIG.keys())
                active = random.sample(all_insts, random.randint(3, 5))

            self.structure.append({
                "start": current_measure,
                "end": current_measure + length,
                "active": active
            })
            self.log_func(f"小节 {current_measure + 1:02d}-{current_measure + length:02d}: {mode}")
            current_measure += length

    def is_active(self, inst_name, measure_idx):
        for section in self.structure:
            if section["start"] <= measure_idx < section["end"]:
                if section["active"] == "ALL": return True
                return inst_name in section["active"]
        return False


def get_smart_pitch(note_name_str, inst_name):
    pc = music21.note.Note(note_name_str).pitch.pitchClass
    min_midi, max_midi = INSTRUMENT_CONFIG[inst_name]["range"]
    valid_midis = []
    for m in range(min_midi, max_midi + 1):
        if m % 12 == pc:
            valid_midis.append(m)
    if not valid_midis:
        return music21.pitch.Pitch((min_midi + max_midi) // 2)
    if len(valid_midis) > 2:
        choice = random.choice(valid_midis[1:-1])
    else:
        choice = random.choice(valid_midis)
    return music21.pitch.Pitch(choice)


def get_rhythm_pool():
    return [(2.0, "half"), (1.0, "quarter"), (1.0, "quarter"), (0.5, "eighth"), (0.5, "eighth"), (0.25, "sixteenth")]


# ==========================================
# 2. GUI 应用程序封装
# ==========================================

class SerialComposerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 序列主义作曲生成器 (Serialism Generator)")
        self.root.geometry("600x500")

        # 输入区域
        lbl_frame = tk.LabelFrame(root, text="设置序列 (P0)", padx=10, pady=10)
        lbl_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(lbl_frame, text="输入12个音符 (用空格分隔):").pack(anchor="w")
        self.entry_p0 = tk.Entry(lbl_frame, width=50)
        # 默认值 (注意：即使这里写 Bb，程序也会自动处理)
        self.entry_p0.insert(0, "C E D F# A G# B Bb G Eb F C#")
        self.entry_p0.pack(fill="x", pady=5)

        tk.Label(lbl_frame,
                 text="支持音名: C, C#, Db, D, D#, Eb... (不区分大小写)",
                 font=("Arial", 8),
                 fg="gray").pack(anchor="w")

        # 按钮
        self.btn_generate = tk.Button(root, text="生成交响乐 (Generate)", command=self.start_generation, bg="#4CAF50",
                                      fg="white", font=("Arial", 12, "bold"))
        self.btn_generate.pack(pady=10)

        # 日志输出区域
        self.log_area = scrolledtext.ScrolledText(root, width=70, height=20)
        self.log_area.pack(padx=10, pady=5)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_generation(self):
        # 使用线程防止界面卡死
        threading.Thread(target=self.run_logic).start()

    def run_logic(self):
        self.btn_generate.config(state="disabled", text="生成中...")
        self.log_area.delete(1.0, tk.END)

        try:
            # 1. 获取输入
            raw_input = self.entry_p0.get().strip().upper()
            # 处理逗号或空格
            raw_input = raw_input.replace(",", " ")
            p0_list = raw_input.split()

            if len(p0_list) != 12:
                raise ValueError(f"检测到 {len(p0_list)} 个音符。必须精确输入 12 个音符！")

            # 2. 初始化
            self.log("正在计算十二音矩阵...")
            composer = TwelveToneComposer(p0_list)
            matrix_file = composer.save_matrix_file()
            self.log(f"矩阵文件已保存: {matrix_file}")

            # 3. 编排
            self.log("正在进行配器规划与音域计算...")
            total_measures = 50
            orchestrator = Orchestrator(total_measures, self.log)

            score = music21.stream.Score()
            score.metadata = music21.metadata.Metadata(title="Serial Custom Gen", composer="Python User")
            dynamics_pool = ["p", "mp", "mf", "f", "ff"]

            for inst_name in INSTRUMENT_CONFIG.keys():
                part = music21.stream.Part()
                part.id = inst_name
                try:
                    inst_obj = getattr(music21.instrument, inst_name)()
                except:
                    inst_obj = music21.instrument.Instrument(inst_name)
                part.insert(0, inst_obj)

                row_type = random.choice(["P", "R", "I", "RI"])
                row_idx = random.randint(0, 11)
                gen = composer.get_generator(f"{row_type}{row_idx}")

                for m_idx in range(total_measures):
                    measure = music21.stream.Measure()
                    measure.number = m_idx + 1

                    if m_idx == 0:
                        measure.append(music21.meter.TimeSignature('4/4'))
                        measure.append(INSTRUMENT_CONFIG[inst_name]["clef"])

                    is_playing = orchestrator.is_active(inst_name, m_idx)
                    current_beat = 0.0
                    target_duration = 4.0

                    if not is_playing:
                        rest = music21.note.Rest()
                        rest.quarterLength = 4.0
                        measure.append(rest)
                    else:
                        while current_beat < target_duration:
                            dur_val, r_name = random.choice(get_rhythm_pool())
                            if current_beat + dur_val > target_duration + 0.01:
                                dur_val = target_duration - current_beat
                            if dur_val <= 0.05: break

                            if random.random() < 0.1:
                                n = music21.note.Rest()
                            else:
                                pitch_val = next(gen)
                                note_char = composer.num_to_note[pitch_val]
                                final_pitch = get_smart_pitch(note_char, inst_name)
                                n = music21.note.Note(final_pitch)
                                n.expressions.append(music21.dynamics.Dynamic(random.choice(dynamics_pool)))

                            n.quarterLength = dur_val
                            measure.append(n)
                            current_beat += dur_val
                    part.append(measure)
                score.append(part)

            # 4. 导出
            filename = f"Symphony_{datetime.datetime.now().strftime('%H%M%S')}.xml"
            score.write('musicxml', fp=filename)
            self.log(f"\n成功! MusicXML 已生成: {filename}")
            messagebox.showinfo("成功", f"生成完毕！\n文件: {filename}")

        except Exception as e:
            self.log(f"\n错误: {str(e)}")
            messagebox.showerror("运行错误", str(e))
        finally:
            self.btn_generate.config(state="normal", text="生成交响乐 (Generate)")


if __name__ == "__main__":
    root = tk.Tk()
    app = SerialComposerApp(root)
    root.mainloop()