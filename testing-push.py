from flask import Flask

import subprocess
# from getpass import getpass # jika butuh input manual untuk keamana
import os

app = Flask(__name__)

TOKEN_GITHUB = os.getenv("GITHUB_TOKEN", "")

@app.route('/')
def home():
    # Cek path aktif
    print("Current directory:", os.getcwd())
    
    return "Push ETL TESTING"

@app.route('/push-etl-testing', methods=['POST'])
def push():
    # -- SETUP -- pindah ke folder induk repo
    # os.chdir("./") # sesuaikan dengan lingkungan aplikasi
    
    # ⛅ Input informasi
    username = "leo42night"  # akun GitHub kamu yang punya akses
    org = "DBS-Coding"
    repo = "histotalk-model1-tfjs"
    email = "karmaborutovvo@gmail.com"
    branch = "main"

    # URL dengan token
    repo_url = f"https://{username}:{TOKEN_GITHUB}@github.com/{org}/{repo}.git"

    if os.path.isdir(repo):
        print("Folder repo ada, pindah ke dalam repo!")
        os.chdir(repo)
        print("Current directory:", os.getcwd())
        
        # fetching
        subprocess.run(["git", "fetch", "origin", branch])
        # sesuaikan dengan data repo agar tidak ada conflict
        subprocess.run(["git", "reset", "--hard", "origin/main"])
    else:
        print("Folder repo tidak ada, CLONE REPO!!")
        # Konfigurasi Git global
        subprocess.run(["git", "config", "--global", "user.email", email], check=True)
        subprocess.run(["git", "config", "--global", "user.name", username], check=True)

        # Clone dari organization
        subprocess.run(["git", "clone", "-b", branch, repo_url])
    
        # masuk ke direktori repo
        os.chdir(repo)
        print("Current directory:", os.getcwd())
        
        
    # --- PERUBAHAN ---
    
    # dir yang akan di update
    path = "tfjs_saved_model"

    # Hapus folder jika ada
    if os.path.exists(path):
        # shutil.rmtree(path) # matikan untuk sementara
        print(f"✅ Folder '{path}' berhasil dihapus.")
    else:
        print(f"⚠️ Folder '{path}' tidak ditemukan.")
    
    # buat file testing
    # Membuat file .txt dan menulis konten
    with open("test_update.txt", "w") as file:
        file.write("Ini adalah file tes untuk memastikan perubahan berhasil.\n")
        file.write("Tanggal pembuatan: 4 Juni 2025\n")
    
    # ---- PUSH KE GITHUB ----
    def run_cmd(cmd):
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"\n👉 Perintah: {' '.join(cmd)}")
        print("✅ STDOUT:")
        print(result.stdout)
        print("❌ STDERR:")
        print(result.stderr)
        if result.returncode != 0:
            print(f"⚠️ Perintah gagal dengan kode {result.returncode}")
        return result

    # Tambah, commit, push
    run_cmd(["git", "add", "."])
    run_cmd(["git", "commit", "-m", "testing push"])
    run_cmd(["git", "push", "origin", branch])
    
    return "--> Push ETL Dijalankan <--"

if __name__ == '__main__':
    port = int(os.getenv("PORT2", 8081))
    app.run(host="0.0.0.0", port=port, debug=True)
