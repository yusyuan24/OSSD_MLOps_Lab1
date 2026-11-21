# Lab 1：Your First Model Service on Kubernetes

## 1. 專案介紹

本實驗使用 Iris 鳶尾花資料集，建立機器學習模型，並透過 FastAPI 將模型包裝成 REST API，最後使用 Docker 與 Kubernetes（kind）部署模型服務。

本實驗包含以下 MLOps 流程：

1. 使用 Scikit-learn 訓練 Random Forest 分類模型。
2. 使用 MLflow 記錄模型參數、Accuracy 與訓練結果。
3. 使用 Joblib 儲存訓練完成的模型。
4. 使用 FastAPI 建立模型推論 API。
5. 使用 Docker 將模型服務容器化。
6. 使用 kind 建立 Kubernetes 叢集。
7. 使用 Kubernetes Deployment 與 Service 部署模型。
8. 使用 Metrics Server 與 HPA 測試自動擴展。
9. 使用 hey 執行 API 壓力測試。

本實驗使用 Iris 資料集，模型規模較小，使用 CPU 即可完成，不需要 GPU。

## 2. 專案架構

```text
MLOps_Lab1/
│
├── train.py
├── app.py
├── Dockerfile
├── deployment.yaml
├── requirements.txt
├── model.pkl
├── README.md
│
└── screenshots/
    ├── hey-load-test-120s-100-concurrency.png
    ├── hpa-autoscaling-monitor.png
    ├── kubernetes-pod-status-monitor.png
    ├── kubernetes-pod-resource-usage.png
    ├── terminal-overview.png
    ├── mlflow-run.png
    └── mlflow-run 2.png
```

檔案用途：

| 檔案 | 用途 |
|---|---|
| `train.py` | 訓練 Iris 分類模型及記錄 MLflow |
| `app.py` | FastAPI 模型推論服務 |
| `Dockerfile` | 建立模型服務 Docker Image |
| `deployment.yaml` | Kubernetes Deployment 與 Service |
| `requirements.txt` | Python 套件清單 |
| `model.pkl` | Joblib 儲存的訓練完成模型 |
| `mlruns/` | MLflow 實驗追蹤資料 |
| `screenshots/` | 實驗成果截圖 |

## 3. 系統環境需求

本實驗以 Ubuntu Linux 為執行環境。

需要安裝：

- Python 3
- pip
- Docker
- kind
- kubectl
- Metrics Server
- hey

## 4. 安裝 kind

kind（Kubernetes IN Docker）可以使用 Docker 容器建立本機 Kubernetes 叢集。

### 4.1 確認系統架構

```bash
uname -m
```

常見架構：

- `x86_64`：AMD64
- `aarch64`：ARM64

### 4.2 下載並安裝 kind

AMD64：

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
```

ARM64：

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-arm64
```

賦予執行權限：

```bash
chmod +x ./kind
```

移動至系統執行路徑：

```bash
sudo mv ./kind /usr/local/bin/kind
```

確認安裝成功：

```bash
kind version
```

### 4.3 建立 Kubernetes Cluster

建立名稱為 `mlops` 的叢集：

```bash
kind create cluster --name mlops
```

確認叢集資訊：

```bash
kubectl cluster-info
```

查看 Kubernetes 節點：

```bash
kubectl get nodes
```

預期會看到類似：

```text
NAME                  STATUS   ROLES           AGE   VERSION
mlops-control-plane   Ready    control-plane   ...   v1.34.0
```

## 5. 安裝 kubectl

kubectl 是 Kubernetes 的命令列管理工具，可以用來建立、查看及管理 Kubernetes 資源。

本專案的 kind 節點版本為 Kubernetes v1.34.0，因此以下使用 Kubernetes v1.34 官方 APT 套件庫。

### 5.1 安裝必要工具

```bash
sudo apt-get update

sudo apt-get install -y ca-certificates curl gpg
```

### 5.2 建立金鑰目錄

```bash
sudo mkdir -p -m 755 /etc/apt/keyrings
```

### 5.3 下載 Kubernetes 官方簽章金鑰

```bash
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | \
sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
```

設定權限：

```bash
sudo chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg
```

### 5.4 加入 Kubernetes 官方套件來源

```bash
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' | \
sudo tee /etc/apt/sources.list.d/kubernetes.list
```

### 5.5 安裝 kubectl

```bash
sudo apt-get update
sudo apt-get install -y kubectl
```

確認安裝成功：

```bash
kubectl version --client
```

預期會顯示 Client Version，例如：

```text
Client Version: v1.34.x
```

## 6. 安裝 Python 套件

建立 Python 虛擬環境並啟動後安裝套件：

```bash
pip install -r requirements.txt
```

確認 Scikit-learn 版本：

```bash
python -c "import sklearn; print(sklearn.__version__)"
```

注意：Dockerfile 中的 Scikit-learn 版本應與訓練環境一致，以避免載入 `model.pkl` 時發生版本相容性問題。

## 7. 訓練 Iris 模型與 MLflow Tracking

執行模型訓練：

```bash
python train.py
```

訓練程式會執行以下工作：

- 載入 Iris 資料集。
- 使用 train_test_split 分割訓練資料與測試資料。
- 建立 Random Forest Classifier。
- 設定 `n_estimators = 100`。
- 計算模型 Accuracy。
- 使用 MLflow 記錄參數與評估指標。
- 使用 Joblib 儲存模型為 `model.pkl`。

執行完成後，會產生：

```text
model.pkl
mlruns/
```

### 7.1 MLflow Run 說明

`mlruns/` 是 MLflow Tracking 的本機實驗紀錄資料夾，保存：

- Experiment 資訊
- Run 執行紀錄
- Parameters
- Metrics
- Model Artifacts

`model.pkl` 則是訓練完成的模型，供 FastAPI 載入使用。

兩者用途不同，不應混為一談。

### 7.2 啟動 MLflow UI

```bash
mlflow ui --host 0.0.0.0 --port 5000
```

若使用遠端 Linux Server，可在本機電腦另外開啟終端機：

```bash
ssh -L 5000:localhost:5000 USER@SERVER_IP
```

將 `USER` 和 `SERVER_IP` 替換成自己的帳號及伺服器 IP。

在本機瀏覽器開啟：

```text
http://localhost:5000
```

選擇 `iris` Experiment，即可查看模型訓練紀錄。


## 8. 建立 FastAPI 模型服務

`app.py` 使用 Joblib 載入 `model.pkl`，並透過 FastAPI 提供模型預測服務。

API 包含：

| API | HTTP Method | 功能 |
|---|---|---|
| `/healthz` | GET | 檢查服務健康狀態 |
| `/predict` | POST | 接收資料並回傳預測結果 |

### 8.1 啟動 FastAPI

```bash
uvicorn app:app --host 0.0.0.0 --port 8080
```

### 8.2 測試健康檢查

```bash
curl http://localhost:8080/healthz
```

預期結果：

```json
{"ok":true}
```

### 8.3 測試模型預測

```bash
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [[5.1, 3.5, 1.4, 0.2]]}'
```

預期回應格式：

```json
{"predictions":[0]}
```

預測結果會依照實際模型訓練結果而定。

也可以開啟 FastAPI Swagger 文件：

```text
http://localhost:8080/docs
```

## 9. 建立 Docker Image

確認以下檔案存在：

```text
Dockerfile
app.py
model.pkl
```

建立 Docker Image：

```bash
docker build -t iris-api:v1 .
```

確認 Image：

```bash
docker images
```

應該可以看到：

```text
iris-api    v1
```

注意：Docker Build 前必須先執行 `python train.py`，確保 `model.pkl` 已經產生。

Dockerfile 使用 Python 3.12 slim 作為基礎映像，安裝模型推論所需套件，並將模型與 FastAPI 程式複製至容器。

Docker 推論環境中的 Scikit-learn 版本應與模型訓練環境一致。

## 10. 將 Docker Image 載入 kind

kind 建立的 Kubernetes 節點使用獨立的容器環境，因此需要將本機 Docker Image 載入 kind。

執行：

```bash
kind load docker-image iris-api:v1 --name mlops
```

確認 kind 叢集：

```bash
kubectl get nodes
```

## 11. Kubernetes Deployment 與 Service

使用 `deployment.yaml` 建立 Kubernetes Deployment 與 Service：

```bash
kubectl apply -f deployment.yaml
```

查看 Pod：

```bash
kubectl get pods
```

持續監控 Pod：

```bash
kubectl get pods -w
```

按下 `Ctrl + C` 可以結束監控，不會停止 Pod。

查看 Deployment：

```bash
kubectl get deployment
```

查看 Service：

```bash
kubectl get svc
```

本實驗的資源設定：

| 項目 | 設定 |
|---|---|
| Deployment | iris-api |
| Replicas | 1 |
| Container Port | 8080 |
| CPU Request | 100m |
| Memory Request | 128Mi |
| CPU Limit | 500m |
| Memory Limit | 256Mi |
| Readiness Probe | `/healthz` |

## 12. 測試 Kubernetes API

使用 Port Forward 將 Kubernetes Service 轉發至本機：

```bash
kubectl port-forward svc/iris-api 8080:80
```

此終端機需要保持執行。

另外開啟一個終端機，測試模型預測：

```bash
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [[5.1, 3.5, 1.4, 0.2]]}'
```

測試健康檢查：

```bash
curl http://localhost:8080/healthz
```

如果能正常收到 JSON 回應，代表 Kubernetes 模型服務已成功運作。


## 13. 安裝 Metrics Server

HPA 需要 Metrics Server 提供 Kubernetes Pod 的 CPU 使用率資訊。

安裝 Metrics Server：

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

kind 環境可能需要額外設定，讓 Metrics Server 忽略 kubelet 憑證驗證：

```bash
kubectl patch deployment metrics-server -n kube-system \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

此設定是實驗環境的便利作法，會略過 kubelet TLS 憑證驗證，不建議用於正式環境。

等待 Metrics Server 啟動：

```bash
kubectl rollout status deployment/metrics-server -n kube-system
```

確認資源指標：

```bash
kubectl top nodes
```

```bash
kubectl top pods
```

如果能正常顯示 CPU 與 Memory 使用量，代表 Metrics Server 已提供資源指標。

## 14. 設定 HPA 自動擴展

使用 kubectl autoscale 建立 Horizontal Pod Autoscaler：

```bash
kubectl autoscale deployment iris-api \
  --cpu-percent=50 \
  --min=1 \
  --max=5
```

查看 HPA：

```bash
kubectl get hpa
```

設定如下：

| 項目 | 設定 |
|---|---|
| Deployment | iris-api |
| CPU Target | 50% |
| Minimum Replicas | 1 |
| Maximum Replicas | 5 |

HPA 會根據 Pod 的 CPU 使用率與 CPU Request，決定是否需要增加或減少 Pod 數量。

查看詳細資訊：

```bash
kubectl describe hpa iris-api
```

## 15. 使用 hey 進行壓力測試

`hey` 是 HTTP 壓力測試工具，可以用來對 FastAPI 模型服務發送大量請求。

請先確認 Port Forward 正在執行：

```bash
kubectl port-forward svc/iris-api 8080:80
```

再使用另一個終端機執行壓力測試：

```bash
hey -z 120s -c 100 -m POST \
  -T application/json \
  -d '{"instances": [[5.1, 3.5, 1.4, 0.2]]}' \
  http://localhost:8080/predict
```

參數說明：

| 參數 | 意義 |
|---|---|
| `-z 120s` | 測試時間 120 秒 |
| `-c 100` | 100 個並行請求 |
| `-m POST` | 使用 POST 方法 |
| `-T application/json` | 指定 JSON Content-Type |
| `-d` | 指定 POST 請求內容 |

測試期間，另外開啟終端機觀察 HPA：

```bash
kubectl get hpa -w
```

觀察 Pod 數量：

```bash
kubectl get pods -w
```

觀察 CPU 使用量：

```bash
kubectl top pods
```

也可以查看 HPA 詳細資訊：

```bash
kubectl describe hpa iris-api
```

## 16. 實驗成果截圖

| 截圖 | 說明 |
|---|---|
| [`hey-load-test-120s-100-concurrency.png`](screenshots/hey-load-test-120s-100-concurrency.png) | 證明已執行 120 秒、100 個並行請求的壓力測試。 |
| [`hpa-autoscaling-monitor.png`](screenshots/hpa-autoscaling-monitor.png) | 顯示觀察 HPA 自動擴縮狀態的紀錄。 |
| [`kubernetes-pod-status-monitor.png`](screenshots/kubernetes-pod-status-monitor.png) | 呈現 Pod 數量及狀態變化。 |
| [`kubernetes-pod-resource-usage.png`](screenshots/kubernetes-pod-resource-usage.png) | 呈現 Pod 的 CPU 與記憶體使用量。 |
| [`terminal-overview.png`](screenshots/terminal-overview.png) | 記錄所有終端機操作的整體畫面。 |
| [`mlflow-run.png`](screenshots/mlflow-run.png) | 顯示 MLflow 執行畫面。 |
| [`mlflow-run 2.png`](<screenshots/mlflow-run 2.png>) | 顯示另一個 MLflow 執行畫面。 |


本實驗完成從模型訓練、實驗追蹤、API 服務化、Docker 容器化，到 Kubernetes 部署與自動擴展的基本 MLOps 流程。