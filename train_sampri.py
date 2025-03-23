import csv
import os
import subprocess
import sys
import platform

def run_command(command):
    """
    Menjalankan perintah shell dan mengembalikan status keberhasilan dan output
    """
    try:
        # Jalankan perintah dan tangkap output serta error
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Membaca output dan error
        stdout, stderr = process.communicate()
        
        # Cek status error
        if process.returncode != 0:
            return False, stderr
        
        return True, stdout
    except Exception as e:
        return False, str(e)

# Fungsi untuk mencatat log
def log_message(message, error=False):
    if error:
        print(f"[ERROR] {message}", file=sys.stderr)
    else:
        print(f"[INFO] {message}")

try:
    # Deteksi sistem operasi
    is_windows = platform.system() == "Windows"
    
    # Buka file SampriBrainTrial.csv dan bersihkan data kosong
    log_message("Membaca dan membersihkan data dari CSV...")
    cleaned_dataset = []
    
    try:
        with open('SampriBrain.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)  # Lewati header
            
            for row in reader:
                # Pastikan jumlah kolom cukup dan tidak ada data kosong
                if len(row) >= 3 and row[1].strip() and row[2].strip():
                    cleaned_dataset.append({"question": row[1], "answer": row[2]})
    except FileNotFoundError:
        raise Exception("File SampriBrainTrial.csv tidak ditemukan. Pastikan file ada di direktori yang sama.")
    except Exception as e:
        raise Exception(f"Error saat membaca file CSV: {str(e)}")
    
    if len(cleaned_dataset) == 0:
        raise Exception("Tidak ada data yang valid dalam CSV. Pastikan format data benar.")
    
    log_message(f"Berhasil memproses {len(cleaned_dataset)} pasangan pertanyaan-jawaban.")

    # Format dataset menjadi prompt Ollama
    log_message("Memformat dataset untuk training...")
    formatted_dataset = [
        f"### Question:\n{data['question']}\n\n### Answer:\n{data['answer']}\n"
        for data in cleaned_dataset
    ]

    # Gabungkan semua dataset sebagai satu teks training
    training_text = "\n\n".join(formatted_dataset)

    # Simpan dataset yang sudah diformat ke dalam file training.txt
    try:
        with open("training.txt", "w", encoding="utf-8") as f:
            f.write(training_text)
        log_message("File training.txt berhasil dibuat.")
    except Exception as e:
        raise Exception(f"Error saat menyimpan file training.txt: {str(e)}")

    # Buat konten untuk file Modelfile
    modelfile_lines = [
        "FROM llama3.2",
        "",
        "# Gunakan TEMPLATE untuk format prompt/response",
        'TEMPLATE """',
        "{{ if .System }}{{ .System }}{{ end }}",
        "",
        "{{ if .Prompt }}",
        "### Question:",
        "{{ .Prompt }}",
        "",
        "### Answer:",
        "{{ end }}",
        '"""',
        "",
        "# Gunakan SYSTEM untuk instruksi sistem",
        'SYSTEM """You are a helpful assistant trained on specific data. Answer questions based on your training."""',
        "",
        "# Parameter model",
        "PARAMETER temperature 0.7",
        "PARAMETER top_p 0.9",
        "PARAMETER num_ctx 4096",
        "PARAMETER num_predict 2048",
        "PARAMETER repeat_penalty 1.1"
    ]
    
    modelfile_content = "\n".join(modelfile_lines)

    # Simpan konfigurasi ke dalam file Modelfile
    try:
        with open("Modelfile", "w", encoding="utf-8") as f:
            f.write(modelfile_content)
        log_message("File Modelfile berhasil dibuat.")
    except Exception as e:
        raise Exception(f"Error saat menyimpan file Modelfile: {str(e)}")

    # Cek apakah Ollama sudah terinstall
    success, output = run_command("ollama --version")
    if not success:
        raise Exception("Ollama tidak ditemukan. Pastikan Ollama sudah terinstall dan tersedia di PATH.")
    
    # Jalankan perintah pembuatan model Ollama menggunakan Modelfile
    log_message("Memulai proses pembuatan model...")
    success, output = run_command("ollama create sampri-custom -f Modelfile")
    
    if not success:
        raise Exception(f"Gagal membuat model: {output}")
    
    log_message("Proses pembuatan model selesai!")
    
    # Proses fine-tuning - sesuaikan berdasarkan sistem operasi
    log_message("Memulai proses fine-tuning dengan data training...")
    
    # Metode alternatif yang lebih portabel - membaca file secara langsung dengan Python
    try:
        with open("training.txt", "r", encoding="utf-8") as training_file:
            training_content = training_file.read()
            
        # Metode 1: Gunakan temporary file untuk input ke ollama
        temp_file_path = os.path.abspath("temp_input.txt")
        with open(temp_file_path, "w", encoding="utf-8") as temp_file:
            temp_file.write(training_content)
        
        if is_windows:
            fine_tune_command = f"ollama run sampri-custom --nowordwrap < {temp_file_path}"
        else:
            fine_tune_command = f"cat {temp_file_path} | ollama run sampri-custom --nowordwrap"
            
        success, output = run_command(fine_tune_command)
        
        # Hapus temporary file
        try:
            os.remove(temp_file_path)
        except:
            pass
            
        if not success:
            # Metode 2 (fallback): Coba gunakan file langsung tanpa pipe
            log_message("Mencoba metode fine-tuning alternatif...")
            success, output = run_command(f"ollama run sampri-custom --nowordwrap < training.txt")
            
            if not success:
                # Metode 3 (fallback): Coba dengan OpenAI format
                log_message("Mencoba metode fine-tuning dengan format berbeda...")
                success, output = run_command(f"ollama run sampri-custom --prompt \"$(cat training.txt)\"")
                
                if not success:
                    raise Exception(f"Semua metode fine-tuning gagal: {output}")
    except Exception as e:
        raise Exception(f"Error saat memproses file training: {str(e)}")
    
    log_message("Fine-tuning selesai! Model baru disimpan sebagai 'sampri-custom'")
    
    # Verifikasi model berhasil dibuat
    success, output = run_command("ollama list | grep sampri-custom")
    if (not success and is_windows) or "sampri-custom" not in output:
        # Di Windows, grep tidak tersedia, jadi coba dengan findstr
        if is_windows:
            success, output = run_command("ollama list | findstr sampri-custom")
            if not success or "sampri-custom" not in output:
                log_message("Warning: Model mungkin tidak berhasil dibuat dengan benar. Coba periksa dengan 'ollama list'.", error=True)
            else:
                log_message("Model sampri-custom berhasil terdeteksi dalam daftar model.")
        else:
            log_message("Warning: Model mungkin tidak berhasil dibuat dengan benar. Coba periksa dengan 'ollama list'.", error=True)
    else:
        log_message("Model sampri-custom berhasil terdeteksi dalam daftar model.")

except Exception as e:
    log_message(f"Terjadi error: {str(e)}", error=True)
    log_message("Proses dihentikan karena error.", error=True)
    sys.exit(1)