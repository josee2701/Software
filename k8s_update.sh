kubectl delete -f k8s/front-deploy.yaml
kubectl delete -f k8s/frontend-ingress.yaml
kubectl delete -f k8s/migrate-job.yaml
kubectl delete -f k8s/secret-env.yaml
docker build -t django-frontend .
docker system prune -f --volumes
kubectl apply -f k8s/secret-env.yaml
kubectl apply -f k8s/front-deploy.yaml
# kubectl apply -f k8s/migrate-job.yaml
