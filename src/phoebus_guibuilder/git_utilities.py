import base64
import re

import requests


class GitYaml:
    def __init__(self, dom: str, prefix: str):
        self.pattern: str = "^(.*)-(.*)-(.*)"
        self.dom: str = dom
        self.git_ref: str = (
            f"https://api.github.com/repos/epics-containers/{dom}-services/git/refs"
        )
        self.prefix: re.Match[str] | None = re.match(self.pattern, prefix)
        assert self.prefix is not None, "Empty Prefix"

    def re_group(self, component: str) -> str | None:
        match: re.Match[str] | None = re.match(self.pattern, component)
        if match:
            return match.group(1)

    def get_json_from_url(self, url: str) -> dict | None:
        try:
            response = requests.get(url)
            print(response)
            response.raise_for_status()
            if response:
                return response.json()
        except requests.exceptions.HTTPError as err:
            print(err.response.text)
            return err.response.json()

    def get_yaml(self, url) -> str | None:
        config_json: dict | None = self.get_json_from_url(url)
        assert config_json is not None, "Could not fetch config json tree"

        ioc_yaml_url = self.fetch_matches(config_json, "iocyaml")
        if ioc_yaml_url is not None:
            data: dict | None = self.get_json_from_url(ioc_yaml_url)
            if data is not None:
                base64_content = data["content"]
                decoded_content = base64.b64decode(base64_content).decode("utf-8")

                return decoded_content

    def fetch_matches(self, tree: dict, task: str) -> str | None:
        if task == "ref":
            matching_refs = [
                item
                for item in tree
                if isinstance(item, dict) and item.get("ref") == "refs/heads/main"
            ]
            return matching_refs[0]["object"]["sha"]
        elif task == "services":
            tree = tree["tree"]
            matching_url = [
                item
                for item in tree
                if isinstance(item, dict) and item.get("path") == "services"
            ]
            return matching_url[0]["url"]

        elif task == "subfolder":
            tree = tree["tree"]
            if self.prefix:
                print(f"DEBUG1:{self.prefix.group(1).lower()}")
                matching_folders = [
                    item
                    for item in tree
                    if isinstance(item, dict)
                    and self.re_group(str(item.get("path")))
                    == self.prefix.group(1).lower()
                ]
                if matching_folders:
                    return matching_folders[0]["url"]

        elif task == "config":
            tree = tree["tree"]
            config = [
                item
                for item in tree
                if isinstance(item, dict) and item.get("path") == "config"
            ]
            print(f"DEBUG2:{config[0]['url']}")
            return config[0]["url"]
        elif task == "iocyaml":
            tree = tree["tree"]
            ioc_url = [
                item
                for item in tree
                if isinstance(item, dict) and item.get("path") == "ioc.yaml"
            ]
            print(f"DEBUG3:{ioc_url[0]['url']}")
            return ioc_url[0]["url"]

    def fetch_ioc_yaml(
        self,
    ):
        commit_hashes: dict | None = self.get_json_from_url(self.git_ref)

        assert commit_hashes is not None, "Could not pull commit hashes"
        if len(commit_hashes) < 3:
            print(f"{commit_hashes['message']}")
            return

        main_hash = self.fetch_matches(commit_hashes, "ref")
        main_url = f"https://api.github.com/repos/epics-containers/{self.dom}-services/git/trees/{main_hash}"
        main_tree: dict | None = self.get_json_from_url(main_url)
        assert main_tree is not None, "Could not obtain main json tree"

        services_url: str | None = self.fetch_matches(main_tree, "services")
        assert services_url is not None, "Could not fetch services url"

        services_json: dict | None = self.get_json_from_url(services_url)
        assert services_json is not None, "Could not fetch services json tree"
        config_url = self.fetch_matches(services_json, "subfolder")

        if config_url is not None:
            config_json: dict | None = self.get_json_from_url(config_url)
            assert config_json is not None, "Could not fetch config json tree"

            ioc_yaml_url = self.fetch_matches(config_json, "config")

            return self.get_yaml(ioc_yaml_url)
