import os
import textwrap
from urllib.parse import urlparse


def get_default_script_execution_commands() -> list[str]:
    return [
        "/tmp/user_cloud_init.sh",
    ]


class ConfigGenerator:
    def __init__(self, packages_to_install: list[str]):
        self.packages_to_install = packages_to_install

    def get_docker_install_config(self):
        with open(
            os.path.join(os.path.dirname(__file__), "scripts/install_docker.sh")
        ) as f:
            return f.read()

    def logrotation_config(self):
        return textwrap.dedent(
            """
        sudo tee /etc/docker/daemon.json > /dev/null <<EOF
        {
            "log-driver": "json-file",
            "log-opts": {
                "max-size": "100m",
                "max-file": "100"
            }
        }
        EOF
        """
        )

    def custom_run_command(self):
        raise NotImplementedError()

    def construct(self):
        install_docker_config = textwrap.indent(
            self.get_docker_install_config(), " " * 20
        )
        custom_run_command = textwrap.indent(self.custom_run_command(), " " * 20)
        logrotation_cmd = textwrap.indent(self.logrotation_config(), " " * 20)
        return textwrap.dedent(
            f"""
            #cloud-config
            package_update: true
            package_upgrade: false
            packages: {self.packages_to_install}
            write_files:
                - path: /tmp/user_cloud_init.sh
                  owner: root:root
                  permissions: '0755'
                  content: |
                    #!/bin/bash

                    # Trap
                    error_handler(){{
                        echo "An error occurred on line $1: $BASH_COMMAND"
                        echo "Command that failed: $BASH_COMMAND" > /home/ubuntu/failure.txt
                        exit 1
                    }}

                    success_handler(){{
                        if [[ ! -f /home/ubuntu/failure.txt ]]; then
                            echo "All commands executed successfully." > /home/ubuntu/success.txt
                        fi
                    }}
                    trap 'error_handler $LINENO' ERR
                    trap success_handler EXIT

                    # Make non interactive
                    export DEBIAN_FRONTEND=noninteractive
                    {install_docker_config}
                    {logrotation_cmd}
                    sudo systemctl restart docker
                    {custom_run_command}
            runcmd: {get_default_script_execution_commands()}
        """
        )


class ProxyAPIConfigGenerator(ConfigGenerator):
    def __init__(self, git_details: dict, proxy_env: dict):
        super().__init__(["build-essential"])
        self.git_details = git_details
        self.proxy_env = proxy_env

    def generate_env(self):
        return "\n".join([f"{k}={v}" for k, v in self.proxy_env.items()])

    def custom_run_command(self):
        parsed_url = urlparse(self.git_details["url"])
        protocol, domain, rest = parsed_url.scheme, parsed_url.netloc, parsed_url.path
        clone_url = f'{protocol}://oauth2:{self.git_details["token"]}@{domain}{rest}'
        return textwrap.dedent(
            f'''
        # Clone the repo
        export REPO_DIR=/home/ubuntu/proxy-api
        git clone {clone_url} --branch {self.git_details["branch"]} $REPO_DIR

        # Make all files ubuntu owner
        sudo chown -R ubuntu:ubuntu /home/ubuntu

        # Fix some permissions
        chown -R ubuntu:ubuntu $REPO_DIR

        # Generating .env
        cd $REPO_DIR
        echo """{self.generate_env()}""" > .env

        # Finally run it now
        make prod-daemon
        '''
        )


class InferenceEngineConfigGenerator(ConfigGenerator):
    def __init__(self, run_command: str):
        super().__init__(["build-essential"])
        self.run_command: str = run_command

    def custom_run_command(self):
        return self.run_command
