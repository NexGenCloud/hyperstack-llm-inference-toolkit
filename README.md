# Hyperstack LLM Inference Toolkit

![Banner](./docs/images/banner.png)

## Introduction

The Hyperstack LLM Inference Toolkit is an open-source tool that simplifies Large Language Model (LLM) management and deployment using Hyperstack. This app serves as a comprehensive toolkit for developers and researchers looking to work with LLMs, allowing them to deploy, manage, and prototype models with ease. With features for generating API keys, unified proxy APIs for streamlined model access, and model management options, this app is designed to accelerate your workflow whether you’re testing, developing, or integrating LLMs.

Here's why this toolkit could be your go-to solution:

1. Fast prototyping and deployment: Jump-start your LLM projects with quick setup and deployment capabilities, letting you focus on developing insights and solutions.
2. Intuitive interface: The toolkit features a user-friendly UI, making it easy to test models, access API integrations, and view setup instructions directly.
3. Robust monitoring and management: Track your models’ performance in real-time, manage multiple deployments, and gain insights from usage data effortlessly.

Highlighted features include:

- ⚙️ Flexible deployment: Deploy open-source LLMs seamlessly, with support for both local and cloud-based setups.
- 🔗 Proxy API integration: Access and manage your LLMs via a streamlined proxy API, with high throughput and low latency using vLLM.
- 🗂️ Comprehensive model management: Quickly deploy and visualize LLMs, connect existing API endpoints, and set rate limits.
- 🔐 API key and security management: Easily generate API keys, enforce usage limits, and secure your application with built-in password protection.
- 📈 Real-time tracking: Monitor usage with detailed insights, including visualized data, table views, and data export options.

Contributions and feedback are encouraged to keep expanding its capabilities for the LLM community!

## Getting started

Please follow the instructions to set this platform up on a machine.

### Prerequisites

Please make sure that you have the following prerequisites installed before you go any further:

1. Docker (instructions [here](https://docs.docker.com/engine/install/))
2. Docker Compose (instructions [here](https://docs.docker.com/compose/install/))
3. Make utility
   - Linux installation: `sudo apt-get install build-essential`
   - macOS installation: `brew install make`

Then, choose one of the following deployment options:

1. **Local Deployment**: Run the toolkit on your local machine.
2. **Cloud Deployment**: Deploy the toolkit on the Hyperstack cloud platform.

### Deployment

#### 1. Local Deployment

To deploy the toolkit locally, follow these steps:

1. Rename the `.env.example` file to `.env`, which contains app configuration for the local environment.
2. Change at least the following environment variables in the `.env` file:
   - `HYPERSTACK_API_KEY`: Your Hyperstack API key
   - `APP_PASSWORD`: The password for the User Interface (UI)
3. Build and start app services containers in attached mode:
   ```bash
   make dev-up
   ```

#### 2. Cloud Deployment

To deploy the toolkit on the Hyperstack platform, follow the steps below.

By default, the toolkit deploys the following resources:

1. A proxy VM that forwards requests to the inference engine VMs and hosts the User Interface (UI)
2. One inference engine VM that hosts the LLM: `NousResearch/Meta-Llama-3.1-8B-instruct`
3. One inference engine VM that hosts the LLM: `microsoft/Phi-3-medium-128k-instruct`

**Instructions**

1. Create a Hyperstack account (instructions [here](https://infrahub-doc.nexgencloud.com/docs/getting-started#before-getting-started))
2. Create an environment and keypair (instructions [here](https://infrahub-doc.nexgencloud.com/docs/getting-started/))
3. Generate an API key (instructions [here](https://infrahub-doc.nexgencloud.com/docs/api-reference/getting-started-api/authentication/#generate-your-first-api-key))
4. Rename the `deployment/build.manifest.yaml.example` file to `deployment/build.manifest.yaml` and update the following fields
5. Change at least the following variables in the `deployment/build.manifest.yaml` file:

   - `env.HYPERSTACK_API_KEY`: Your Hyperstack API key (used in the VMs)
   - `env.APP_PASSWORD`: The password for the User Interface (UI)
   - `hyperstack_api_key`: Your Hyperstack API key (used in the deployment)
   - `proxy_instance.key_name`: The name of the Hyperstack keypair to use for the proxy VM
   - `inference_engine_vms.[idx].key_name`: The name of the Hyperstack keypair to use for the inference engine VMs

6. Deploy the toolkit using the Hyperstack platform
   ```bash
   make deploy-app
   ```
7. Go to the [Hyperstack platform](https://console.hyperstack.cloud) and view the public URL of your deployment.

## Usage

You can interact with the toolkit using the User Interface. Here's how you can access the toolkit:

1. Go to the User Interface (UI) URL:
   - **Local Deployment**: http://localhost:8501
   - **Cloud Deployment**: Use the URL provided by Hyperstack
2. Use the User Interface to interact with the toolkit:
   1. **🏠 Home**: Home page describing the toolkit
   2. **📦 Models**: View all deployed LLMs, add new models, and manage replicas for each model
   3. **👩‍💻 Playground**: Interact with your deployed LLM models
   4. **🔑 API Keys**: Create and manage API keys for your users
   5. **📊 Monitoring**: View and interact with the data stored in your databases

## Architecture

For a detailed overview of the architecture, services, and API endpoints, please refer to the [Architecture documentation](./docs/architecture.md).

## Contributing

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/new-feature`)
3. Commit your Changes (`git commit -m 'Add some new-feature'`)
4. Push to the Branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See the `LICENSE` file for more information.
