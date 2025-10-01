import os
import re
import time
from datetime import datetime

import speech_recognition as sr
import pyttsx3

import ezdxf
import svgwrite
import numpy as np
import trimesh
from trimesh.creation import box as tm_box, cylinder as tm_cylinder, icosphere as tm_sphere

print("==============================================================================\n")
namaprogram = "AI Speech Recognition Polapedia Nusantara\n"
devby = "Developed by Team Polapedia Nusantara\n"
devdate = "Start Developed: 01 Oktober 2025\n"
print(namaprogram)
print(devby)
print(devdate)
print("==============================================================================\n")

recognizer = sr.Recognizer()

def speak(text: str):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS] Gagal bicara: {e}")

def listen_once(timeout=8, phrase_time_limit=10):
    with sr.Microphone() as source:
        print("🎤 Silakan berbicara...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        text = recognizer.recognize_google(audio, language="id-ID")
        text = text.lower().strip()
        print("✅ Terdeteksi ucapan:", text)
        speak("Kamu berkata " + text)
        return text
    except sr.RequestError as e:
        print(f"❌ Tidak bisa request hasil; {e}")
        return None
    except sr.UnknownValueError:
        print("❌ Maaf, tidak bisa mengenali suara")
        return None

num = r"(-?\d+\.?\d*)"

def extract_numbers(text):
    return [float(x) for x in re.findall(num, text)]

def parse_command(text: str):
    t = text.lower()

    if any(k in t for k in ["keluar", "stop", "selesai", "quit", "exit"]):
        return {'kind': 'exit'}

    if "persegi panjang" in t or "kotak" in t or "rectangle" in t:
        L = None; W = None
        mL = re.search(r"panjang\s+" + num, t)
        mW = re.search(r"lebar\s+" + num, t)
        if mL: L = float(mL.group(1))
        if mW: W = float(mW.group(1))
        if L is None or W is None:
            nums = extract_numbers(t)
            if len(nums) >= 2:
                L, W = nums[0], nums[1]
        if L and W:
            return {'kind': 'rect', 'L': abs(L), 'W': abs(W)}

    if "lingkaran" in t or "circle" in t:
        mR = re.search(r"(radius|r)\s+" + num, t)
        R = None
        if mR:
            R = float(mR.group(2))
        else:
            nums = extract_numbers(t)
            if len(nums) >= 1:
                R = nums[0]
        if R and R > 0:
            return {'kind': 'circle', 'R': R}

    if "garis" in t or "line" in t:
        m = re.search(r"dari\s+" + num + r"\s+" + num + r"\s+ke\s+" + num + r"\s+" + num, t)
        if m:
            x1, y1, x2, y2 = map(float, m.groups())
            return {'kind': 'line', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
        nums = extract_numbers(t)
        if len(nums) >= 4:
            return {'kind': 'line', 'x1': nums[0], 'y1': nums[1], 'x2': nums[2], 'y2': nums[3]}

    if "box" in t or "balok" in t or "kubus" in t:
        L = W = H = None
        mL = re.search(r"panjang\s+" + num, t)
        mW = re.search(r"lebar\s+" + num, t)
        mH = re.search(r"tinggi\s+" + num, t)
        if mL: L = float(mL.group(1))
        if mW: W = float(mW.group(1))
        if mH: H = float(mH.group(1))
        if any(v is None for v in [L, W, H]):
            nums = extract_numbers(t)
            if len(nums) >= 3:
                L, W, H = nums[0], nums[1], nums[2]
        if L and W and H:
            return {'kind': 'box', 'L': abs(L), 'W': abs(W), 'H': abs(H)}

    if "silinder" in t or "cylinder" in t or "tabung" in t:
        R = H = None
        mR = re.search(r"(radius|r)\s+" + num, t)
        mH = re.search(r"(tinggi|height|h)\s+" + num, t)
        if mR: R = float(mR.group(2))
        if mH: H = float(mH.group(2))
        if R is None or H is None:
            nums = extract_numbers(t)
            if len(nums) >= 2:
                R, H = nums[0], nums[1]
        if R and H:
            return {'kind': 'cylinder', 'R': abs(R), 'H': abs(H)}

    if "bola" in t or "sphere" in t:
        R = None
        mR = re.search(r"(radius|r)\s+" + num, t)
        if mR:
            R = float(mR.group(2))
        else:
            nums = extract_numbers(t)
            if len(nums) >= 1:
                R = nums[0]
        if R and R > 0:
            return {'kind': 'sphere', 'R': abs(R)}

    return {'kind': 'unknown', 'raw': t}

def ensure_outdir():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = os.path.join("output", ts)
    os.makedirs(outdir, exist_ok=True)
    return outdir

def save_rect_2d(L, W, outdir, basename="rect"):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0,0),(L,0),(L,W),(0,W),(0,0)], close=True)
    dxf_path = os.path.join(outdir, f"{basename}.dxf")
    doc.saveas(dxf_path)

    dwg = svgwrite.Drawing(os.path.join(outdir, f"{basename}.svg"), profile='tiny')
    dwg.add(dwg.rect(insert=(0,0), size=(L,W), fill='none', stroke='black'))
    dwg.save()

    mesh = tm_box(extents=[L, W, 1.0])
    obj_path = os.path.join(outdir, f"{basename}.obj")
    mesh.export(obj_path)

    return dxf_path, obj_path

def save_circle_2d(R, outdir, basename="circle"):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    msp.add_circle((0,0), R)
    dxf_path = os.path.join(outdir, f"{basename}.dxf")
    doc.saveas(dxf_path)

    dwg = svgwrite.Drawing(os.path.join(outdir, f"{basename}.svg"), profile='tiny')
    dwg.add(dwg.circle(center=(R, R), r=R, fill='none', stroke='black'))
    dwg.save()

    mesh = tm_cylinder(radius=R, height=1.0, sections=64)
    obj_path = os.path.join(outdir, f"{basename}.obj")
    mesh.export(obj_path)
    return dxf_path, obj_path

def save_line_2d(x1, y1, x2, y2, outdir, basename="line"):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    msp.add_line((x1,y1),(x2,y2))
    dxf_path = os.path.join(outdir, f"{basename}.dxf")
    doc.saveas(dxf_path)

    dwg = svgwrite.Drawing(os.path.join(outdir, f"{basename}.svg"), profile='tiny')
    dwg.add(dwg.line(start=(x1,y1), end=(x2,y2), stroke='black'))
    dwg.save()

    length = np.linalg.norm(np.array([x2-x1, y2-y1]))
    mesh = tm_box(extents=[length, 1.0, 1.0])
    obj_path = os.path.join(outdir, f"{basename}.obj")
    mesh.export(obj_path)
    return dxf_path, obj_path

def save_box_3d(L, W, H, outdir, basename="box"):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0,0),(L,0),(L,W),(0,W),(0,0)], close=True)
    dxf_path = os.path.join(outdir, f"{basename}.dxf")
    doc.saveas(dxf_path)

    dwg = svgwrite.Drawing(os.path.join(outdir, f"{basename}.svg"), profile='tiny')
    dwg.add(dwg.rect(insert=(0,0), size=(L,W), fill='none', stroke='black'))
    dwg.save()

    mesh = tm_box(extents=[L, W, H])
    obj_path = os.path.join(outdir, f"{basename}.obj")
    mesh.export(obj_path)
    return dxf_path, obj_path

def save_cylinder_3d(R, H, outdir, basename="cylinder"):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    msp.add_circle((0,0), R)
    dxf_path = os.path.join(outdir, f"{basename}.dxf")
    doc.saveas(dxf_path)

    dwg = svgwrite.Drawing(os.path.join(outdir, f"{basename}.svg"), profile='tiny')
    dwg.add(dwg.circle(center=(R, R), r=R, fill='none', stroke='black'))
    dwg.save()

    mesh = tm_cylinder(radius=R, height=H, sections=64)
    obj_path = os.path.join(outdir, f"{basename}.obj")
    mesh.export(obj_path)
    return dxf_path, obj_path

def save_sphere_3d(R, outdir, basename="sphere"):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    msp.add_circle((0,0), R)
    dxf_path = os.path.join(outdir, f"{basename}.dxf")
    doc.saveas(dxf_path)

    dwg = svgwrite.Drawing(os.path.join(outdir, f"{basename}.svg"), profile='tiny')
    dwg.add(dwg.circle(center=(R, R), r=R, fill='none', stroke='black'))
    dwg.save()

    mesh = tm_sphere(subdivisions=4, radius=R)
    obj_path = os.path.join(outdir, f"{basename}.obj")
    mesh.export(obj_path)
    return dxf_path, obj_path

def process_command(cmd: dict, outdir: str):
    if cmd['kind'] == 'rect':
        L, W = cmd['L'], cmd['W']
        print(f"🧩 Membuat persegi panjang {L}x{W} mm")
        dxf, obj = save_rect_2d(L, W, outdir, basename=f"rect_{L}x{W}mm")
        speak(f"Persegi panjang {int(L)} kali {int(W)} milimeter dibuat")

    elif cmd['kind'] == 'circle':
        R = cmd['R']
        print(f"🧩 Membuat lingkaran R={R} mm")
        dxf, obj = save_circle_2d(R, outdir, basename=f"circle_R{R}mm")
        speak(f"Lingkaran radius {int(R)} milimeter dibuat")

    elif cmd['kind'] == 'line':
        x1, y1, x2, y2 = cmd['x1'], cmd['y1'], cmd['x2'], cmd['y2']
        print(f"🧩 Membuat garis ({x1},{y1}) → ({x2},{y2}) mm")
        dxf, obj = save_line_2d(x1, y1, x2, y2, outdir, basename=f"line_{x1}_{y1}_{x2}_{y2}mm")
        speak("Garis telah dibuat")

    elif cmd['kind'] == 'box':
        L, W, H = cmd['L'], cmd['W'], cmd['H']
        print(f"🧩 Membuat box 3D {L}x{W}x{H} mm")
        dxf, obj = save_box_3d(L, W, H, outdir, basename=f"box_{L}x{W}x{H}mm")
        speak(f"Box tiga dimensi {int(L)} kali {int(W)} kali {int(H)} milimeter dibuat")

    elif cmd['kind'] == 'cylinder':
        R, H = cmd['R'], cmd['H']
        print(f"🧩 Membuat silinder 3D R={R} H={H} mm")
        dxf, obj = save_cylinder_3d(R, H, outdir, basename=f"cylinder_R{R}_H{H}mm")
        speak(f"Silinder tiga dimensi radius {int(R)} tinggi {int(H)} milimeter dibuat")

    elif cmd['kind'] == 'sphere':
        R = cmd['R']
        print(f"🧩 Membuat bola 3D R={R} mm")
        dxf, obj = save_sphere_3d(R, outdir, basename=f"sphere_R{R}mm")
        speak(f"Bola tiga dimensi radius {int(R)} milimeter dibuat")

    elif cmd['kind'] == 'unknown':
        print("⚠️ Perintah tidak dikenali. Coba ucapkan contoh seperti: 'buat persegi panjang panjang 120 lebar 80'")
        speak("Perintah tidak dikenali")
    elif cmd['kind'] == 'exit':
        pass

def main():
    speak("Sistem pengenalan suara Polapedia siap")
    print("Katakan bentuk yang akan dibuat. Ucapkan 'keluar' untuk menutup program.")
    while True:
        try:
            text = listen_once()
            if not text:
                continue
            cmd = parse_command(text)
            if cmd.get('kind') == 'exit':
                speak("Sampai jumpa")
                print("👋 Keluar aplikasi.")
                break

            outdir = ensure_outdir()
            process_command(cmd, outdir)
            print(f"📁 File disimpan di folder: {outdir}\n")

        except KeyboardInterrupt:
            print("\n⛔ Dihentikan pengguna.")
            break
        except Exception as e:
            print(f"❗ Terjadi error: {e}")
            speak("Terjadi kesalahan")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
