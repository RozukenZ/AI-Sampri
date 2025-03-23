import csv
import os
import time
import datetime
from ollama import Client

# Inisialisasi client Ollama
client = Client(host='http://localhost:11434')

def save_to_csv(question, answer, filename="sampri_interactions.csv"):
    """
    Menyimpan interaksi user dan respon AI ke file CSV
    """
    # Cek apakah file sudah ada
    file_exists = os.path.isfile(filename)
    
    # Timestamp untuk pencatatan waktu interaksi
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Buka file CSV
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'question', 'response']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Tulis header jika file baru
        if not file_exists:
            writer.writeheader()
        
        # Tulis data interaksi
        writer.writerow({
            'timestamp': timestamp,
            'question': question,
            'response': answer
        })

def chat_with_sampri():
    """
    Fungsi utama untuk berinteraksi dengan model Sampri
    """
    print("=" * 50)
    print("Selamat datang di Sampri - Asisten Virtual Prodi Informatika UMM")
    print("Ketik 'exit' untuk keluar dari aplikasi")
    print("=" * 50)
    
    while True:
        # Menerima input dari user
        user_input = input("\nAnda: ")
        
        # Cek apakah user ingin keluar
        if user_input.lower() == 'exit':
            print("Terima kasih telah menggunakan Sampri. Sampai jumpa!")
            break
        
        try:
            # Kirim prompt ke model Ollama
            start_time = time.time()
            response = client.chat(
                model='sampri', 
                messages=[{'role': 'user', 'content': user_input}]
            )
            end_time = time.time()
            
            # Ambil respon dari model
            ai_response = response['message']['content']
            
            # Tampilkan respon
            print(f"\nSampri: {ai_response}")
            print(f"\n[Waktu respons: {end_time - start_time:.2f} detik]")
            
            # Simpan interaksi ke CSV
            save_to_csv(user_input, ai_response)
            
        except Exception as e:
            print(f"Terjadi kesalahan: {e}")
            print("Pastikan server Ollama sudah berjalan dan model 'sampri' sudah dimuat.")

def check_model_exists():
    """
    Memeriksa apakah model Sampri sudah ada
    """
    try:
        models = client.list()
        return any(model['name'] == 'sampri' for model in models['models'])
    except Exception:
        return False

def create_model():
    """
    Memuat model Sampri jika belum ada menggunakan modelfile yang sudah dibuat
    """
    if not check_model_exists():
        print("Model Sampri belum ditemukan. Memuat model dari modelfile yang sudah ada...")
        try:
            # Pastikan modelfile ada
            if not os.path.exists('sampri.modelfile'):
                print("Error: File sampri.modelfile tidak ditemukan")
                return False
            
            print("Memulai proses pembuatan model Sampri. Ini mungkin memerlukan waktu...")
            
            # Menggunakan perintah command line untuk membuat model
            import subprocess
            result = subprocess.run(['ollama', 'create', 'sampri', '-f', 'sampri.modelfile'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Model Sampri berhasil dibuat!")
            else:
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error saat membuat model: {e}")
            return False
    return True

if __name__ == "__main__":
    if create_model():
        chat_with_sampri()