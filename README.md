# ETL
Proses CI/CD untuk model 1 (tfjs) agar dapat selalu diupdate dengan cepat. Server ETL di panggil menggunakan url endpoint. Di dalam server cloud, model yang di-*build* otomatis di-*export* ke repo [histotalk-model1-tfjs](https://github.com/DBS-Coding/histotalk-model1-tfjs). Model tfjs kemudian diakses menggunakan url github pages.

Rekor terbaru proses ETL untuk tiap NPC: 
- Soekarno `22 detik`
- Hatta `31 detik`

## Development
Proyek dibuat di [Google Colab](https://colab.research.google.com/drive/1dAvs4mJpgz3F8vLOvTaMNHkEqQPqNm9D?usp=sharing) untuk pemanggilan datset dari database, pembuatan tensorflow model text classification, sampai export saved_model dan export ke tfjs menggunakan tfjs_converter.

Skema env GCollab yang berhasil untuk build saved_model dan export ke tfjs_saved_model
```bash
python 3.11.13

# Core
numpy~=2.0.2
pandas

# ML
scikit-learn
tensorflow~=2.18.0
tensorflowjs~=4.22.0
```
---

Beberapa library penting untuk tfjs converter (sesuai di collab):
```bash
numpy~=2.0.2
tf_keras==2.18.0
tensorflow_decision_forests==1.11.0
pandas==2.2.2
```

---
Untuk Web/API Server Flask:
```
Flask
requests
python-dotenv
```

## Deployment
`Repo -> Cloud Build Google -> Cloud Run`. Using cloudbuild.gserviceaccount.com to auto re-deploy when repo change.

current library in Cloud Build (python 3.12.3):
```bash
Successfully installed Flask-3.1.1 PyYAML-6.0.2 absl-py-2.3.0 astunparse-1.6.3 blinker-1.9.0 certifi-2025.4.26 charset-normalizer-3.4.2 chex-0.1.89 click-8.2.1 etils-1.12.2 flatbuffers-25.2.10 flax-0.10.6 fsspec-2025.5.1 gast-0.6.0 google-pasta-0.2.0 grpcio-1.72.1 h5py-3.14.0 humanize-4.12.3 idna-3.10 importlib_resources-6.5.2 itsdangerous-2.2.0 jax-0.6.1 jaxlib-0.6.1 jinja2-3.1.6 joblib-1.5.1 
keras-3.10.0 libclang-18.1.1 markdown-3.8 markdown-it-py-3.0.0 markupsafe-3.0.2 mdurl-0.1.2 ml-dtypes-0.5.1 msgpack-1.1.0 namex-0.1.0 nest_asyncio-1.6.0 
numpy-2.1.3 opt-einsum-3.4.0 optax-0.2.4 optree-0.16.0 orbax-checkpoint-0.11.13 packaging-23.2 
pandas-2.3.0 protobuf-5.29.5 pygments-2.19.1 python-dateutil-2.9.0.post0 
python-dotenv-1.1.0 pytz-2025.2 requests-2.32.3 rich-14.0.0 
scikit-learn-1.7.0 scipy-1.15.3 simplejson-3.20.1 six-1.17.0 tensorboard-2.19.0 tensorboard-data-server-0.7.2 
tensorflow-2.19.0 
tensorflow-decision-forests-1.12.0 tensorflow-hub-0.16.1 tensorflow-io-gcs-filesystem-0.37.1 
tensorflowjs-4.22.0 tensorstore-0.1.75 termcolor-3.1.0 
tf-keras-2.19.0 threadpoolctl-3.6.0 toolz-1.0.0 treescope-0.1.9 typing-extensions-4.14.0 tzdata-2025.2 urllib3-2.4.0 werkzeug-3.1.3 wrapt-1.17.2 wurlitzer-3.1.1 ydf-0.12.0 zipp-3.22.0
```
---
Error Deployment Log
```
ERROR: (gcloud.run.services.update) Revision 'model1-etl-repo-00002-lr2' is not ready and cannot serve traffic. The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable within the allocated timeout. This can happen when the container port is misconfigured or if the timeout is too short. The health check timeout can be extended. Logs for this revision might contain more information.
```