from flask import Flask
import os
import subprocess
import requests
from IPython.display import display
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, GlobalAveragePooling1D, Dense
from tensorflow.keras.utils import to_categorical

app = Flask(__name__)

TOKEN_GITHUB = os.getenv("GITHUB_TOKEN", "")

@app.route('/')
def home():
    return "ETL PROCESS HISTOTALK MODEL 1/TFJS"

@app.route('/etl-run-model1', methods=['POST'])
def etlRun():
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
        
        
    # --- PERUBAHAN ---
    # --- pull Dataset dari Database ---
    url1 = "https://capstone-five-dusky.vercel.app/chatbot/tags/nama/Soekarno"
    url2 = "https://capstone-five-dusky.vercel.app/chatbot/tags/nama/hatta"
    # {'code': 200, 'status': 'success', 'message': '', 'data': [{'tag': 'nationalism', 'nama': 'Soekarno', 'input': [], 'responses': []
    try:
        response1 = requests.get(url1)
        response2 = requests.get(url2)
        response1.raise_for_status()  # Akan raise error jika status bukan 200
        response2.raise_for_status()

        data1 = response1.json() # Jika response-nya adalah JSON
        data2 = response2.json()
        print(data1)
        print(data2)

    except requests.exceptions.RequestException as e:
        print("Terjadi kesalahan:", e)
    
    # tampikan data nama NPC
    print(data1["data"][0]["nama"])
    print(data2["data"][0]["nama"])
    
    # getting all the data list
    # soekarno
    tags1 = []
    inputs1 = []
    responses1 = {}
    for intent in data1['data']:
        responses1[intent['tag']] = intent['responses']
        for lines in intent['input']:
            inputs1.append(lines.lower())
            tags1.append(intent['tag'])
    display(len(list(set(tags1))))
    print("tags1: ", tags1)
    print("inputs1: ", inputs1)
    print("responses1: ", responses1)

    # hatta
    tags2 = []
    inputs2 = []
    responses2 = {}
    for intent in data1['data']:
        responses2[intent['tag']] = intent['responses']
        for lines in intent['input']:
            inputs2.append(lines.lower())
            tags2.append(intent['tag'])
    display(len(list(set(tags2))))
    print("tags2: ", tags2)
    print("inputs2: ", inputs2)
    print("responses2: ", responses2)

    # 1. export into dataframe
    df1 = pd.DataFrame({"inputs":inputs1, "tags":tags1})
    display(df1.head())
    df2 = pd.DataFrame({"inputs":inputs2, "tags":tags2})
    display(df2.head())
    
    # 2. Encode label ke angka
    label_encoder1 = LabelEncoder()
    df1['label'] = label_encoder1.fit_transform(df1['tags'])
    num_classes1 = len(label_encoder1.classes_)

    label_encoder2 = LabelEncoder()
    df2['label'] = label_encoder2.fit_transform(df2['tags'])
    num_classes2 = len(label_encoder2.classes_)

    # 3. Split data
    X_train1, X_test1, y_train1, y_test1 = train_test_split(df1['inputs'], df1['label'], test_size=0.2, random_state=42, stratify=df1['label'])
    X_train2, X_test2, y_train2, y_test2 = train_test_split(df2['inputs'], df2['label'], test_size=0.2, random_state=42, stratify=df2['label'])

    # 4. Tokenisasi
    tokenizer1 = Tokenizer(oov_token="<OOV>")
    tokenizer1.fit_on_texts(X_train1)
    word_index1 = tokenizer1.word_index

    tokenizer2 = Tokenizer(oov_token="<OOV>")
    tokenizer2.fit_on_texts(X_train2)
    word_index2 = tokenizer2.word_index

    # 5. Konversi teks ke urutan angka
    train_sequences1 = tokenizer1.texts_to_sequences(X_train1)
    test_sequences1 = tokenizer1.texts_to_sequences(X_test1)

    train_sequences2 = tokenizer2.texts_to_sequences(X_train2)
    test_sequences2 = tokenizer2.texts_to_sequences(X_test2)

    # 6. Padding
    # max_length = max([len(x) for x in train_sequences]) # otomatis
    max_length = 10 # statis mengikuti standar 10 classes (karena isue tfjs predict)
    X_train_padded1 = pad_sequences(train_sequences1, maxlen=max_length, padding='post')
    X_test_padded1 = pad_sequences(test_sequences1, maxlen=max_length, padding='post')

    X_train_padded2 = pad_sequences(train_sequences2, maxlen=max_length, padding='post')
    X_test_padded2 = pad_sequences(test_sequences2, maxlen=max_length, padding='post')

    # 7. One-hot encode label
    y_train_cat1 = to_categorical(y_train1, num_classes=num_classes1)
    y_test_cat1 = to_categorical(y_test1, num_classes=num_classes1)

    y_train_cat2 = to_categorical(y_train2, num_classes=num_classes2)
    y_test_cat2 = to_categorical(y_test2, num_classes=num_classes2)

    # 8. Buat model
    model1 = Sequential([
        Embedding(input_dim=len(word_index1) + 1, output_dim=16, input_length=max_length),
        GlobalAveragePooling1D(),
        Dense(16, activation='relu'),
        Dense(num_classes1, activation='softmax')
    ])
    model1.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    model2 = Sequential([
        Embedding(input_dim=len(word_index2) + 1, output_dim=16, input_length=max_length),
        GlobalAveragePooling1D(),
        Dense(16, activation='relu'),
        Dense(num_classes2, activation='softmax')
    ])
    model2.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    # 9. Latih model
    history1 = model1.fit(X_train_padded1, y_train_cat1, epochs=50, validation_data=(X_test_padded1, y_test_cat1), verbose=2)
    history2 = model2.fit(X_train_padded2, y_train_cat2, epochs=50, validation_data=(X_test_padded2, y_test_cat2), verbose=2)

    # 10. Evaluasi
    loss1, accuracy1 = model1.evaluate(X_test_padded1, y_test_cat1)
    print(f"Test Accuracy (1): {accuracy1:.2f}")

    loss2, accuracy2 = model2.evaluate(X_test_padded2, y_test_cat2)
    print(f"Test Accuracy (2): {accuracy2:.2f}")
    # dir yang akan di update
    path = "tfjs_saved_model"

    # Hapus folder jika ada
    if os.path.exists(path):
        # shutil.rmtree(path) # matikan untuk sementara
        print(f"✅ Folder '{path}' berhasil dihapus.")
    else:
        print(f"⚠️ Folder '{path}' tidak ditemukan.")
    
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