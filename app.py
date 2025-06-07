from flask import Flask, request, jsonify
import logging
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
from dotenv import load_dotenv
import time
import subprocess
import json
import requests
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, GlobalAveragePooling1D, Dense
from tensorflow.keras.utils import to_categorical

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

load_dotenv()  # ⬅️ Ini penting agar .env dibaca
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
ETL_KEY = os.getenv("ETL_KEY")
    
# Tempat menyimpan file model
username = "Leo42night"
org = "DBS-Coding"
repo = "histotalk-model1-tfjs"
email = "karmaborutovvo@gmail.com"
branch = "main"

if not GITHUB_TOKEN:
    raise EnvironmentError("❌ GITHUB_TOKEN belum diset di .env atau secret Cloud Run")

# URL
repo_url = f"https://{username}:{GITHUB_TOKEN}@github.com/{org}/{repo}.git"
dataset_url = "https://capstone-five-dusky.vercel.app/chatbot/tags/nama"


def getRepo():
    if os.path.isdir(repo):
        app.logger.info(f"Folder repo {repo} ada, pindah ke dalam repo!")
        os.chdir(repo) #masuk ke dalam karena ada git fetch
        app.logger.info(f"\n\nREPO DIR: {os.getcwd()}\n\n")
        
        # fetching
        subprocess.run(["git", "fetch", "origin", branch], check=True)
        # sesuaikan dengan data repo agar tidak ada conflict
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
        
        os.chdir("./..")  # Kembali ke folder induk
        app.logger.info(f"\n\nPARENT DIR: {os.getcwd()}\n\n")
        
    else:
        app.logger.info("Folder repo tidak ada, CLONE REPO!!")
        # Konfigurasi Git global
        subprocess.run(["git", "config", "--global", "user.email", email], check=True)
        subprocess.run(["git", "config", "--global", "user.name", username], check=True)

        # Clone dari organization
        subprocess.run(["git", "clone", "-b", branch, repo_url], check=True)

def modelling(npc):
    try:
        response = requests.get(f"{dataset_url}/{npc}")
        response.raise_for_status()  # Akan raise error jika status bukan 200
        data = response.json() # Jika response-nya adalah JSON
        app.logger.info("data didapatkan!")
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Terjadi kesalahan: {e}")
        return
    
    app.logger.info(data["data"][0]["nama"]) # tampikan data nama NPC
    
    # getting all the data list
    # soekarno
    tags = []
    inputs = []
    responses = {}
    for intent in data['data']:
        responses[intent['tag']] = intent['responses']
        for lines in intent['input']:
            inputs.append(lines.lower())
            tags.append(intent['tag'])
    # app.logger.info(len(list(set(tags))))
    # app.logger.info(f"tags: {tags}")
    
    # 1. export into dataframe
    df = pd.DataFrame({"inputs":inputs, "tags":tags})
    # app.logger.info(df.head().to_string())
    
    # 2. Encode label ke angka
    label_encoder = LabelEncoder()
    df['label'] = label_encoder.fit_transform(df['tags'])
    num_classes = len(label_encoder.classes_)
    # app.logger.info(f"Number of classes: {num_classes}")

    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(df['inputs'], df['label'], test_size=0.2, random_state=42, stratify=df['label'])

    # 4. Tokenisasi
    tokenizer = Tokenizer(oov_token="<OOV>")
    tokenizer.fit_on_texts(X_train)
    word_index = tokenizer.word_index
    
    # 5. Konversi teks ke urutan angka
    train_sequences = tokenizer.texts_to_sequences(X_train)
    test_sequences = tokenizer.texts_to_sequences(X_test)

    # 6. Padding
    # max_length = max([len(x) for x in train_sequences]) # otomatis
    max_length = 10 # statis mengikuti standar 10 classes (karena isue tfjs predict)
    X_train_padded = pad_sequences(train_sequences, maxlen=max_length, padding='post')
    X_test_padded = pad_sequences(test_sequences, maxlen=max_length, padding='post')

    # 7. One-hot encode label
    y_train_cat = to_categorical(y_train, num_classes=num_classes)
    y_test_cat = to_categorical(y_test, num_classes=num_classes)

    # 8. Buat model
    model_inputs = Input(shape=(max_length,))  # fleksibel batch size
    x = Embedding(input_dim=len(word_index)+1, output_dim=16)(model_inputs)
    x = GlobalAveragePooling1D()(x)
    x = Dense(16, activation='relu')(x)
    outputs = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=model_inputs, outputs=outputs)
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    # 9. Latih model
    model.fit(X_train_padded, y_train_cat, epochs=50, validation_data=(X_test_padded, y_test_cat), verbose=2)

    # 10. Evaluasi
    loss, accuracy = model.evaluate(X_test_padded, y_test_cat)
    app.logger.info(f"Test Accuracy: {accuracy:.2f}")
    app.logger.info(f"Test Loss: {loss:.2f}")

    # 11. Simpan model
    model.export(f'saved_model_{npc}')
    app.logger.info(f"\n\nPARENT DIR: {os.getcwd()}\n\n")
    
    
    # -- TFJS CONVERTER --
    # Definisikan perintah
    cmd = [
        "tensorflowjs_converter",
        "--input_format=tf_saved_model",
        "--output_format=tfjs_graph_model",
        "--signature_name=serving_default",
        "--saved_model_tags=serve",
        f"saved_model_{npc}",
        f"{repo}/tfjs_saved_model/{npc}"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        app.logger.info(f"✅ STDOUT:\n{result.stdout}")
        app.logger.info(f"❌ STDERR:\n{result.stderr}")
        app.logger.info("✅ Konversi Model TFJS Soekarno berhasil")
    except subprocess.CalledProcessError as e:
        app.logger.error(f"⚠️ Konversi gagal dengan error: {e}")
    except FileNotFoundError:
        app.logger.error("⚠️ tensorflowjs_converter tidak ditemukan. Pastikan sudah terinstall dan PATH sudah benar.")

    # -- SIMPAN ATRIBUT DATA MODEL --
    # simpan word_index dan label_encoder
    with open(f"{repo}/tfjs_saved_model/{npc}/word_index.json", "w") as f:
        json.dump(word_index, f)
        
    # 1. Sort dataframe berdasarkan label
    sorted_tags = df.sort_values('label')['tags'].drop_duplicates().tolist()
    # app.logger.info(sorted_tags)
    # 2. Bangun dictionary baru dengan urutan sesuai label
    sorted_responses = {tag: responses[tag] for tag in sorted_tags}
    
    with open(f"{repo}/tfjs_saved_model/{npc}/content.json", "w") as f:
        json.dump(sorted_responses, f)

def run_cmd(cmd, log_prefix):
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        app.logger.info(f"✅ {log_prefix} STDOUT:\n{result.stdout}")
    if result.stderr:
        app.logger.warning(f"❌ {log_prefix} STDERR:\n{result.stderr}")
    
    if result.returncode != 0:
        app.logger.error(f"⚠️ Command failed with code {result.returncode}: {' '.join(cmd)}")
    
    return result

def gitPush(commit_message):
    os.chdir(f"{repo}")  # Pindah ke folder Repo
    app.logger.info(f"\n\nREPO DIR: {os.getcwd()}\n\n")
    
    run_cmd(["git", "add", "."], "Git Add")
    run_cmd(["git", "commit", "-m", commit_message], "Git Commit")
    run_cmd(["git", "push", "origin", "main"], "Git Push")
    os.chdir("./..")  # Kembali ke folder induk
    app.logger.info(f"\n\nPARENT DIR: {os.getcwd()}\n\n")

@app.route('/')
def home():
    return "ETL Process HISTOTALK model Text Classification: Take DB Dataset -> Model Build (Saved Model export to Tfjs) -> Export to Model Repo Github Server", 200

@app.route('/ready')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/etl-run-model1-soekarno', methods=['POST'])
def etlRunSoekarno():
    data = request.get_json()
    etl_key = data.get('etl_key') if data else None
    
    if not ETL_KEY or not etl_key or etl_key != ETL_KEY:
        return "Unauthorized", 401
    
    getRepo() # {'code': 200, 'status': '', 'message': '', 'data': [{'tag': 'nationalism', 'nama': 'Soekarno', 'input': [], 'responses': []

    modelling("soekarno") # run modelling
    
    # # push ke github
    timestamp = int(time.time())  # Local time in seconds
    gitPush(f"Soekarno PUSH to Repo Dir TFJS {timestamp}")
    
    return jsonify({"status": "ok", "message":"ETL Soekarno Dijalankan (DB -> Train TFJS -> Push GitHub)"}), 201


@app.route('/etl-run-model1-hatta', methods=['POST'])
def etlRunHatta():
    app.logger.info("running etl-run-model1-hatta")
    app.logger.info(f"ENV: {ETL_KEY}")
    data = request.get_json()
    etl_key = data.get('etl_key') if data else None
    app.logger.info(f"json: {etl_key}")
    
    if not ETL_KEY or not etl_key or etl_key != ETL_KEY:
        return "Unauthorized", 401
    
    getRepo() # clone repo dari github
    modelling("hatta") # run modelling
    timestamp = int(time.time())  # Local time in seconds
    gitPush(f"Hatta PUSH to Repo Dir TFJS {timestamp}")
    
    return jsonify({"status": "ok", "message":"ETL Hatta Dijalankan (DB -> Train TFJS -> Push GitHub)"}), 201


@app.route('/push-etl-testing', methods=['POST'])
def pushTest():
    app.logger.info(f"ENV: {ETL_KEY}")
    data = request.get_json()
    etl_key = data.get('etl_key') if data else None
    app.logger.info(f"json: {etl_key}")
    
    if not ETL_KEY or not etl_key or etl_key != ETL_KEY:
        return "Unauthorized", 401
    
    timestamp = int(time.time())  # Local time in secon
    with open("test_updates.txt", "a") as file:
        file.write(f"Log Test ETL PUSH: {timestamp}\n")
    
    gitPush(f"Test PUSH to Repo Dir TFJS {timestamp}")
    
    return jsonify({"status": "ok","message":"Push ETL Github Testing Dijalankan"}), 201

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {error}")
    return "Something went wrong", 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False) # hentikan fitur auto-reload dan auto-debug