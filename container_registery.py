from flask import Flask, request, jsonify
from kubernetes import client, config
from kubernetes.client.rest import ApiException

app = Flask(__name__)

# Function to create a secret
def create_secret(api_instance, namespace, secret_name, data):
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name=secret_name),
        data={k: v.encode() for k, v in data.items()}
    )
    try:
        api_instance.create_namespaced_secret(namespace=namespace, body=secret)
        print(f"Secret '{secret_name}' created.")
    except ApiException as e:
        print(f"Exception when creating secret: {e}")

# Function to create a service
def create_service(api_instance, namespace, service_name, app_name, service_port):
    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=service_name),
        spec=client.V1ServiceSpec(
            selector={"app": app_name},
            ports=[client.V1ServicePort(port=service_port, target_port=service_port)]
        )
    )
    try:
        api_instance.create_namespaced_service(namespace=namespace, body=service)
        print(f"Service '{service_name}' created.")
    except ApiException as e:
        print(f"Exception when creating service: {e}")

# Function to create a deployment
def create_deployment(api_instance, namespace, app_name, image_address, image_tag, replicas, envs, resources, secret_name):
    container = client.V1Container(
        name=app_name,
        image=f"{image_address}:{image_tag}",
        ports=[client.V1ContainerPort(container_port=80)],
        env=[client.V1EnvVar(name=k, value=v) for k, v in envs.items()],
        resources=client.V1ResourceRequirements(
            requests=resources,
            limits=resources
        )
    )
    if secret_name:
        container.env_from = [client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name=secret_name))]

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": app_name}),
        spec=client.V1PodSpec(containers=[container])
    )
    spec = client.V1DeploymentSpec(
        replicas=replicas,
        template=template,
        selector={'matchLabels': {'app': app_name}}
    )
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=app_name),
        spec=spec
    )
    try:
        api_instance.create_namespaced_deployment(namespace=namespace, body=deployment)
        print(f"Deployment '{app_name}' created.")
    except ApiException as e:
        print(f"Exception when creating deployment: {e}")

# Function to create an ingress
def create_ingress(api_instance, namespace, ingress_name, app_name, domain_address, service_port):
    ingress = client.ExtensionsV1beta1Ingress(
        metadata=client.V1ObjectMeta(name=ingress_name),
        spec=client.ExtensionsV1beta1IngressSpec(
            rules=[client.ExtensionsV1beta1IngressRule(
                host=domain_address,
                http=client.ExtensionsV1beta1HTTPIngressRuleValue(
                    paths=[client.ExtensionsV1beta1HTTPIngressPath(
                        path="/",
                        backend=client.ExtensionsV1beta1IngressBackend(
                            service_name=app_name,
                            service_port=service_port
                        )
                    )]
                )
            )]
        )
    )
    try:
        api_instance.create_namespaced_ingress(namespace=namespace, body=ingress)
        print(f"Ingress '{ingress_name}' created.")
    except ApiException as e:
        print(f"Exception when creating ingress: {e}")

@app.route('/create_app', methods=['POST'])
def create_app():
    data = request.json
    namespace = "default"  # Change if needed
    app_name = data["AppName"]
    replicas = data["Replicas"]
    image_address = data["ImageAddress"]
    image_tag = data["ImageTag"]
    domain_address = data["DomainAddress"]
    service_port = data["ServicePort"]
    resources = data["Resources"]
    envs = data["Envs"]
    secrets = data["Secrets"]
    external_access = data["ExternalAccess"]

    config.load_kube_config()
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    extensions_v1beta1 = client.ExtensionsV1beta1Api()

    if secrets:
        create_secret(v1, namespace, f"{app_name}-secret", secrets)
    create_service(v1, namespace, f"{app_name}-service", app_name, service_port)
    create_deployment(apps_v1, namespace, app_name, image_address, image_tag, replicas, envs, resources, f"{app_name}-secret" if secrets else None)

    if external_access:
        create_ingress(extensions_v1beta1, namespace, f"{app_name}-ingress", app_name, domain_address, service_port)

    return jsonify({"status": "Application created successfully"}), 201

@app.route('/get_deployment_status', methods=['GET'])
def get_deployment_status():
    deployment_name = request.args.get('deployment_name')
    namespace = "default"  # Change if needed

    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

    try:
        # Get deployment status
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        replicas = deployment.status.replicas
        ready_replicas = deployment.status.ready_replicas

        # Get pod details
        pods = core_v1.list_namespaced_pod(namespace=namespace, label_selector=f"app={deployment_name}")
        pod_statuses = []
        for pod in pods.items:
            pod_statuses.append({
                "Name": pod.metadata.name,
                "Phase": pod.status.phase,
                "HostIP": pod.status.host_ip,
                "PodIP": pod.status.pod_ip,
                "StartTime": pod.status.start_time
            })

        response = {
            "DeploymentName": deployment_name,
            "Replicas": replicas,
            "ReadyReplicas": ready_replicas,
            "PodStatuses": pod_statuses
        }
        return jsonify(response), 200

    except ApiException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_all_deployments_status', methods=['GET'])
def get_all_deployments_status():
    namespace = "default"  # Change if needed

    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

    try:
        # Get all deployments
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
        all_deployments_status = []

        for deployment in deployments.items:
            deployment_name = deployment.metadata.name
            replicas = deployment.status.replicas
            ready_replicas = deployment.status.ready_replicas

            # Get pod details for each deployment
            pods = core_v1.list_namespaced_pod(namespace=namespace, label_selector=f"app={deployment_name}")
            pod_statuses = []
            for pod in pods.items:
                pod_statuses.append({
                    "Name": pod.metadata.name,
                    "Phase": pod.status.phase,
                    "HostIP": pod.status.host_ip,
                    "PodIP": pod.status.pod_ip,
                    "StartTime": pod.status.start_time
                })

            all_deployments_status.append({
                "DeploymentName": deployment_name,
                "Replicas": replicas,
                "ReadyReplicas": ready_replicas,
                "PodStatuses": pod_statuses
            })

        return jsonify(all_deployments_status), 200

    except ApiException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
