# User Guide - Hyperstack LLM Inference Toolkit

This user guides provides instructions on how to customize the toolkit.

## 1. Deploying additional LLMs during initialization

If you want to deploy additional LLMs during initialization, you can do so by adding the LLMs to the [deployment/conf/build.manifest.yaml](../deployment/conf/build.manifest.yaml) file.

For example, to add the `microsoft/Phi-3-medium-128k-instruct` LLM, you can adjust `inference_engine_vms` list by adding a new entry as shown below.

**Make sure to use the same `model_name` as the one you use in the vLLM Docker deployment**

```yaml
inference_engine_vms:
  [...]
  - name: 'inference-vm-3'
    environment_name: 'default-CANADA-1'
    flavor_name: 'n1-RTX-A6000x1'
    key_name: 'default-CANADA-1-key'
    image_name: 'Ubuntu Server 22.04 LTS R535 CUDA 12.2'
    assign_floating_ip: 'True'
    model_name: 'microsoft/Phi-3-medium-128k-instruct'
    run_command: |
      mkdir /home/ubuntu/data/hf
      docker run -d --gpus all \
      -v /home/ubuntu/data/hf:/root/.cache/huggingface \
      -p 8000:8000 \
      --ipc=host --restart always \
      vllm/vllm-openai:latest --model "microsoft/Phi-3-medium-128k-instruct" \
      --gpu-memory-utilization 0.9 --max-model-len 15360
    port: 8000
```

Any security rules to allow the Proxy VM to communicate with the Inference Engine VMs are automatically added during deployment.

## 2. Deploying additional LLMs after initialization

If you want to deploy additional LLMs after initialization, you can do so by using the User Interface:

1. Go to the User Interface (UI) URL:
   - **Local Deployment**: http://localhost:8501/?embed=True
   - **Cloud Deployment**: Use the public URL of the proxy-vm (e.g. `http://0.0.0.0:8501/?embed=True`)
2. Go the **Models** page.
3. Click on the **New model**.
4. Enter a name for the model and click on the **Add model** button. Make sure to use the same `model_name` as the one you use in the (vLLM Docker) deployment.
5. After a new model is added, you can create a new replica by clicking on the **Add** button below the newly added model.
6. If the LLM is already hosted, you can enter the **Endpoint URL** and click on **Create** to add the replica.
7. If you want to host a new LLM via Hyperstack, click on **Deploy a new replica on Hyperstack** and fill in the required fields:
   1. **Name**: Name of the VM
   2. **Environment name**: Name of the Hyperstack environment to deploy the VM in
   3. **Image name**: Name of the Hyperstack image to use for the VM
   4. **Flavor name**: Name of the Hyperstack flavor to use for the VM
   5. **Run command**: Command to run on the VM to start the LLM. See the [deployment/conf/build.manifest.yaml](../deployment/conf/build.manifest.yaml) file for `run_command` examples.

### Tips & tricks

- If you want to use a local Ollama endpoint (for local deployments only), you can use the following instructions:
  1.  Follow steps 1 - 3 above.
  2.  Add a new model with:
      - `Model name` = `llama3:8b` (or any other ollama model running on your local machine, check out: `ollama ps` for your local models)
  3.  Add a new replica with
      - `Endpoint URL` = `http://host.docker.internal:11434/v1/chat/completions`
  - ⚠️ **Note**: The metrics will not be recorded for Ollama models as Ollama's `/chat/completions` endpoint does not respond with any metrics data.
