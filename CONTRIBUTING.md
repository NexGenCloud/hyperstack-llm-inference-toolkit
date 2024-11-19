# Contributing to Hyperstack LLM Inference Toolkit

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## We Develop with Github

We use github to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html), So All Code Changes Happen Through Pull Requests

Pull requests are the best way to propose changes to the codebase (we use [Github Flow](https://guides.github.com/introduction/flow/index.html)). We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed code, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Report bugs using Github's [issues](https://github.com/NexGenCloud/hyperstack-llm-inference-toolkit/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](); it's that easy!

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can, includes sample code that _anyone_ can run to reproduce.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Developing the Hyperstack LLM Inference Toolkit

Before you start, make sure you have the following tools installed:

- [Python 3.11](https://www.python.org/downloads/)
- Python dependencies
  ```bash
  python3 -m pip install -r requirements.txt
  ```

### Running the Hyperstack LLM Inference Toolkit locally

To run the toolkit locally, follow the steps described in the [Readme/#deployment](./README.md#deployment).

### Testing the Hyperstack LLM Inference Toolkit

#### Unit tests

To run the unit tests of Toolkit, run the following command:

```bash
# Run the toolkit locally
make dev-up

# Run the unit tests
make dev-test
```

#### Integration tests

To run the integration tests, make sure to deploy the MISTRAL model. See instructions in the [docs/makefile-docs.md](./docs/makefile-docs.md#integration-tests-pytest)

```bash
# Run the toolkit locally
make dev-up

# Run the unit tests
make dev-integration-test
```
