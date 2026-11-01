set -euo pipefail
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || { echo 'Нужен Linux или WSL2 x86_64'; exit 1; }
command -v curl >/dev/null
slo_bin="$HOME/.local/bin"
slo_download=$(mktemp -d)
trap 'rm -rf "$slo_download"' EXIT
mkdir -p "$slo_bin"
export PATH="$slo_bin:$PATH"
if ! command -v minikube >/dev/null; then
  curl -fLsS --retry 3 https://storage.googleapis.com/minikube/releases/v1.39.0/minikube-linux-amd64 -o "$slo_download/minikube"
  install -m 755 "$slo_download/minikube" "$slo_bin/minikube"
fi
if ! command -v kubectl >/dev/null; then
  curl -fLsS --retry 3 https://dl.k8s.io/release/v1.37.1/bin/linux/amd64/kubectl -o "$slo_download/kubectl"
  install -m 755 "$slo_download/kubectl" "$slo_bin/kubectl"
fi
if ! command -v helm >/dev/null; then
  curl -fLsS --retry 3 https://get.helm.sh/helm-v4.3.1-linux-amd64.tar.gz -o "$slo_download/helm.tar.gz"
  tar -xzf "$slo_download/helm.tar.gz" -C "$slo_download"
  install -m 755 "$slo_download/linux-amd64/helm" "$slo_bin/helm"
fi
minikube version --short
kubectl version --client
helm version --short
