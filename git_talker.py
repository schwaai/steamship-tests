import steamship
from steamship import Steamship, File, Block, Tag, DocTag, Configuration, Tag
from steamship.data.tags import TagKind, TagValueKey
from steamship.data.tags.tag_constants import RoleTag
import requests
import github as Github
import time

g = Github.Github()


class GitTalker:

    def __init__(self, workspace="schwaaweb_test0", plugin="gpt-3", repo_url=None, pre_clear=False):
        self.repo_user = repo_url.split("/")[3]
        self.repo_project = repo_url.split("/")[4]
        self.repo_url = repo_url
        self.client = Steamship(workspace=workspace)
        self.workspace = self.client.get_workspace()
        if pre_clear:
            self.clear_workspace()
        if plugin == "gpt-3":
            self.plugin = self.client.use_plugin(plugin, config={"max_words": 1024})
        elif plugin == "gpt-4":
            self.plugin = self.client.use_plugin(plugin)

        self.list_workspace_files()

        results = File.query(self.client, tag_filter_query='name "git_talker"').files

        if len(results) == 0:
            print(f"Workspace is not initialized, initializing...")
            self._init_workspace()
        else:
            self.readme_ship_file = results[0]
            self.readme_file_id = self.readme_ship_file.id
            self.readme = self.readme_ship_file.raw()

    def _get_all_repo_contents(self):
        import os
        import subprocess

        def clone_git_repo(git_url):
            tmp_dir = "tmp"

            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)

            try:
                subprocess.run(["git", "clone", "--branch", self.branch, git_url, tmp_dir], check=True)
                print(f"Cloned '{git_url}' into '{tmp_dir}' folder.")
            except subprocess.CalledProcessError as e:
                print(f"Error cloning '{git_url}' into '{tmp_dir}' folder. Error: {e}")

        clone_git_repo(self.repo_url)
        import os

        import os
        import re

        def get_file_info(root_dir, ignore_dirs=[".git", ".ci", "ldm", "web"],
                          ignore_files=[".gitignore"],
                          ignore_extensions=[".pyc", ".js"]):
            file_info_list = []
            exts = {}

            for root, _, files in os.walk(root_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    ext = os.path.splitext(full_path)[1]

                    if ext not in exts:
                        exts[ext] = []

                    if file in ignore_files:
                        continue
                    if ext in ignore_extensions:
                        continue
                    if any([ignore_dir in root for ignore_dir in ignore_dirs]):
                        continue

                    file_size = os.path.getsize(full_path)
                    data = (os.path.realpath(full_path), (full_path, ext, file_size))
                    file_info_list.append(data)
                    exts[ext].append(data)

            return file_info_list, exts

        def get_file_fdefs(files):
            file_fdefs = []

            for file_info in files:
                try:
                    with open(file_info[0], "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        function_defs = re.findall(r"(def\s+\w+\s*\(.*\))", content)

                        for func_def in function_defs:
                            file_fdefs.append((file_info[0], func_def))
                except Exception as e:
                    print(f"Error processing file '{file_info[1][0]}': {e}")

            return file_fdefs

        # Example usage:
        file_info_list, by_ext = get_file_info("tmp")
        file_fdefs = get_file_fdefs(by_ext[".py"])

        for fdef in file_fdefs:
            print(fdef)

        return file_fdefs

    def list_workspace_files(self):
        files = File.list(self.client).files
        for f in files:
            tags_str = ", ".join([f"{t.kind} {t.name}" for t in f.tags])
            print(f"{f.id} : tag[0] = {tags_str}")

    def clear_workspace(self):
        files = File.list(self.client)
        for f in files.files:
            f.delete()

    def _init_workspace(self):
        self.branch, self.readme = self._find_correct_branch(return_readme=True)
        self.readme_ship_file = self.encode_text_to_ship_file(self.readme)

        fdefs = self._get_all_repo_contents()

        def_blocks = []
        for func_def in fdefs:
            func_name = func_def[1].split("(")[0].split(" ")[1]
            func_args = func_def[1].split("(")[1].split(")")[0]
            func_return = func_def[1].split(")")[1].split(":")[0].strip()
            tags = [
                Tag(kind="code", name="function def", value={"file": func_def[0],
                                                             "name": func_name,
                                                             "args": func_args,
                                                             "return": func_return, }),
            ]
            new_block = Block(text=str(func_def), tags=tags)
            def_blocks.append(new_block)

        self.funcdefs_ship_file = File.create(self.client,
                                              blocks=def_blocks,
                                              tags=[Tag(kind="code",
                                                        name="def blocks",
                                                        value={"repo": self.repo_url})
                                                    ])
        return

    def _find_correct_branch(self, return_readme=False):
        repo_url = self.repo_url
        readme_url = f"{repo_url.rstrip('/')}/raw/main/README.md"

        # now get the response check the status code
        response = requests.get(readme_url)
        if response.status_code != 200:
            readme_url = f"{repo_url.rstrip('/')}/raw/master/README.md"
            response = requests.get(readme_url)
            if response.status_code != 200:
                return None
            else:
                self.repo_url.replace("main", "master")
                if return_readme:
                    return "master", response.text
                else:
                    return "master"
        else:
            self.repo_url.replace("master", "main")
            if return_readme:
                return "main", response.text
            else:
                return "main"

    def encode_text_to_ship_file(self, text):
        blocks = [
            Block(text=s, tags=[Tag(kind=TagKind.ROLE, name=RoleTag.SYSTEM),
                                ])
            for s in text.splitlines() if s.strip() != ""]

        chat_file = File.create(self.client, blocks=blocks, tags=[Tag(kind="custom", name="git_talker", )])
        return chat_file

    def get_response(self, text):
        self.readme_ship_file.append_block(text)
        task = self.plugin.generate(
            input_file_id=self.readme_ship_file.id,
            append_output_to_file=True,
            output_file_id=self.readme_ship_file.id,
        )
        task.wait()
        response = task.output.blocks[0].text
        return response.strip()


url = "https://github.com/comfyanonymous/ComfyUI"
gt = GitTalker(repo_url=url, pre_clear=True)
print(gt.get_response("What is this repo about?"))
gt.clear_workspace()
pass

# for fl in q.files:
#    for b in fl.blocks:
#        test = [t for t in b.tags if t.kind == 'role' and t.name == 'user']
#        if test:
#            if len(b.text) < 50:
#                print(b.text)
