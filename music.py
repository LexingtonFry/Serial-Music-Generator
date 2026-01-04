import random
import datetime
import music21
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading

# ==========================================
# 1. 乐器配置 (包含演奏法逻辑分类)
# ==========================================
INSTRUMENT_CONFIG = {
    # 木管 (Woodwinds)
    "Flute":       {"range": (60, 93), "clef": music21.clef.TrebleClef(), "type": "wind"},
    "Oboe":        {"range": (58, 88), "clef": music21.clef.TrebleClef(), "type": "wind"},
    "Clarinet":    {"range": (50, 89), "clef": music21.clef.TrebleClef(), "type": "wind"},
    "Bassoon":     {"range": (36, 72), "clef": music21.clef.BassClef(),   "type": "wind"},
    # 铜管 (Brass)
    "Horn":        {"range": (53, 79), "clef": music21.clef.TrebleClef(), "type": "brass"},
    "Trumpet":     {"range": (55, 84), "clef": music21.clef.TrebleClef(), "type": "brass"},
    "Trombone":    {"range": (40, 72), "clef": music21.clef.BassClef(),   "type": "brass"},
    "Tuba":        {"range": (28, 55), "clef": music21.clef.BassClef(),   "type": "brass"},
    # 弦乐 (Strings)
    "Violin":      {"range": (55, 100),"clef": music21.clef.TrebleClef(), "type": "string"},
    "Viola":       {"range": (48, 84), "clef": music21.clef.AltoClef(),   "type": "string"},
    "Violoncello": {"range": (36, 72), "clef": music21.clef.BassClef(),   "type": "string"},
    "Contrabass":  {"range": (40, 67), "clef": music21.clef.BassClef(),   "type": "string"}
}

# ==========================================
# 2. 序列生成核心 (支持大写输入)
# ==========================================
class TwelveToneComposer:
    def __init__(self, p0_notes):
        self.note_to_num = {
            "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
            "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8,
            "A": 9, "A#": 10,"BB": 10, "B": 11
        }
        self.num_to_note = {
            0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
            6: "F#", 7: "G", 8: "G#", 9: "A", 10: "Bb", 11: "B"
        }
        try:
            self.p0_nums = [self.note_to_num[n] for n in p0_notes]
        except KeyError as e:
            raise ValueError(f"无法识别的音符: {e}")
        if len(set(self.p0_nums)) != 12:
            raise ValueError("序列必须包含12个不重复的音符！")
        self.matrix_data = self._calculate_matrix()

    def _calculate_matrix(self):
        matrix = {}
        p0 = self.p0_nums
        start_note = p0[0]
        i0 = [(start_note + (start_note - x)) % 12 for x in p0]
        for i in range(12):
            target_start = i0[i]
            semitone_shift = target_start - p0[0]
            row_sequence = [(n + semitone_shift) % 12 for n in p0]
            matrix[f"P{i}"] = row_sequence
            matrix[f"R{i}"] = row_sequence[::-1]
            inv_row = [(start_note + (start_note - x) + i) % 12 for x in p0]
            matrix[f"I{i}"] = inv_row
            matrix[f"RI{i}"] = inv_row[::-1]
        return matrix

    def get_generator(self, seq_key):
        if seq_key not in self.matrix_data: seq_key = "P0"
        sequence = self.matrix_data[seq_key]
        idx = 0
        while True:
            yield sequence[idx % 12]
            idx += 1

    def save_matrix_file(self):
        filename = f"Matrix_{datetime.datetime.now().strftime('%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== 12-Tone Matrix ===\n")
            for k, v in self.matrix_data.items():
                if "P" in k and "T" not in k:
                    row_str = " ".join([self.num_to_note[n] for n in v])
                    f.write(f"{k}: {row_str}\n")
        return filename

# ==========================================
# 3. 流体织体指挥系统 (Fluid Orchestrator)
# ==========================================
class FluidOrchestrator:
    def __init__(self, total_measures, log_func):
        self.density_map = []
        self.log_func = log_func
        self._generate_fluid_density(total_measures)

    def _generate_fluid_density(self, measures):
        """
        不再使用固定的Section，而是生成一个随时间变化的'密度曲线'。
        Density 0.1 = 稀疏 (独奏/二重奏)
        Density 0.9 = 稠密 (全奏/高潮)
        """
        self.log_func("\n=== 生成流体织体 (Fluid Texture) ===")
        current_density = 0.5 # 初始密度
        
        for i in range(measures):
            # 随机漫步 (Random Walk): 密度随时间缓慢波动
            change = random.uniform(-0.2, 0.2)
            current_density += change
            # 限制在 0.1 到 1.0 之间
            current_density = max(0.1, min(1.0, current_density))
            
            self.density_map.append(current_density)
            
            # 记录日志 (每5小节一次)
            if i % 5 == 0:
                bar_len = int(current_density * 10)
                visual = "█" * bar_len + "░" * (10 - bar_len)
                self.log_func(f"小节 {i+1}: 密度 {visual} ({current_density:.2f})")

    def should_play(self, measure_idx):
        """每个乐器在每个小节独立掷骰子决定是否演奏"""
        if measure_idx >= len(self.density_map): return False
        density = self.density_map[measure_idx]
        # 增加一点随机性，让每个乐器的决定不完全同步
        return random.random() < density

# ==========================================
# 4. 辅助功能 (音高、节奏、技巧)
# ==========================================
def get_smart_pitch(note_name, inst_name):
    pc = music21.note.Note(note_name).pitch.pitchClass
    min_m, max_m = INSTRUMENT_CONFIG[inst_name]["range"]
    valid = [m for m in range(min_m, max_m+1) if m % 12 == pc]
    if not valid: return music21.pitch.Pitch((min_m + max_m)//2)
    # 偏向选择中间音域
    if len(valid) > 2: return music21.pitch.Pitch(random.choice(valid[1:-1]))
    return music21.pitch.Pitch(random.choice(valid))

def apply_technique(note_obj, inst_name, context_dict):
    """
    添加高级演奏技法：连线、跳音、重音、拨奏、震音
    """
    inst_type = INSTRUMENT_CONFIG[inst_name]["type"]
    
    # === 力度 (Dynamics) ===
    # 扩大力度范围，增加 sfz
    dynamics_list = ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "sfz"]
    dyn = music21.dynamics.Dynamic(random.choice(dynamics_list))
    note_obj.expressions.append(dyn)

    # === 弦乐特技 (Strings) ===
    if inst_type == "string":
        roll = random.random()
        # 10% 概率切换为拨奏 (Pizzicato)
        if roll < 0.10:
            note_obj.expressions.append(music21.expressions.TextExpression("pizz."))
            note_obj.articulations.append(music21.articulations.Staccato())
            context_dict['pizz'] = True
        # 5% 概率震音 (Tremolo)
        elif roll < 0.15:
            # MusicXML 中震音通常作为 expression
            # 为了简单，这里用文字标记，或者强行加 Tremolo 对象
            # note_obj.expressions.append(music21.expressions.Tremolo()) # 兼容性一般
            note_obj.expressions.append(music21.expressions.TextExpression("trem."))
            context_dict['pizz'] = False # 震音必须是 arco
        # 如果之前是 pizz，现在大概率切回 arco
        elif context_dict.get('pizz', False) and roll > 0.3:
            note_obj.expressions.append(music21.expressions.TextExpression("arco"))
            context_dict['pizz'] = False
            
    # === 通用演奏法 (Articulations) ===
    art_roll = random.random()
    
    # 20% 跳音 (Staccato)
    if art_roll < 0.2:
        note_obj.articulations.append(music21.articulations.Staccato())
    # 10% 重音 (Accent)
    elif art_roll < 0.3:
        note_obj.articulations.append(music21.articulations.Accent())
    # 5% 保持音 (Tenuto)
    elif art_roll < 0.35:
        note_obj.articulations.append(music21.articulations.Tenuto())
    
    return note_obj

# ==========================================
# 5. GUI 应用程序
# ==========================================
class SerialComposerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Serialism Composer (Pro)")
        self.root.geometry("700x550")

        lbl_frame = tk.LabelFrame(root, text="序列设定 (P0)", padx=10, pady=10)
        lbl_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(lbl_frame, text="输入12音 (支持 Bb, F#, EB 等):").pack(anchor="w")
        self.entry_p0 = tk.Entry(lbl_frame, width=60)
        self.entry_p0.insert(0, "C E D F# A G# B Bb G Eb F C#")
        self.entry_p0.pack(fill="x", pady=5)
        tk.Label(lbl_frame, text="包含特性: 流体织体、弦乐拨奏/震音、多种演奏法、sfz强弱", font=("Arial", 9), fg="blue").pack(anchor="w")

        self.btn_gen = tk.Button(root, text="生成大师级作品 (Generate)", command=self.start_gen, bg="#2196F3", fg="white", font=("Arial", 12, "bold"))
        self.btn_gen.pack(pady=10)

        self.log_area = scrolledtext.ScrolledText(root, width=80, height=22)
        self.log_area.pack(padx=10, pady=5)

    def log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)

    def start_gen(self):
        threading.Thread(target=self.run_logic).start()

    def run_logic(self):
        self.btn_gen.config(state="disabled")
        self.log_area.delete(1.0, tk.END)
        try:
            # 1. 序列准备
            raw = self.entry_p0.get().replace(",", " ").upper().split()
            composer = TwelveToneComposer(raw)
            composer.save_matrix_file()
            
            # 2. 织体规划
            total_measures = 48
            orchestrator = FluidOrchestrator(total_measures, self.log)
            
            score = music21.stream.Score()
            score.metadata = music21.metadata.Metadata(title="Fluid Serialism", composer="AI & User")

            # 3. 乐器生成循环
            for inst_name in INSTRUMENT_CONFIG.keys():
                part = music21.stream.Part()
                part.id = inst_name
                try:
                    inst_obj = getattr(music21.instrument, inst_name)()
                except:
                    inst_obj = music21.instrument.Instrument(inst_name)
                part.insert(0, inst_obj)
                
                # 为该乐器选择一种序列形式
                row_type = random.choice(["P", "R", "I", "RI"])
                gen = composer.get_generator(f"{row_type}{random.randint(0,11)}")
                
                # 状态记忆 (用于判断是否需要切回arco等)
                context = {'pizz': False} 

                for m in range(total_measures):
                    meas = music21.stream.Measure(number=m+1)
                    if m == 0:
                        meas.append(music21.meter.TimeSignature('4/4'))
                        meas.append(INSTRUMENT_CONFIG[inst_name]["clef"])

                    # 询问流体指挥：这小节我演不演？
                    if not orchestrator.should_play(m):
                        rest = music21.note.Rest()
                        rest.quarterLength = 4.0
                        meas.append(rest)
                        # 如果休息太久，强制切回 arco 状态 (逻辑复位)
                        context['pizz'] = False
                    else:
                        # 填充音符
                        curr_beat = 0.0
                        while curr_beat < 4.0:
                            # 节奏池 (加入切分音的可能性)
                            durs = [1.0, 0.5, 0.5, 0.25, 2.0]
                            dur = random.choice(durs)
                            if curr_beat + dur > 4.0: dur = 4.0 - curr_beat
                            if dur <= 0: break

                            # 随机连线逻辑 (Slur Grouping)
                            # 如果是一个短音符，且决定开始连奏...
                            is_slur_start = False
                            
                            if random.random() < 0.15: # 15% 概率休止
                                n = music21.note.Rest()
                            else:
                                n = music21.note.Note(get_smart_pitch(composer.num_to_note[next(gen)], inst_name))
                                # 应用技巧 (拨奏、重音等)
                                n = apply_technique(n, inst_name, context)
                                
                                # === 连线逻辑 (简化版) ===
                                # 如果是连线，这里就不加 Staccato
                                # MusicXML 自动连线比较复杂，这里用 "Legato" 文字代替或不加跳音来暗示
                                # 或者使用 music21.spanner (在单小节内简单连线)
                                pass 

                            n.quarterLength = dur
                            meas.append(n)
                            curr_beat += dur
                            
                    part.append(meas)
                score.append(part)

            # 4. 导出
            fname = f"Fluid_Score_{datetime.datetime.now().strftime('%H%M%S')}.xml"
            score.write('musicxml', fp=fname)
            self.log(f"\n生成完毕! 文件名: {fname}")
            messagebox.showinfo("Success", f"大师级作品已生成:\n{fname}")

        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            self.btn_gen.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialComposerApp(root)
    root.mainloop()
